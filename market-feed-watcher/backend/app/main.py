from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.schemas import ListingInput, ListingSnapshotResponse, ChangeEvent
from app.services.snapshot_service import process_listing_batch, get_recent_snapshots
from app.seed_data import MOCK_LISTINGS_BATCH_1, MOCK_LISTINGS_BATCH_2

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Market Feed Watcher",
    description="A small backend system for tracking market listing changes.",
    version="0.1.0",
)

@app.get("/")
def root():
    return {
        "service": "Market Feed Watcher",
        "status": "running",
        "message": "Backend is ready."
    }

@app.post("/ingest", response_model=list[ChangeEvent])
def ingest_listings(
    listings: list[ListingInput],
    db: Session = Depends(get_db),
):
    return process_listing_batch(db, listings)

@app.post("/demo/batch-1", response_model=list[ChangeEvent])
def ingest_demo_batch_1(db: Session = Depends(get_db)):
    listings = [ListingInput(**item) for item in MOCK_LISTINGS_BATCH_1]
    return process_listing_batch(db, listings)

@app.post("/demo/batch-2", response_model=list[ChangeEvent])
def ingest_demo_batch_2(db: Session = Depends(get_db)):
    listings = [ListingInput(**item) for item in MOCK_LISTINGS_BATCH_2]
    return process_listing_batch(db, listings)

@app.get("/snapshots", response_model=list[ListingSnapshotResponse])
def snapshots(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return get_recent_snapshots(db, limit)