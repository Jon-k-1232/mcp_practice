"""Route groupings for the MCP Rally FastAPI application."""

from .defects import router as defects_router
from .transcript import router as transcript_router

__all__ = ["defects_router", "transcript_router"]
