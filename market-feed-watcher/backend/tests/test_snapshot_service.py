from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.schemas import ListingInput
from app.services.snapshot_service import process_listing_batch

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

def test_detects_new_listing():
    db = create_test_db()

    listings = [
        ListingInput(
            external_id="car-001",
            title="2019 Honda Civic",
            price=5200000,
            status="available",
            source="test_market",
        )
    ]

    changes = process_listing_batch(db, listings)

    assert len(changes) == 1
    assert changes[0].change_type == "new_listing"
    assert changes[0].external_id == "car-001"

    db.close()

def test_detects_price_change():
    db = create_test_db()

    first_batch = [
        ListingInput(
            external_id="car-001",
            title="2019 Honda Civic",
            price=5200000,
            status="available",
            source="test_market",
        )
    ]

    second_batch = [
        ListingInput(
            external_id="car-001",
            title="2019 Honda Civic",
            price=5050000,
            status="available",
            source="test_market",
        )
    ]

    process_listing_batch(db, first_batch)
    changes = process_listing_batch(db, second_batch)

    assert len(changes) == 1
    assert changes[0].change_type == "price_changed"
    assert changes[0].old_price == 5200000
    assert changes[0].new_price == 5050000

    db.close()

def test_detects_status_change():
    db = create_test_db()

    first_batch = [
        ListingInput(
            external_id="car-002",
            title="2021 Toyota Corolla",
            price=6100000,
            status="available",
            source="test_market",
        )
    ]

    second_batch = [
        ListingInput(
            external_id="car-002",
            title="2021 Toyota Corolla",
            price=6100000,
            status="sold",
            source="test_market",
        )
    ]

    process_listing_batch(db, first_batch)
    changes = process_listing_batch(db, second_batch)

    assert len(changes) == 1
    assert changes[0].change_type == "status_changed"
    assert changes[0].old_status == "available"
    assert changes[0].new_status == "sold"

    db.close()