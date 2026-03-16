from typing import Optional

from pydantic import BaseModel


class Party(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    party_name: str
    party_id: Optional[str] = None
    old_party_id: Optional[str] = None
    previous_name: Optional[str] = None
    number_of_mnas: Optional[int] = None
    leader: Optional[str] = None
    authorization_date: Optional[str] = None
    address: Optional[str] = None
    leader_nomination: Optional[str] = None
    official_representative: Optional[str] = None
    official_agent: Optional[str] = None
    executive_officials: Optional[str] = None
    auditor: Optional[str] = None

