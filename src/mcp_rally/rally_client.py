"""HTTP client for interacting with the CA Rally REST API."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Iterable, List, Optional

import requests

from .auth import RallyAuth
from .config import RallyConfig
from .models import RallyDefect

logger = logging.getLogger(__name__)


class RallyClient:
    """Minimal client for fetching defects from CA Rally."""

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
