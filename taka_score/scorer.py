"""Score Aggregator — Tổng hợp điểm từ tất cả analyzers thành overall score."""
from __future__ import annotations

from taka_score.analyzers import AnalyzerResult
from taka_score.schemas.response import ScoreBreakdown

# Default weights (tổng = 100)
DEFAULT_WEIGHTS: dict[str, float] = {
    "fluency": 20.0,          # = average of rhythm + readability
    "repetition": 15.0,
    "lexical_diversity": 15.0,
    "sentence_rhythm": 15.0,
    "readability": 10.0,
    "structure_pattern": 15.0,
    "cohesion": 10.0,
}

_GRADE_TABLE = [
    (97, "A+"), (93, "A"), (90, "A-"),
    (87, "B+"), (83, "B"), (80, "B-"),
    (77, "C+"), (73, "C"), (70, "C-"),
    (67, "D+"), (60, "D"), (0, "F"),
]


def score_to_grade(score: float) -> str:
    for threshold, grade in _GRADE_TABLE:
        if score >= threshold:
            return grade
    return "F"


class ScoreAggregator:
    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        self._normalize_weights()

    def _normalize_weights(self) -> None:
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total * 100 for k, v in self.weights.items()}

    def aggregate(
        self,
        results: dict[str, AnalyzerResult],
    ) -> tuple[float, str, ScoreBreakdown]:
        """
        Tổng hợp kết quả từ các analyzers.
        
        Returns:
            (overall_score, grade, breakdown)
        """
        # Fluency = trung bình sentence_rhythm + readability
        rhythm_score = results.get("sentence_rhythm", AnalyzerResult(score=75.0)).score
        readability_score = results.get("readability", AnalyzerResult(score=75.0)).score
        fluency_score = (rhythm_score + readability_score) / 2.0

        breakdown = ScoreBreakdown(
            fluency=round(fluency_score, 1),
            repetition=round(results.get("repetition", AnalyzerResult(score=75.0)).score, 1),
            lexical_diversity=round(results.get("lexical_diversity", AnalyzerResult(score=75.0)).score, 1),
            sentence_rhythm=round(rhythm_score, 1),
            readability=round(readability_score, 1),
            structure_pattern=round(results.get("structure_pattern", AnalyzerResult(score=75.0)).score, 1),
            cohesion=round(results.get("cohesion", AnalyzerResult(score=75.0)).score, 1),
        )

        score_map = {
            "fluency": breakdown.fluency,
            "repetition": breakdown.repetition,
            "lexical_diversity": breakdown.lexical_diversity,
            "sentence_rhythm": breakdown.sentence_rhythm,
            "readability": breakdown.readability,
            "structure_pattern": breakdown.structure_pattern,
            "cohesion": breakdown.cohesion,
        }

        overall = sum(
            score_map[key] * (self.weights.get(key, 0) / 100)
            for key in score_map
        )

        return round(overall, 1), score_to_grade(overall), breakdown
