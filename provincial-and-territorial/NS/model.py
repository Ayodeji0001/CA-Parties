from typing import Optional

from pydantic import BaseModel


class Party(BaseModel):
    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    full_name: str
    website: Optional[str] = None
