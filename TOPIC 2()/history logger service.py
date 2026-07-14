"""
History Logger Service
------------------------
Scenario 3: lets users log a completed "smart starters" session and later
review what was generated in previous sessions.
"""

import json
from datetime import datetime, timezone
from typing import List

from app.database import get_connection
from app.schemas import HistoryEntry, HistoryEntryCreate


def log_history(entry: HistoryEntryCreate) -> HistoryEntry:
    """Persist a new history entry and return it with its assigned id."""
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO history (user_id, event_description, themes, starters, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry.user_id,
                entry.event_description,
                json.dumps(entry.themes),
                json.dumps(entry.starters),
                created_at,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid

    return HistoryEntry(id=new_id, created_at=created_at, **entry.model_dump())


def get_history_for_user(user_id: str) -> List[HistoryEntry]:
    """Return all history entries for a given user, most recent first."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, event_description, themes, starters, created_at
            FROM history
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

    return [
        HistoryEntry(
            id=row["id"],
            user_id=row["user_id"],
            event_description=row["event_description"],
            themes=json.loads(row["themes"]),
            starters=json.loads(row["starters"]),
            created_at=row["created_at"],
        )
        for row in rows
    ]


def get_history_entry(history_entry_id: int) -> HistoryEntry | None:
    """Fetch a single history entry by id, or None if it doesn't exist."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, event_description, themes, starters, created_at
            FROM history WHERE id = ?
            """,
            (history_entry_id,),
        ).fetchone()

    if row is None:
        return None

    return HistoryEntry(
        id=row["id"],
        user_id=row["user_id"],
        event_description=row["event_description"],
        themes=json.loads(row["themes"]),
        starters=json.loads(row["starters"]),
        created_at=row["created_at"],
    )
