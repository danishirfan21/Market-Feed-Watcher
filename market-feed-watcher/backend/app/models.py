from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database import Base

class ListingSnapshot(Base):
    __tablename__ = "listing_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    external_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    source = Column(String, nullable=False)

    captured_at = Column(DateTime, default=datetime.utcnow)

class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(String, nullable=False)
    status = Column(String, nullable=False)

    listings_found = Column(Integer, default=0)
    changes_detected = Column(Integer, default=0)

    error_message = Column(String, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)