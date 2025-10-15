"""Data models used within the MCP Rally server."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse Rally ISO timestamps into datetime objects."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@dataclass(slots=True)
class RallyDefect:
    """Representation of a Rally defect record."""

    formatted_id: str
    name: str
    state: Optional[str]
    severity: Optional[str]
    owner: Optional[str]
    submitted_by: Optional[str]
    opened_date: Optional[datetime]
    last_update_date: Optional[datetime]
    tags: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_rally(cls, payload: Dict[str, Any]) -> "RallyDefect":
        """Create a `RallyDefect` from the CA Rally API response record."""
        return cls(
            formatted_id=payload.get("FormattedID", ""),
            name=payload.get("Name", ""),
            state=payload.get("State"),
            severity=payload.get("Severity"),
            owner=(payload.get("Owner") or {}).get("_refObjectName"),
            submitted_by=(payload.get("SubmittedBy") or {}).get("_refObjectName"),
            opened_date=parse_datetime(payload.get("CreationDate")),
            last_update_date=parse_datetime(payload.get("LastUpdateDate")),
            tags=[
                tag.get("_refObjectName", "")
                for tag in (payload.get("Tags") or {}).get("Results", [])
                if tag.get("_refObjectName")
            ],
            raw=payload,
        )
