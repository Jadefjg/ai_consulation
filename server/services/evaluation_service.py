"""AI 回复离线/在线质量评估指标。"""
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EvaluationResult:
    citation_coverage: float
    groundedness: float
    safety_disclaimer: bool
    answer_length: int

    def as_dict(self) -> dict:
        return {
            "citation_coverage": round(self.citation_coverage, 4),
            "groundedness": round(self.groundedness, 4),
            "safety_disclaimer": self.safety_disclaimer,
            "answer_length": self.answer_length,
        }


def evaluate_answer(answer: str, references: Iterable[dict], disclaimer: str) -> EvaluationResult:
    answer = answer or ""
    refs = list(references or [])
    ref_terms = {term for ref in refs for term in str(ref.get("content", "")).split() if len(term) >= 2}
    answer_terms = {term for term in answer.split() if len(term) >= 2}
    groundedness = len(answer_terms & ref_terms) / max(len(answer_terms), 1)
    return EvaluationResult(
        citation_coverage=1.0 if refs and any(ref.get("content") for ref in refs) else 0.0,
        groundedness=min(groundedness, 1.0),
        safety_disclaimer=disclaimer in answer,
        answer_length=len(answer),
    )
