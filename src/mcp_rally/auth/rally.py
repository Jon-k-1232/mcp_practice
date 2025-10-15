"""Authentication helpers for CA Rally API access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RallyAuth:
    """Encapsulates the headers required for Rally API key authentication."""

    api_key: str

    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
            "X-RallyIntegrationName": "MCP Rally Server",
            "X-RallyIntegrationVendor": "MCP Practice",
            "X-RallyIntegrationVersion": "0.1.0",
        }
