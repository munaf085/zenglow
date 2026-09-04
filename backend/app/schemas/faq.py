"""
FAQ schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FAQCreate(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1)


class FAQResponse(BaseModel):
    id: UUID
    business_id: UUID
    question: str
    answer: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}