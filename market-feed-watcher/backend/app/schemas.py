from pydantic import BaseModel
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

    class Config:
        from_attributes = True

class ChangeEvent(BaseModel):
    external_id: str
    title: str
    old_price: int | None = None
    new_price: int | None = None
    old_status: str | None = None
    new_status: str | None = None
    change_type: str