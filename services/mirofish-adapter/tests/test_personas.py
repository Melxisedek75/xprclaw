"""Tests for agent personas."""

import pytest

from xprclaw_mirofish.models import AgentPersona
from xprclaw_mirofish.personas import DEFAULT_PERSONAS, get_all_personas, get_persona_by_id


def test_all_personas_are_valid() -> None:
    """All personas round-trip through Pydantic."""
    for persona_id, persona in DEFAULT_PERSONAS.items():
        assert persona.id == persona_id
        # Ensure it round-trips
        data = persona.model_dump()
        restored = AgentPersona(**data)
        assert restored.id == persona.id
        assert restored.name == persona.name


def test_get_all_personas_ordered() -> None:
    """get_all_personas returns personas in consistent order."""
    personas = get_all_personas()
    assert len(personas) == 6
    ids = [p.id for p in personas]
    assert ids == sorted(ids)  # Always same order


def test_get_persona_by_id() -> None:
    """get_persona_by_id retrieves personas or None."""
    whale = get_persona_by_id("whale-holder")
    assert whale is not None
    assert whale.name == "Whale Holder"
    assert whale.bias == "bullish"

    assert get_persona_by_id("nonexistent") is None


def test_personas_have_valid_traits() -> None:
    """All personas have valid trait ranges."""
    for persona in get_all_personas():
        assert persona.risk_tolerance >= 0 and persona.risk_tolerance <= 1
        assert persona.time_horizon_days > 0
        assert persona.bias in ["bullish", "bearish", "neutral", "contrarian"]
        assert len(persona.description) > 0
