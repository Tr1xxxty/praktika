import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
class SupportReply(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    reply: str = Field(min_length=1, max_length=2000)
    topic: Literal["delivery", "payment", "return", "warranty", "order", "other"]
    grounded: bool
    needs_clarification: bool
    handoff: bool
    order_number: str | None = Field(pattern=r"^\d{6}$")
def output_schema():
    return SupportReply.model_json_schema()
def validate(raw):
    return SupportReply.model_validate(json.loads(raw)).model_dump()
