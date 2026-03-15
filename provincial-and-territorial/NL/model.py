from typing import Optional

from pydantic import BaseModel


class Party(BaseModel):
    """Fields present on Elections NL Officially Registered Parties page."""

    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    full_name: str
    leader: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
