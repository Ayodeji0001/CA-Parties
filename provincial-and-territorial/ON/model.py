from typing import Optional

from pydantic import BaseModel


class Party(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    party_name: str
    name_in_election_documents: Optional[str] = None
    president: Optional[str] = None
    leader: Optional[str] = None
    registered_date: Optional[str] = None
    address: Optional[str] = None
    telephone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    constituency_associations: Optional[str] = None
