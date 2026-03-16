from typing import Optional

from pydantic import BaseModel


class Party(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    party_name: str
    leader: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None

