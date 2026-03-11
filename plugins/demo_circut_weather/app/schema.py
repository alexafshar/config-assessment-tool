from typing import Any, Literal, AsyncIterable
from pydantic import BaseModel

class ResponseFormat(BaseModel):
    status: Literal["completed", "input_required", "error"]  # Structured status of the agent reply
    message: str