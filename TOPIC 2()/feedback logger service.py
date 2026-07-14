"""
Feedback Logger Service
-------------------------
Scenario 3 (continued): lets users mark specific conversation starters as
useful (thumbs up) or not useful (thumbs down), and provides an aggregated
summary of feedback for a given history entry. This feedback loop is what
lets the assistant "improve personalization" over time.
"""

from datetime import datetime, timezone
from typing import List

from app.database import get_connection
from app.schemas import FeedbackCreate, FeedbackEntry, FeedbackSummary


def log_feedback(feedback: FeedbackCreate) -> FeedbackEntry:
    """Persist a thumbs up/down for a specific generated starter."""
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO feedback (history_entry_id, starter_text, is_useful, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                feedback.history_entry_id,
                feedback.starter_text,
                int(feedback.is_useful),
                created_at,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

    return FeedbackEntry(id=new_id, created_at=created_at, **feedback.model_dump())


def get_feedback_for_history_entry(history_entry_id: int) -> List[FeedbackEntry]:
    """Return every feedback record logged against a given history entry."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, history_entry_id, starter_text, is_useful, created_at
            FROM feedback WHERE history_entry_id = ?
            ORDER BY created_at DESC
            """,
            (history_entry_id,),
        ).fetchall()

    return [
        FeedbackEntry(
            id=row["id"],
            history_entry_id=row["history_entry_id"],
            starter_text=row["starter_text"],
            is_useful=bool(row["is_useful"]),
            created_at=row["created_at"],
        )
        for row in rows
    ]


def get_feedback_summary(history_entry_id: int) -> FeedbackSummary:
    """Aggregate thumbs up/down counts for a given history entry."""
    entries = get_feedback_for_history_entry(history_entry_id)
    useful_count = sum(1 for e in entries if e.is_useful)

    return FeedbackSummary(
        history_entry_id=history_entry_id,
        total_feedback=len(entries),
        useful_count=useful_count,
        not_useful_count=len(entries) - useful_count,
    )
