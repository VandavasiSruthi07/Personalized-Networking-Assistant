"""
Data Schema Definitions
------------------------
Central Pydantic models used across the whole application: request/response
bodies for the API routes, and internal data shapes passed between services.
Having these in one file keeps the event analyzer, topic generator, fact
checker, history logger, and feedback logger all speaking the same "language".
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Scenario 1: Generating Smart Starters
# ---------------------------------------------------------------------------

class EventAnalysisRequest(BaseModel):
    """Input the user gives us about the event they're attending."""
    event_description: str = Field(..., example="AI for Sustainable Cities")
    interests: List[str] = Field(
        default_factory=list,
        example=["climate change", "urban planning"],
    )


class EventAnalysisResult(BaseModel):
    """Output of the event analyzer service (theme extraction)."""
    event_description: str
    extracted_themes: List[str]
    matched_interests: List[str]


class ConversationStarterRequest(BaseModel):
    """Input to the topic generator service."""
    event_description: str
    themes: List[str]
    interests: List[str] = Field(default_factory=list)
    num_starters: int = Field(default=3, ge=1, le=5)
    backend: Optional[str] = Field(
        default="gpt2",
        description="Which generation backend to use: 'gpt2' (local, default) or 'gemini' (API-based).",
    )


class ConversationStarter(BaseModel):
    text: str
    based_on_theme: Optional[str] = None


class ConversationStarterResponse(BaseModel):
    event_description: str
    starters: List[ConversationStarter]


# ---------------------------------------------------------------------------
# Scenario 2: Quick Fact Verification
# ---------------------------------------------------------------------------

class FactCheckRequest(BaseModel):
    query: str = Field(..., example="blockchain in healthcare")


class FactCheckResult(BaseModel):
    query: str
    summary: str
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    found: bool = True


# ---------------------------------------------------------------------------
# Scenario 3: Reviewing Past Strategies (History + Feedback)
# ---------------------------------------------------------------------------

class HistoryEntryCreate(BaseModel):
    user_id: str
    event_description: str
    themes: List[str]
    starters: List[str]


class HistoryEntry(HistoryEntryCreate):
    id: int
    created_at: datetime


class FeedbackCreate(BaseModel):
    history_entry_id: int
    starter_text: str
    is_useful: bool  # True = thumbs up, False = thumbs down


class FeedbackEntry(FeedbackCreate):
    id: int
    created_at: datetime


class FeedbackSummary(BaseModel):
    history_entry_id: int
    total_feedback: int
    useful_count: int
    not_useful_count: int
