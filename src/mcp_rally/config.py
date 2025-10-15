"""Configuration utilities for the MCP Rally server."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class RallyConfig:
    """Configuration values required to talk to CA Rally."""

    api_key: str
    base_url: str = "https://rally1.rallydev.com"
    workspace: Optional[str] = None
    project: Optional[str] = None
    page_size: int = 200

    @property
    def defects_endpoint(self) -> str:
        return f"{self.base_url.rstrip('/')}/slm/webservice/v2.0/defect"


def load_config(env_file: Optional[str] = None) -> RallyConfig:
    """Load Rally configuration from environment variables.

    Parameters
    ----------
    env_file:
        Optional path to a `.env` file. If not provided the loader searches the current working
        directory and its parents.
    """

    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    from os import getenv

    api_key = getenv("RALLY_API_KEY")
    if not api_key:
        raise ValueError("Missing required environment variable RALLY_API_KEY.")

    base_url = getenv("RALLY_BASE_URL", "https://rally1.rallydev.com")
    workspace = getenv("RALLY_WORKSPACE") or None
    project = getenv("RALLY_PROJECT") or None

    try:
        page_size = int(getenv("RALLY_PAGE_SIZE", "200"))
    except ValueError as exc:
        raise ValueError("RALLY_PAGE_SIZE must be an integer.") from exc

    return RallyConfig(
        api_key=api_key,
        base_url=base_url,
        workspace=workspace,
        project=project,
        page_size=page_size,
    )
