"""Transcript ingestion route for Rally artifacts."""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..deps import get_client
from ..models import ArtifactUpdateResult
from ..rally_client import (
    RallyArtifactNotFoundError,
    RallyArtifactUpdateError,
    RallyClient,
    RallyUnsupportedArtifactTypeError,
)
from ..transcript import TranscriptArtifactUpdate, parse_transcript

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/artifacts", tags=["transcripts"])


class TranscriptUpdateRequest(BaseModel):
    workspace: str
    project: Optional[str]
    transcript: str


class ArtifactUpdateModel(BaseModel):
    formatted_id: str
    artifact_type: str
    applied_state_field: Optional[str]
    applied_state: Optional[str]
    blocked: Optional[bool]
    blocked_reason: Optional[str]
    summary: str
    comment_posted: bool
    comment_text: Optional[str]

    @classmethod
    def from_domain(cls, result: ArtifactUpdateResult) -> "ArtifactUpdateModel":
        return cls(
            formatted_id=result.formatted_id,
            artifact_type=result.artifact_type,
            applied_state_field=result.applied_state_field,
            applied_state=result.applied_state,
            blocked=result.blocked,
            blocked_reason=result.blocked_reason,
            summary=result.summary,
            comment_posted=result.comment_posted,
            comment_text=result.comment_text,
        )


class SkippedArtifactUpdateModel(BaseModel):
    formatted_id: str
    reason: str
    summary: str


class TranscriptUpdateResponseModel(BaseModel):
    total_mentions: int
    applied_count: int
    skipped_count: int
    applied: List[ArtifactUpdateModel]
    skipped: List[SkippedArtifactUpdateModel]


class ManualArtifactUpdateRequest(BaseModel):
    workspace: str
    project: Optional[str]
    formatted_id: str
    state: Optional[str]
    blocked: Optional[bool]
    blocked_reason: Optional[str]
    comment: str


@router.post("/transcript", response_model=TranscriptUpdateResponseModel)
def update_artifacts_from_transcript(
    payload: TranscriptUpdateRequest,
    client: RallyClient = Depends(get_client),
) -> TranscriptUpdateResponseModel:
    if not payload.workspace:
        raise HTTPException(
            status_code=400,
            detail="Workspace is required.",
        )
    if not payload.transcript or not payload.transcript.strip():
        raise HTTPException(
            status_code=400,
            detail="Transcript content is required.",
        )

    parsed_updates = parse_transcript(payload.transcript)
    if not parsed_updates:
        return TranscriptUpdateResponseModel(
            total_mentions=0,
            applied_count=0,
            skipped_count=0,
            applied=[],
            skipped=[],
        )

    applied: List[ArtifactUpdateModel] = []
    skipped: List[SkippedArtifactUpdateModel] = []

    for update in parsed_updates:
        try:
            result = client.apply_transcript_update(
                update=update,
                workspace=payload.workspace,
                project=payload.project,
            )
            applied.append(ArtifactUpdateModel.from_domain(result))
        except (
            RallyArtifactNotFoundError,
            RallyUnsupportedArtifactTypeError,
            RallyArtifactUpdateError,
        ) as exc:
            skipped.append(
                SkippedArtifactUpdateModel(
                    formatted_id=update.formatted_id,
                    reason=str(exc),
                    summary=update.summary,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error updating Rally artifact %s", update.formatted_id)
            skipped.append(
                SkippedArtifactUpdateModel(
                    formatted_id=update.formatted_id,
                    reason=f"Unexpected error: {exc}",
                    summary=update.summary,
                )
            )

    return TranscriptUpdateResponseModel(
        total_mentions=len(parsed_updates),
        applied_count=len(applied),
        skipped_count=len(skipped),
        applied=applied,
        skipped=skipped,
    )


@router.post("/manual", response_model=ArtifactUpdateModel)
def manual_artifact_update(
    payload: ManualArtifactUpdateRequest,
    client: RallyClient = Depends(get_client),
) -> ArtifactUpdateModel:
    if not payload.workspace:
        raise HTTPException(status_code=400, detail="Workspace is required.")
    if not payload.formatted_id or not payload.formatted_id.strip():
        raise HTTPException(status_code=400, detail="Formatted ID is required.")
    if not payload.comment or not payload.comment.strip():
        raise HTTPException(status_code=400, detail="Comment text is required.")

    update = TranscriptArtifactUpdate(
        formatted_id=payload.formatted_id.strip(),
        state=payload.state.strip() if payload.state else None,
        blocked=payload.blocked,
        blocked_reason=payload.blocked_reason,
        summary=payload.comment.strip(),
    )

    try:
        result = client.apply_transcript_update(
            update=update,
            workspace=payload.workspace,
            project=payload.project,
        )
    except RallyArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RallyUnsupportedArtifactTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RallyArtifactUpdateError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Unexpected error applying manual update to Rally artifact %s",
            payload.formatted_id,
        )
        raise HTTPException(status_code=502, detail=f"Unexpected error: {exc}") from exc

    return ArtifactUpdateModel.from_domain(result)


__all__ = [
    "router",
    "ArtifactUpdateModel",
    "TranscriptUpdateRequest",
    "TranscriptUpdateResponseModel",
    "ManualArtifactUpdateRequest",
]
