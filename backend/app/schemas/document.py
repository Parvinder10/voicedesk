from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    organization_id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: str
    error_message: Optional[str] = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    top_k: int = Field(4, ge=1, le=10)


class SourceReference(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    score: float
    snippet: str


class DocumentQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceReference]
    has_answer: bool
    is_fallback: bool
