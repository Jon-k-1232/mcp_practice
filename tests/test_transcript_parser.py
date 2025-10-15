from mcp_rally.transcript import parse_transcript


def test_parse_transcript_identifies_states_and_blockers() -> None:
    transcript = (
        "US12345 is in progress and waiting on QA. "
        "DE54321 is blocked by database migration issues. "
        "TA11101 is done and ready for review."
    )

    updates = {item.formatted_id: item for item in parse_transcript(transcript)}

    assert updates["US12345"].state == "In-Progress"
    assert updates["US12345"].blocked is None

    assert updates["DE54321"].state == "In-Progress"  # blocker implies in-progress when no state
    assert updates["DE54321"].blocked is True
    assert "database migration" in (updates["DE54321"].blocked_reason or "")

    assert updates["TA11101"].state == "Completed"
    assert updates["TA11101"].blocked is None
