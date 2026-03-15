from typing import Optional

from pydantic import BaseModel


class Party(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    party_name: str
    ballot_name: str
    leader: str
    contact_name: str
    address: str
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
