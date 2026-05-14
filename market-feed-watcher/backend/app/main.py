from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

import asyncio
from contextlib import asynccontextmanager

from app.database import Base, engine, get_db, SessionLocal
from app.schemas import ListingInput, ListingSnapshotResponse, ChangeEvent, CrawlRunResponse
from app.services.snapshot_service import process_listing_batch, get_recent_snapshots
from app.services.health_service import get_source_health
from app.seed_data import MOCK_LISTINGS_BATCH_1, MOCK_LISTINGS_BATCH_2
from app.crawlers.mock_market_crawler import MockMarketCrawler
from app.crawlers.http_market_crawler import HttpMarketCrawler
from fastapi.staticfiles import StaticFiles
from app.websocket_manager import WebSocketManager
from app.services.crawl_run_service import (
    start_crawl_run,
    finish_crawl_run,
    fail_crawl_run,
    get_recent_crawl_runs,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Market Feed Watcher",
    description="A small backend system for tracking market listing changes.",
    version="0.3.0",
)

app.mount("/static", StaticFiles(directory="."), name="static")

crawler = MockMarketCrawler()
http_crawler = HttpMarketCrawler(
    source="local_http_market",
    url="http://localhost:8000/static/sample_market.html",
)

scheduler_state = {
    "enabled": False,
    "interval_seconds": 10,
    "task": None,
}

ws_manager = WebSocketManager()

async def broadcast_changes(changes: list[ChangeEvent]):
    for change in changes:
        await ws_manager.broadcast({
            "type": "market_change",
            "payload": change.model_dump(),
        })

async def execute_mock_crawl():
    db = SessionLocal()
    crawl_run = start_crawl_run(db, source="mock_html_market")

    try:
        raw_listings = await crawler.fetch_listings()
        listings = [ListingInput(**item) for item in raw_listings]

        changes = process_listing_batch(db, listings)

        finish_crawl_run(
            db=db,
            crawl_run=crawl_run,
            listings_found=len(listings),
            changes_detected=len(changes),
        )

        await broadcast_changes(changes)

    except Exception as exc:
        fail_crawl_run(
            db=db,
            crawl_run=crawl_run,
            error_message=str(exc),
        )

    finally:
        db.close()

async def scheduler_loop():
    while scheduler_state["enabled"]:
        await execute_mock_crawl()
        await asyncio.sleep(scheduler_state["interval_seconds"])



@app.get("/")
def root():
    return {
        "service": "Market Feed Watcher",
        "status": "running",
        "version": "0.3.0",
        "message": "WebSocket live feed is ready."
    }

@app.websocket("/ws/changes")
async def websocket_changes(websocket: WebSocket):
    await ws_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
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
    crawl_run = start_crawl_run(db, source="mock_html_market")

    try:
        raw_listings = await crawler.fetch_listings()
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
        raise

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
    crawl_run = start_crawl_run(db, source="local_http_market")

    try:
        raw_listings = await http_crawler.fetch_listings()
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
        raise

@app.post("/scheduler/start")
async def start_scheduler(interval_seconds: int = 10):
    if scheduler_state["enabled"]:
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
    scheduler_state["enabled"] = False

    task = scheduler_state.get("task")
    if task:
        task.cancel()
        scheduler_state["task"] = None

    return {
        "status": "stopped",
    }

@app.get("/scheduler/status")
def scheduler_status():
    return {
        "enabled": scheduler_state["enabled"],
        "interval_seconds": scheduler_state["interval_seconds"],
    }