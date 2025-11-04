from pydantic import BaseModel, Field
from typing import List

class PolicyBriefRequest(BaseModel):
    document: str = Field(..., min_length=50, max_length=10000)
    audience: str = Field(default="citizen", pattern="^(citizen|journalist|small business owner)$")
    language: str = Field(default="en", pattern="^(en|sw|am)$")

class PolicyBriefResponse(BaseModel):
    summary: str
    key_obligations: List[str]
    effective_date: str
    confidence: str