"""FastAPI-based MCP server for working with CA Rally defects."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from .analysis import DefectAnalysis, analyze_defects
from .auth import RallyAuth
from .config import RallyConfig, load_config
from .models import RallyDefect
from .rally_client import RallyClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
                FrequencyBucket(name=name, count=count)
                for name, count in analysis.leading_owners
            ],
            leading_tags=[
                FrequencyBucket(name=name, count=count) for name, count in analysis.leading_tags
            ],
            submissions_by_week=analysis.submissions_by_week,
            suspected_root_causes=analysis.suspected_root_causes,
        )


@lru_cache
def get_config() -> RallyConfig:
    return load_config()


@lru_cache
def get_client() -> RallyClient:
    config = get_config()
    auth = RallyAuth(api_key=config.api_key)
    return RallyClient(config=config, auth=auth)


def create_app() -> FastAPI:
    app = FastAPI(title="MCP Rally Server", version="0.1.0")

    @app.get("/defects", response_model=List[RallyDefectModel])
    def list_defects(
        query: Optional[str] = Query(None, description="Rally WSAPI formatted query string"),
        limit: Optional[int] = Query(None, ge=1, le=1000),
        client: RallyClient = Depends(get_client),
    ) -> List[RallyDefectModel]:
        try:
            defects = client.get_defects(query=query, limit=limit)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to retrieve defects from Rally")
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return [RallyDefectModel.from_domain(defect) for defect in defects]

    @app.get("/defects/analysis", response_model=DefectAnalysisModel)
    def defect_analysis(
        query: Optional[str] = Query(None, description="Optional filter on defects"),
        limit: Optional[int] = Query(None, ge=1, le=1000),
        client: RallyClient = Depends(get_client),
    ) -> DefectAnalysisModel:
        try:
            defects = client.get_defects(query=query, limit=limit)
            analysis = analyze_defects(defects)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to analyze Rally defects")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return DefectAnalysisModel.from_domain(analysis)

    return app


def main() -> None:
    """Entrypoint for running the MCP Rally server with uvicorn."""
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()
