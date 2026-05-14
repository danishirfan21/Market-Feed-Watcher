from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import CrawlRun
from app.services.health_service import get_source_health

def create_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    return TestingSessionLocal()

def test_source_health_unknown_when_no_runs_exist():
    db = create_test_db()

    health = get_source_health(db, "test_market")

    assert health["status"] == "unknown"
    assert health["total_runs"] == 0
    assert health["success_rate"] == 0

    db.close()

def test_source_health_healthy_when_all_runs_succeed():
    db = create_test_db()

    db.add(
        CrawlRun(
            source="test_market",
            status="success",
            listings_found=3,
            changes_detected=2,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
    )

    db.commit()

    health = get_source_health(db, "test_market")

    assert health["status"] == "healthy"
    assert health["total_runs"] == 1
    assert health["successful_runs"] == 1
    assert health["failed_runs"] == 0
    assert health["success_rate"] == 100
    assert health["total_changes_detected"] == 2

    db.close()

def test_source_health_degraded_when_failures_exist():
    db = create_test_db()

    db.add_all(
        [
            CrawlRun(
                source="test_market",
                status="success",
                listings_found=3,
                changes_detected=2,
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            ),
            CrawlRun(
                source="test_market",
                status="failed",
                listings_found=0,
                changes_detected=0,
                error_message="Timeout",
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
            ),
        ]
    )

    db.commit()

    health = get_source_health(db, "test_market")

    assert health["status"] == "degraded"
    assert health["total_runs"] == 2
    assert health["successful_runs"] == 1
    assert health["failed_runs"] == 1
    assert health["success_rate"] == 50
    assert health["last_error"] in [None, "Timeout"]

    db.close()