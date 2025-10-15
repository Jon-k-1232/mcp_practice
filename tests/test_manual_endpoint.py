from fastapi.testclient import TestClient

from mcp_rally.deps import get_client
from mcp_rally.models import ArtifactUpdateResult
from mcp_rally.server import create_app
from mcp_rally.transcript import TranscriptArtifactUpdate


class FakeRallyClient:
    def __init__(self) -> None:
        self.last_update: TranscriptArtifactUpdate | None = None

    def apply_transcript_update(
        self,
        update: TranscriptArtifactUpdate,
        workspace: str,
        project: str | None = None,
    ) -> ArtifactUpdateResult:
        self.last_update = update
        assert workspace == "/workspace/123"
        assert project == "/project/789"
        return ArtifactUpdateResult(
            formatted_id=update.formatted_id,
            artifact_type="HierarchicalRequirement",
            applied_state_field="ScheduleState" if update.state else None,
            applied_state=update.state,
            blocked=update.blocked,
            blocked_reason=update.blocked_reason,
            summary=update.summary,
            comment_posted=True,
            comment_text=update.summary,
        )


def test_manual_artifact_update_endpoint() -> None:
    app = create_app()
    fake_client = FakeRallyClient()
    app.dependency_overrides[get_client] = lambda: fake_client

    client = TestClient(app)

    payload = {
        "workspace": "/workspace/123",
        "project": "/project/789",
        "formatted_id": "US99999",
        "state": "In-Progress",
        "comment": "Manual update from automated test.",
    }

    response = client.post("/artifacts/manual", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["formatted_id"] == "US99999"
    assert data["applied_state"] == "In-Progress"
    assert data["comment_posted"] is True
    assert "Manual update" in data["comment_text"]

    assert fake_client.last_update is not None
    assert fake_client.last_update.state == "In-Progress"
    assert fake_client.last_update.summary == "Manual update from automated test."
