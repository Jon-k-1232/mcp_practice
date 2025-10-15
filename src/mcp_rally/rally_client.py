"""HTTP client for interacting with the CA Rally REST API."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import requests

from .auth import RallyAuth
from .config import RallyConfig
from .models import ArtifactUpdateResult, RallyArtifact, RallyDefect
from .transcript import TranscriptArtifactUpdate

logger = logging.getLogger(__name__)


class RallyArtifactNotFoundError(Exception):
    """Raised when no Rally artifact matches the requested formatted ID."""


class RallyArtifactUpdateError(Exception):
    """Raised when Rally rejects an update operation."""


class RallyUnsupportedArtifactTypeError(RallyArtifactUpdateError):
    """Raised when an artifact type does not support the requested fields."""


STATE_FIELD_BY_TYPE: Dict[str, str] = {
    "HierarchicalRequirement": "ScheduleState",
    "Defect": "State",
    "Task": "State",
}

BLOCKED_SUPPORTED_TYPES = {"HierarchicalRequirement", "Defect", "Task"}


class RallyClient:
    """Client for fetching and updating work items in CA Rally."""

    def __init__(
        self,
        config: RallyConfig,
        auth: RallyAuth,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._config = config
        self._auth = auth
        self._session = session or requests.Session()

    def _base_params(self, workspace: str, project: Optional[str]) -> Dict[str, str]:
        params: Dict[str, str] = {
            "pagesize": str(self._config.page_size),
            "include": "Permissions,Owner,SubmittedBy,Tags",
            "fetch": "true",
            "start": "1",
        }
        if not workspace:
            raise ValueError("Workspace scope is required.")
        params["workspace"] = workspace
        if project:
            params["project"] = project
        return params

    def _scope_params(self, workspace: str, project: Optional[str]) -> Dict[str, str]:
        if not workspace:
            raise ValueError("Workspace scope is required.")
        params: Dict[str, str] = {"workspace": workspace}
        if project:
            params["project"] = project
        return params

    def get_defects(
        self,
        query: Optional[str] = None,
        updated_after: Optional[datetime] = None,
        updated_before: Optional[datetime] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: Optional[int] = None,
        workspace: str,
        project: Optional[str] = None,
        state: Optional[str] = None,
    ) -> List[RallyDefect]:
        """Fetch defects from Rally, optionally filtered.

        Parameters
        ----------
        query:
            Rally query string, e.g. `(State = "Open")`. See Rally WS API docs.
        updated_after:
            If provided, only defects updated since that timestamp are returned.
        updated_before:
            Upper bound on last update timestamp.
        created_after:
            Lower bound on creation timestamp.
        created_before:
            Upper bound on creation timestamp.
        limit:
            Maximum number of defects to return.
        workspace:
            Workspace scope identifier (required).
        project:
            Optional project scope override.
        state:
            Optional state filter (e.g., "Open", "Closed").
        """

        params = self._base_params(workspace=workspace, project=project)
        query_parts: List[str] = []
        if query:
            normalized = query.strip()
            if not normalized.startswith("("):
                normalized = f"({normalized})"
            query_parts.append(normalized)
        if updated_after:
            query_parts.append(f"(LastUpdateDate >= {updated_after.isoformat()})")
        if updated_before:
            query_parts.append(f"(LastUpdateDate <= {updated_before.isoformat()})")
        if created_after:
            query_parts.append(f"(CreationDate >= {created_after.isoformat()})")
        if created_before:
            query_parts.append(f"(CreationDate <= {created_before.isoformat()})")
        if state:
            query_parts.append(f'(State = "{state}")')
        if query_parts:
            params["query"] = " AND ".join(query_parts)

        collected: List[RallyDefect] = []
        start = 1
        while True:
            params["start"] = str(start)
            response = self._session.get(
                self._config.defects_endpoint,
                headers=self._auth.headers(),
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            query_result = payload.get("QueryResult", {})
            results: Iterable[Dict] = query_result.get("Results", [])

            for raw_defect in results:
                collected.append(RallyDefect.from_rally(raw_defect))
                if limit and len(collected) >= limit:
                    return collected

            total_result_count = int(query_result.get("TotalResultCount", 0))
            page_size = int(query_result.get("PageSize", self._config.page_size))

            start += page_size
            if start > total_result_count:
                break

        return collected

    def find_artifact(
        self,
        formatted_id: str,
        workspace: str,
        project: Optional[str] = None,
    ) -> RallyArtifact:
        """Lookup any Rally artifact by its formatted ID."""

        params = self._scope_params(workspace, project)
        params.update(
            {
                "query": f'(FormattedID = "{formatted_id}")',
                "pagesize": "1",
                "start": "1",
                "fetch": (
                    "FormattedID,Name,State,ScheduleState,Blocked,BlockedReason," "_ref,_type"
                ),
            }
        )

        response = self._session.get(
            self._config.artifact_endpoint,
            headers=self._auth.headers(),
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        results: Iterable[Dict[str, Any]] = payload.get("QueryResult", {}).get("Results", [])
        try:
            raw_artifact = next(iter(results))
        except StopIteration as exc:
            raise RallyArtifactNotFoundError(
                f"No Rally work item found for formatted ID {formatted_id}."
            ) from exc

        return RallyArtifact.from_rally(raw_artifact)

    def _state_field_for_artifact(self, artifact: RallyArtifact) -> Optional[str]:
        state_field = STATE_FIELD_BY_TYPE.get(artifact.type)
        if state_field:
            return state_field
        # Avoid portfolio items until explicit mapping exists.
        if artifact.type.startswith("PortfolioItem/"):
            return None
        return STATE_FIELD_BY_TYPE.get(artifact.raw.get("_type", ""))

    def _create_conversation_post(self, artifact_ref: str, text: str) -> str:
        payload = {
            "ConversationPost": {
                "Artifact": artifact_ref,
                "Text": text,
            }
        }
        response = self._session.post(
            self._config.conversation_post_endpoint,
            headers=self._auth.headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json().get("CreateResult") or {}
        errors: List[str] = result.get("Errors", [])
        if errors:
            raise RallyArtifactUpdateError(errors[0])
        created_ref = (result.get("Object") or {}).get("_ref", "")
        return created_ref

    def apply_transcript_update(
        self,
        update: TranscriptArtifactUpdate,
        workspace: str,
        project: Optional[str] = None,
    ) -> ArtifactUpdateResult:
        """Apply a parsed transcript update to the corresponding Rally artifact."""

        artifact = self.find_artifact(
            formatted_id=update.formatted_id,
            workspace=workspace,
            project=project,
        )

        body: Dict[str, Any] = {}
        applied_state: Optional[str] = None
        applied_state_field: Optional[str] = None

        state_field = self._state_field_for_artifact(artifact)
        if update.state:
            if not state_field:
                raise RallyUnsupportedArtifactTypeError(
                    f"Artifact {update.formatted_id} ({artifact.type}) does not support automatic state updates."
                )
            body[state_field] = update.state
            applied_state = update.state
            applied_state_field = state_field

        if update.blocked is not None:
            if artifact.type not in BLOCKED_SUPPORTED_TYPES:
                logger.info(
                    "Skipping blocked flag for %s (%s); type does not support Blocked field.",
                    update.formatted_id,
                    artifact.type,
                )
            else:
                body["Blocked"] = update.blocked
                if update.blocked:
                    body["BlockedReason"] = update.blocked_reason or update.summary
                else:
                    body["BlockedReason"] = ""

        if body:
            payload = {artifact.type: body}
            response = self._session.post(
                artifact.ref,
                headers=self._auth.headers(),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json().get("OperationResult") or {}
            errors: List[str] = result.get("Errors", [])
            if errors:
                raise RallyArtifactUpdateError(errors[0])

        comment_posted = False
        if update.summary:
            self._create_conversation_post(artifact.ref, update.summary)
            comment_posted = True

        return ArtifactUpdateResult(
            formatted_id=artifact.formatted_id,
            artifact_type=artifact.type,
            applied_state_field=applied_state_field,
            applied_state=applied_state,
            blocked=body.get("Blocked") if "Blocked" in body else None,
            blocked_reason=body.get("BlockedReason"),
            summary=update.summary,
            comment_posted=comment_posted,
            comment_text=update.summary if comment_posted else None,
        )
