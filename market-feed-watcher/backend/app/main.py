from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db, SessionLocal
from app.schemas import ListingInput, ListingSnapshotResponse, ChangeEvent
from app.services.snapshot_service import process_listing_batch, get_recent_snapshots
from app.seed_data import MOCK_LISTINGS_BATCH_1, MOCK_LISTINGS_BATCH_2
from app.crawlers.mock_market_crawler import MockMarketCrawler
from app.websocket_manager import WebSocketManager

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Market Feed Watcher",
    description="A small backend system for tracking market listing changes.",
    version="0.3.0",
)

crawler = MockMarketCrawler()
ws_manager = WebSocketManager()

async def broadcast_changes(changes: list[ChangeEvent]):
    for change in changes:
        await ws_manager.broadcast({
            "type": "market_change",
            "payload": change.model_dump(),
        })

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
    raw_listings = await crawler.fetch_listings()
    listings = [ListingInput(**item) for item in raw_listings]

    changes = process_listing_batch(db, listings)
    await broadcast_changes(changes)

    return changes

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