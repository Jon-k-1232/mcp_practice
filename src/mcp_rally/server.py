"""FastAPI application setup for the MCP Rally service."""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from .api import defects_router, transcript_router

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(title="MCP Rally Server", version="0.1.0")
    app.include_router(defects_router)
    app.include_router(transcript_router)
    return app


def main() -> None:
    """Entrypoint for running the MCP Rally server with uvicorn."""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
