import asyncio
import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.crawlers.http_market_crawler import HttpMarketCrawler
from app.crawlers.mock_market_crawler import MockMarketCrawler
from app.database import Base, SessionLocal, engine, get_db
from app.schemas import ChangeEvent, CrawlRunResponse, ListingInput, ListingSnapshotResponse
from app.seed_data import MOCK_LISTINGS_BATCH_1, MOCK_LISTINGS_BATCH_2
from app.services.crawl_run_service import (
    fail_crawl_run,
    finish_crawl_run,
    get_recent_crawl_runs,
    start_crawl_run,
)
from app.services.health_service import get_source_health
from app.services.snapshot_service import get_recent_snapshots, process_listing_batch
from app.websocket_manager import WebSocketManager

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Market Feed Watcher",
    description="A small backend system for tracking market listing changes.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

APP_URL = os.getenv("APP_URL", "http://localhost:8000").rstrip("/")

crawler = MockMarketCrawler()
http_crawler = HttpMarketCrawler(
    source="local_http_market",
    url=f"{APP_URL}/static/sample_market.html",
)

scheduler_state: dict[str, Any] = {
    "enabled": False,
    "interval_seconds": 10,
    "task": None,
}
scheduler_lock = asyncio.Lock()

ws_manager = WebSocketManager()


async def broadcast_changes(changes: list[ChangeEvent]) -> None:
    if not changes:
        return

    await ws_manager.broadcast(
        {
            "type": "market_changes",
            "payload": [change.model_dump() for change in changes],
            "count": len(changes),
        }
    )


async def run_market_crawl(
    *,
    db: Session,
    source: str,
    crawler_client: MockMarketCrawler | HttpMarketCrawler,
) -> list[ChangeEvent]:
    crawl_run = start_crawl_run(db, source=source)

    try:
        raw_listings = await crawler_client.fetch_listings()
        listings = [ListingInput(**item) for item in raw_listings]
        changes = process_listing_batch(db, listings)

        finish_crawl_run(
            db=db,
            crawl_run=crawl_run,
            listings_found=len(listings),
            changes_detected=len(changes),
        )

        await broadcast_changes(changes)
        return changes
    except Exception as exc:
        fail_crawl_run(
            db=db,
            crawl_run=crawl_run,
            error_message=str(exc),
        )
        logger.exception("Crawler run failed", extra={"source": source})
        raise HTTPException(
            status_code=502,
            detail={
                "error": "crawler_failed",
                "source": source,
                "message": str(exc),
            },
        ) from exc


async def execute_mock_crawl() -> None:
    db = SessionLocal()
    try:
        await run_market_crawl(
            db=db,
            source="mock_html_market",
            crawler_client=crawler,
        )
    except HTTPException as exc:
        logger.warning("Scheduled crawl failed: %s", exc.detail)
    finally:
        db.close()


async def scheduler_loop() -> None:
    logger.info("Scheduler started")
    try:
        while scheduler_state["enabled"]:
            await execute_mock_crawl()
            await asyncio.sleep(scheduler_state["interval_seconds"])
    except asyncio.CancelledError:
        logger.info("Scheduler cancelled")
        raise
    finally:
        scheduler_state["enabled"] = False
        scheduler_state["task"] = None
        logger.info("Scheduler stopped")


@app.get("/")
def root():
    return {
        "service": "Market Feed Watcher",
        "status": "running",
        "version": "0.3.0",
        "message": "WebSocket live feed is ready.",
    }


@app.websocket("/ws/changes")
async def websocket_changes(websocket: WebSocket):
    await ws_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        logger.exception("Unexpected WebSocket error")
        ws_manager.disconnect(websocket)


@app.post("/ingest", response_model=list[ChangeEvent])
async def ingest_listings(
    listings: list[ListingInput],
    db: Session = Depends(get_db),
):
    changes = process_listing_batch(db, listings)
    await broadcast_changes(changes)

    return changes


@app.post("/crawl/run", response_model=list[ChangeEvent])
async def run_crawler(db: Session = Depends(get_db)):
    return await run_market_crawl(
        db=db,
        source="mock_html_market",
        crawler_client=crawler,
    )


@app.get("/crawl-runs", response_model=list[CrawlRunResponse])
def crawl_runs(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    return get_recent_crawl_runs(db, limit)


@app.post("/demo/batch-1", response_model=list[ChangeEvent])
async def ingest_demo_batch_1(db: Session = Depends(get_db)):
    listings = [ListingInput(**item) for item in MOCK_LISTINGS_BATCH_1]

    changes = process_listing_batch(db, listings)
    await broadcast_changes(changes)

    return changes


@app.post("/demo/batch-2", response_model=list[ChangeEvent])
async def ingest_demo_batch_2(db: Session = Depends(get_db)):
    listings = [ListingInput(**item) for item in MOCK_LISTINGS_BATCH_2]

    changes = process_listing_batch(db, listings)
    await broadcast_changes(changes)

    return changes


@app.get("/snapshots", response_model=list[ListingSnapshotResponse])
def snapshots(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return get_recent_snapshots(db, limit)


@app.get("/health/source/{source}")
def source_health(
    source: str,
    db: Session = Depends(get_db),
):
    return get_source_health(db, source)


@app.post("/crawl/http", response_model=list[ChangeEvent])
async def run_http_crawler(db: Session = Depends(get_db)):
    return await run_market_crawl(
        db=db,
        source="local_http_market",
        crawler_client=http_crawler,
    )


@app.post("/scheduler/start")
async def start_scheduler(interval_seconds: int = 10):
    if interval_seconds < 1:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_interval",
                "message": "interval_seconds must be at least 1.",
            },
        )

    async with scheduler_lock:
        task = scheduler_state.get("task")
        if scheduler_state["enabled"] and task and not task.done():
            return {
                "status": "already_running",
                "interval_seconds": scheduler_state["interval_seconds"],
            }

        scheduler_state["enabled"] = True
        scheduler_state["interval_seconds"] = interval_seconds
        scheduler_state["task"] = asyncio.create_task(scheduler_loop())

    return {
        "status": "started",
        "interval_seconds": interval_seconds,
    }


@app.post("/scheduler/stop")
async def stop_scheduler():
    async with scheduler_lock:
        scheduler_state["enabled"] = False
        task = scheduler_state.get("task")
        scheduler_state["task"] = None

    if task and not task.done():
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    return {
        "status": "stopped",
    }


@app.get("/scheduler/status")
def scheduler_status():
    task = scheduler_state.get("task")
    return {
        "enabled": scheduler_state["enabled"],
        "running": bool(task and not task.done()),
        "interval_seconds": scheduler_state["interval_seconds"],
        "worker_pid": os.getpid(),
    }
