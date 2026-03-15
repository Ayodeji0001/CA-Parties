import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


class Party(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    full_name: str
    short_name: str
    leader: str
    headquarters: str
    registered_date: Optional[date] = None
    deregistered_date: Optional[date] = None
    chief_agent: str
    auditor: str
    logo_url: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    privacy_policy: Optional[str] = None
    anchor_id: str

    @field_validator("registered_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        match = re.search(r"(\d{4}-\d{2}-\d{2})", str(v or ""))
        return date.fromisoformat(match.group(1)) if match else None
