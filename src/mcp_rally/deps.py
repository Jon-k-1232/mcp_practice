"""Dependency helpers for FastAPI endpoints."""

from __future__ import annotations

import logging
from functools import lru_cache

from .auth import RallyAuth
from .config import RallyConfig, load_config
from .rally_client import RallyClient

logger = logging.getLogger(__name__)


@lru_cache
def get_config() -> RallyConfig:
    return load_config()


@lru_cache
def get_client() -> RallyClient:
    config = get_config()
    auth = RallyAuth(api_key=config.api_key)
    logger.debug("Instantiating RallyClient with base URL %s", config.base_url)
    return RallyClient(config=config, auth=auth)


__all__ = ["get_client", "get_config"]
