from datetime import datetime
from sqlalchemy.orm import Session

from app.models import CrawlRun

def start_crawl_run(db: Session, source: str):
    crawl_run = CrawlRun(
        source=source,
        status="running",
    )

    db.add(crawl_run)
    db.commit()
    db.refresh(crawl_run)

    return crawl_run

def finish_crawl_run(
    db: Session,
    crawl_run: CrawlRun,
    listings_found: int,
    changes_detected: int,
):
    crawl_run.status = "success"
    crawl_run.listings_found = listings_found
    crawl_run.changes_detected = changes_detected
    crawl_run.finished_at = datetime.utcnow()

    db.commit()
    db.refresh(crawl_run)

    return crawl_run

def fail_crawl_run(
    db: Session,
    crawl_run: CrawlRun,
    error_message: str,
):
    crawl_run.status = "failed"
    crawl_run.error_message = error_message
    crawl_run.finished_at = datetime.utcnow()

    db.commit()
    db.refresh(crawl_run)

    return crawl_run

def get_recent_crawl_runs(db: Session, limit: int = 10):
    return (
        db.query(CrawlRun)
        .order_by(CrawlRun.started_at.desc())
        .limit(limit)
        .all()
    )