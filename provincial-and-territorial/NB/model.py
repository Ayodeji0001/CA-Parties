from typing import Optional

from pydantic import BaseModel


class Party(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    full_name: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    toll_free: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
