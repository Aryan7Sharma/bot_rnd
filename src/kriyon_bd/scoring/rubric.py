"""Loads and validates config/rubric.toml — the versioned scoring rubric.
Treat that file as config, not code: bump its `version` field on any
substantive edit so `signal_scores.rubric_version` stays a meaningful
audit trail for the Phase 2 eval harness.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass

from kriyon_bd.settings import CONFIG_DIR

AXIS_NAMES = ("fit", "timing", "reachability", "evidence_quality")


@dataclass(frozen=True)
class Rubric:
    version: str
    threshold: int
    axis_descriptions: dict[str, str]

    @classmethod
    def load(cls) -> "Rubric":
        with open(CONFIG_DIR / "rubric.toml", "rb") as f:
            data = tomllib.load(f)
        axes = data["axes"]
        descriptions = {name: axes[name]["description"] for name in AXIS_NAMES}
        return cls(
            version=data["version"],
            threshold=data["surfacing"]["threshold"],
            axis_descriptions=descriptions,
        )
