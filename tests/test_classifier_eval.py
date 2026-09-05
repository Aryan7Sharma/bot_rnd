"""Classifier eval harness: replays the fixture set of TED-like notices
against the live classifier and compares to hand-corrected expected
scores, per the brief ("test against that instead of mocking the model").

IMPORTANT: tests/fixtures/ted_notices_raw/*.json are SYNTHETIC fixtures
(see each file's `_fixture_note`), not the ten real TED notices the brief
asks for — this sandbox has no network access to TED. Swap them for real
notices, and expected_scores.yaml for your own hand-corrected scores,
before treating this as a meaningful eval.

Requires ANTHROPIC_API_KEY and costs real API calls; not run by default
(see README.md's Tests section for the exact invocation).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from kriyon_bd.ingest.ted_parser import parse_notice
from kriyon_bd.scoring.classifier import SignalClassifier
from kriyon_bd.scoring.rubric import AXIS_NAMES

FIXTURES_DIR = Path(__file__).parent / "fixtures"
NOTICES_DIR = FIXTURES_DIR / "ted_notices_raw"
EXPECTED_SCORES_PATH = FIXTURES_DIR / "expected_scores.yaml"

SCORE_TOLERANCE = 1  # allow +/-1 per axis vs. the hand-corrected value


@pytest.fixture(scope="module")
def classifier():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set; skipping live classifier eval")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
    return SignalClassifier(api_key=api_key, model=model)


@pytest.fixture(scope="module")
def expected_scores():
    with open(EXPECTED_SCORES_PATH) as f:
        return yaml.safe_load(f)


def _fixture_ids() -> list[str]:
    return sorted(p.stem for p in NOTICES_DIR.glob("*.json"))


@pytest.mark.parametrize("fixture_id", _fixture_ids())
def test_classifier_matches_expected_scores_within_tolerance(fixture_id, classifier, expected_scores):
    raw = json.loads((NOTICES_DIR / f"{fixture_id}.json").read_text())
    signal = parse_notice(raw)
    expected = expected_scores[fixture_id]

    result = classifier.score(signal)

    for axis in AXIS_NAMES:
        actual_score = getattr(result, axis).score
        expected_score = expected[axis]
        assert abs(actual_score - expected_score) <= SCORE_TOLERANCE, (
            f"{fixture_id}/{axis}: expected {expected_score}, got {actual_score} "
            f"(justification: {getattr(result, axis).justification})"
        )
