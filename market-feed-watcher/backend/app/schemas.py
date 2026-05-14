from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ListingInput(BaseModel):
    external_id: str
    title: str
    price: int
    status: str
    source: str

class ListingSnapshotResponse(BaseModel):
    id: int
    external_id: str
    title: str
    price: int
    status: str
    source: str
    captured_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChangeEvent(BaseModel):
    external_id: str
    title: str
    old_price: int | None = None
    new_price: int | None = None
    old_status: str | None = None
    new_status: str | None = None
    change_type: str

class CrawlRunResponse(BaseModel):
    id: int
    source: str
    status: str
    listings_found: int
    changes_detected: int
    error_message: str | None = None
    started_at: datetime
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)