"""Utilities for parsing standup transcripts into Rally status updates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


ID_PATTERN = re.compile(r"\b([A-Z]{1,5}\d{2,})\b")

STATE_KEYWORDS: List[Tuple[Iterable[str], str]] = [
    (("in progress", "progressing", "working on", "underway"), "In-Progress"),
    (("completed", "complete", "done", "finished"), "Completed"),
    (("accepted", "signed off", "shipped"), "Accepted"),
    (("not started", "no progress", "to do", "todo", "backlog"), "Defined"),
    (("ready for qa", "ready for test", "ready for testing", "waiting on qa"), "Completed"),
    (("testing", "in test", "qa in progress"), "In-Progress"),
    (("in review", "code review", "reviewing"), "In-Progress"),
]


def _detect_blocked(snippet_lower: str) -> Tuple[Optional[bool], Optional[str]]:
    if "blocked" not in snippet_lower and "blocker" not in snippet_lower:
        return None, None

    reason_match = re.search(
        r"\bblocked\b(?:\s+on|\s+by|\s+because of|\s+due to)?\s*(?P<reason>[^.]+)",
        snippet_lower,
    )
    if reason_match:
        reason = reason_match.group("reason").strip()
        return True, reason if reason else None
    return True, None


def _detect_state(snippet_lower: str) -> Optional[str]:
    for keywords, canonical in STATE_KEYWORDS:
        for keyword in keywords:
            if keyword in snippet_lower:
                return canonical
    return None


@dataclass(slots=True)
class TranscriptArtifactUpdate:
    """Normalized status update parsed from a meeting transcript."""

    formatted_id: str
    state: Optional[str]
    blocked: Optional[bool]
    blocked_reason: Optional[str]
    summary: str


def parse_transcript(transcript: str) -> List[TranscriptArtifactUpdate]:
    """Extract Rally artifact updates from a transcript."""

    updates: Dict[str, TranscriptArtifactUpdate] = {}

    for raw_snippet in re.split(r"[.\n]", transcript):
        snippet = raw_snippet.strip()
        if not snippet:
            continue

        matches = ID_PATTERN.findall(snippet)
        if not matches:
            continue

        snippet_lower = snippet.lower()
        state = _detect_state(snippet_lower)
        blocked, blocked_reason = _detect_blocked(snippet_lower)

        # If the transcript expresses a blocker without an explicit state,
        # assume the work is still in progress.
        if blocked and state is None:
            state = "In-Progress"

        for formatted_id in matches:
            update = TranscriptArtifactUpdate(
                formatted_id=formatted_id,
                state=state,
                blocked=blocked,
                blocked_reason=blocked_reason,
                summary=snippet,
            )
            updates[formatted_id] = update

    return list(updates.values())


__all__ = ["TranscriptArtifactUpdate", "parse_transcript"]
