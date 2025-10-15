"""Utilities for analyzing CA Rally defect data."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from ..models import RallyDefect


@dataclass(slots=True)
class DefectAnalysis:
    """Summarizes trends and potential root causes in Rally defects."""

    total_defects: int
    by_state: Dict[str, int]
    by_severity: Dict[str, int]
    leading_owners: List[Tuple[str, int]]
    leading_tags: List[Tuple[str, int]]
    submissions_by_week: Dict[str, int]
    suspected_root_causes: List[str]


def _bucket_by_week(defects: Iterable[RallyDefect]) -> Dict[str, int]:
    buckets: Dict[str, int] = defaultdict(int)
    for defect in defects:
        if defect.opened_date:
            buckets[defect.opened_date.strftime("%Y-%W")] += 1
    return dict(sorted(buckets.items()))


def _heuristic_root_causes(defects: Iterable[RallyDefect]) -> List[str]:
    causes: Counter[str] = Counter()
    for defect in defects:
        text = " ".join(defect.tags + [defect.name]).lower()
        if "environment" in text:
            causes["Environment Instability"] += 1
        if "regression" in text:
            causes["Regression Issues"] += 1
        if "performance" in text:
            causes["Performance Bottlenecks"] += 1
        if "data" in text:
            causes["Data Quality"] += 1
        if "automation" in text:
            causes["Automation Gap"] += 1

    return [f"{cause} ({count})" for cause, count in causes.most_common()]


def analyze_defects(defects: List[RallyDefect]) -> DefectAnalysis:
    """Create an aggregate view of defects for insight reporting."""

    if not defects:
        return DefectAnalysis(
            total_defects=0,
            by_state={},
            by_severity={},
            leading_owners=[],
            leading_tags=[],
            submissions_by_week={},
            suspected_root_causes=[],
        )

    by_state = Counter(defect.state or "Unknown" for defect in defects)
    by_severity = Counter(defect.severity or "Unknown" for defect in defects)
    owner_counts = Counter(defect.owner or "Unassigned" for defect in defects)

    tag_counter: Counter[str] = Counter()
    for defect in defects:
        tag_counter.update(defect.tags)

    return DefectAnalysis(
        total_defects=len(defects),
        by_state=dict(by_state),
        by_severity=dict(by_severity),
        leading_owners=owner_counts.most_common(5),
        leading_tags=tag_counter.most_common(10),
        submissions_by_week=_bucket_by_week(defects),
        suspected_root_causes=_heuristic_root_causes(defects),
    )
