from sqlalchemy.orm import Session

from app.models import ListingSnapshot
from app.schemas import ListingInput, ChangeEvent

def get_latest_snapshot(db: Session, external_id: str):
    return (
        db.query(ListingSnapshot)
        .filter(ListingSnapshot.external_id == external_id)
        .order_by(ListingSnapshot.captured_at.desc())
        .first()
    )

def create_snapshot(db: Session, listing: ListingInput):
    snapshot = ListingSnapshot(
        external_id=listing.external_id,
        title=listing.title,
        price=listing.price,
        status=listing.status,
        source=listing.source,
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot

def process_listing_batch(db: Session, listings: list[ListingInput]):
    changes: list[ChangeEvent] = []

    for listing in listings:
        latest = get_latest_snapshot(db, listing.external_id)

        if latest is None:
            changes.append(
                ChangeEvent(
                    external_id=listing.external_id,
                    title=listing.title,
                    new_price=listing.price,
                    new_status=listing.status,
                    change_type="new_listing",
                )
            )
        else:
            price_changed = latest.price != listing.price
            status_changed = latest.status != listing.status

            if price_changed:
                changes.append(
                    ChangeEvent(
                        external_id=listing.external_id,
                        title=listing.title,
                        old_price=latest.price,
                        new_price=listing.price,
                        change_type="price_changed",
                    )
                )

            if status_changed:
                changes.append(
                    ChangeEvent(
                        external_id=listing.external_id,
                        title=listing.title,
                        old_status=latest.status,
                        new_status=listing.status,
                        change_type="status_changed",
                    )
                )

        create_snapshot(db, listing)

    return changes

def get_recent_snapshots(db: Session, limit: int = 20):
    return (
        db.query(ListingSnapshot)
        .order_by(ListingSnapshot.captured_at.desc())
        .limit(limit)
        .all()
    )