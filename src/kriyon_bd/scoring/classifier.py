"""The only module in Phase 1 that calls a model. Scores a signal on the
four rubric axes and returns a one-sentence justification per axis,
enforced via Anthropic tool-use so the response is structured rather than
free-text parsed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import anthropic

from kriyon_bd.models import AxisScore, Signal, SignalScore
from kriyon_bd.scoring.rubric import AXIS_NAMES, Rubric

PROMPT_PATH = Path(__file__).parent / "prompts" / "classify_signal.md"

SCORE_TOOL = {
    "name": "record_signal_score",
    "description": "Record the four-axis score and justification for one signal.",
    "input_schema": {
        "type": "object",
        "properties": {
            axis: {
                "type": "object",
                "properties": {
                    "score": {"type": "integer", "minimum": 0, "maximum": 5},
                    "justification": {
                        "type": "string",
                        "description": "One sentence, tied to a specific detail in the notice.",
                    },
                },
                "required": ["score", "justification"],
            }
            for axis in AXIS_NAMES
        },
        "required": list(AXIS_NAMES),
    },
}


class SignalClassifier:
    def __init__(self, api_key: str, model: str, rubric: Optional[Rubric] = None) -> None:
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required to run the classifier")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._rubric = rubric or Rubric.load()

    def score(self, signal: Signal) -> SignalScore:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            tools=[SCORE_TOOL],
            tool_choice={"type": "tool", "name": "record_signal_score"},
            messages=[{"role": "user", "content": self._build_prompt(signal)}],
        )
        tool_use = next(block for block in response.content if block.type == "tool_use")
        raw: dict[str, Any] = tool_use.input

        axis_scores = {
            axis: AxisScore(score=int(raw[axis]["score"]), justification=raw[axis]["justification"])
            for axis in AXIS_NAMES
        }
        total = sum(a.score for a in axis_scores.values())

        return SignalScore(
            signal_id=signal.id,
            rubric_version=self._rubric.version,
            fit=axis_scores["fit"],
            timing=axis_scores["timing"],
            reachability=axis_scores["reachability"],
            evidence_quality=axis_scores["evidence_quality"],
            surfaced=total >= self._rubric.threshold,
            model_name=self._model,
            raw_model_response=response.model_dump(),
        )

    def _build_prompt(self, signal: Signal) -> str:
        template = PROMPT_PATH.read_text()
        axis_block = "\n".join(
            f"- **{name}**: {desc}" for name, desc in self._rubric.axis_descriptions.items()
        )
        return template.format(
            axis_block=axis_block,
            title=signal.title,
            summary=signal.summary,
            buyer_name=signal.buyer_name or "unknown",
            country=signal.country or "unknown",
            cpv_codes=", ".join(signal.cpv_codes) or "none listed",
            publication_date=signal.publication_date or "unknown",
            deadline_date=signal.deadline_date or "none listed",
            source_url=signal.source_url,
        )
