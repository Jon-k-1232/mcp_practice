"""Defect-related FastAPI routes."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..analysis import DefectAnalysis, analyze_defects
from ..deps import get_client
from ..models import RallyDefect
from ..rally_client import RallyClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/defects", tags=["defects"])


def _parse_datetime(value: Optional[str], field: str) -> Optional[datetime]:
    if value is None:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid datetime format for {field}; use ISO 8601.",
        ) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class RallyDefectModel(BaseModel):
    formatted_id: str
    name: str
    state: Optional[str]
    severity: Optional[str]
    owner: Optional[str]
    submitted_by: Optional[str]
    opened_date: Optional[str]
    last_update_date: Optional[str]
    tags: List[str]

    @classmethod
    def from_domain(cls, defect: RallyDefect) -> "RallyDefectModel":
        return cls(
            formatted_id=defect.formatted_id,
            name=defect.name,
            state=defect.state,
            severity=defect.severity,
            owner=defect.owner,
            submitted_by=defect.submitted_by,
            opened_date=defect.opened_date.isoformat() if defect.opened_date else None,
            last_update_date=(
                defect.last_update_date.isoformat() if defect.last_update_date else None
            ),
            tags=defect.tags,
        )


class FrequencyBucket(BaseModel):
    name: str
    count: int


class DefectAnalysisModel(BaseModel):
    total_defects: int
    by_state: dict[str, int]
    by_severity: dict[str, int]
    leading_owners: List[FrequencyBucket]
    leading_tags: List[FrequencyBucket]
    submissions_by_week: dict[str, int]
    suspected_root_causes: List[str]

    @classmethod
    def from_domain(cls, analysis: DefectAnalysis) -> "DefectAnalysisModel":
        return cls(
            total_defects=analysis.total_defects,
            by_state=analysis.by_state,
            by_severity=analysis.by_severity,
            leading_owners=[
                FrequencyBucket(name=name, count=count) for name, count in analysis.leading_owners
            ],
            leading_tags=[
                FrequencyBucket(name=name, count=count) for name, count in analysis.leading_tags
            ],
            submissions_by_week=analysis.submissions_by_week,
            suspected_root_causes=analysis.suspected_root_causes,
        )


@router.get("", response_model=List[RallyDefectModel])
def list_defects(
    query: Optional[str] = Query(None, description="Rally WSAPI formatted query string"),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    workspace: str = Query(..., description="Workspace scope for this request"),
    project: Optional[str] = Query(None, description="Override project scope for this request"),
    state: Optional[str] = Query(None, description='Filter by defect state, e.g. "Open"'),
    created_after: Optional[str] = Query(
        None, description="Only include defects created on/after this ISO timestamp"
    ),
    created_before: Optional[str] = Query(
        None, description="Only include defects created on/before this ISO timestamp"
    ),
    updated_after: Optional[str] = Query(
        None, description="Only include defects updated on/after this ISO timestamp"
    ),
    updated_before: Optional[str] = Query(
        None, description="Only include defects updated on/before this ISO timestamp"
    ),
    client: RallyClient = Depends(get_client),
) -> List[RallyDefectModel]:
    if not workspace:
        raise HTTPException(
            status_code=400,
            detail="Workspace query parameter is required.",
        )

    created_after_dt = _parse_datetime(created_after, "created_after")
    created_before_dt = _parse_datetime(created_before, "created_before")
    updated_after_dt = _parse_datetime(updated_after, "updated_after")
    updated_before_dt = _parse_datetime(updated_before, "updated_before")
    normalized_state = state.strip() if state else None

    try:
        defects = client.get_defects(
            query=query,
            limit=limit,
            workspace=workspace,
            project=project,
            state=normalized_state,
            created_after=created_after_dt,
            created_before=created_before_dt,
            updated_after=updated_after_dt,
            updated_before=updated_before_dt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to retrieve defects from Rally")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return [RallyDefectModel.from_domain(defect) for defect in defects]


@router.get("/analysis", response_model=DefectAnalysisModel)
def defect_analysis(
    query: Optional[str] = Query(None, description="Optional filter on defects"),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    workspace: str = Query(..., description="Workspace scope for this request"),
    project: Optional[str] = Query(None, description="Override project scope for this request"),
    state: Optional[str] = Query(None, description='Filter by defect state, e.g. "Closed"'),
    created_after: Optional[str] = Query(
        None, description="Only include defects created on/after this ISO timestamp"
    ),
    created_before: Optional[str] = Query(
        None, description="Only include defects created on/before this ISO timestamp"
    ),
    updated_after: Optional[str] = Query(
        None, description="Only include defects updated on/after this ISO timestamp"
    ),
    updated_before: Optional[str] = Query(
        None, description="Only include defects updated on/before this ISO timestamp"
    ),
    client: RallyClient = Depends(get_client),
) -> DefectAnalysisModel:
    if not workspace:
        raise HTTPException(
            status_code=400,
            detail="Workspace query parameter is required.",
        )

    created_after_dt = _parse_datetime(created_after, "created_after")
    created_before_dt = _parse_datetime(created_before, "created_before")
    updated_after_dt = _parse_datetime(updated_after, "updated_after")
    updated_before_dt = _parse_datetime(updated_before, "updated_before")
    normalized_state = state.strip() if state else None

    try:
        defects = client.get_defects(
            query=query,
            limit=limit,
            workspace=workspace,
            project=project,
            state=normalized_state,
            created_after=created_after_dt,
            created_before=created_before_dt,
            updated_after=updated_after_dt,
            updated_before=updated_before_dt,
        )
        analysis = analyze_defects(defects)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to analyze Rally defects")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return DefectAnalysisModel.from_domain(analysis)


__all__ = [
    "router",
    "DefectAnalysisModel",
    "FrequencyBucket",
    "RallyDefectModel",
]
