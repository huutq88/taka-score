"""Report Generator — Tổng hợp kết quả phân tích thành báo cáo."""
from __future__ import annotations

from taka_score.analyzers import AnalyzerResult
from taka_score.schemas.response import (
    EvaluateResponse,
    ScoreBreakdown,
    TechnicalFinding,
)

_STRENGTH_THRESHOLD = 80.0
_WEAKNESS_THRESHOLD = 65.0

_METRIC_LABELS = {
    "fluency": "Độ trôi chảy",
    "repetition": "Tránh lặp từ",
    "lexical_diversity": "Đa dạng từ vựng",
    "sentence_rhythm": "Nhịp câu",
    "readability": "Dễ đọc",
    "structure_pattern": "Đa dạng cấu trúc",
    "cohesion": "Liên kết văn bản",
}


def generate_report(
    overall_score: float,
    grade: str,
    breakdown: ScoreBreakdown,
    analyzer_results: dict[str, AnalyzerResult],
    meta: dict,
    detail_level: str = "medium",
    include_examples: bool = True,
) -> EvaluateResponse:
    score_map = {
        "fluency": breakdown.fluency,
        "repetition": breakdown.repetition,
        "lexical_diversity": breakdown.lexical_diversity,
        "sentence_rhythm": breakdown.sentence_rhythm,
        "readability": breakdown.readability,
        "structure_pattern": breakdown.structure_pattern,
        "cohesion": breakdown.cohesion,
    }

    # Strengths & weaknesses
    strengths: list[str] = []
    weaknesses: list[str] = []
    for key, score in score_map.items():
        label = _METRIC_LABELS.get(key, key)
        if score >= _STRENGTH_THRESHOLD:
            strengths.append(f"{label} ({score:.0f}/100)")
        elif score < _WEAKNESS_THRESHOLD:
            weaknesses.append(f"{label} ({score:.0f}/100)")

    # Technical findings
    findings: list[TechnicalFinding] = []
    examples: list[str] = []

    for analyzer_name, result in analyzer_results.items():
        for msg in result.findings:
            # Severity dựa theo score của chính analyzer đó
            severity = (
                "error" if result.score < 55
                else "warning" if result.score < 75
                else "info"
            )
            findings.append(TechnicalFinding(
                analyzer=analyzer_name,
                message=msg,
                severity=severity,
            ))
        if include_examples and detail_level in ("medium", "high"):
            examples.extend(result.examples)

    # Summary
    summary = _build_summary(overall_score, grade, strengths, weaknesses, meta)

    return EvaluateResponse(
        ok=True,
        overall_score=overall_score,
        grade=grade,
        scores=breakdown,
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        technical_findings=findings,
        examples=examples[:10],
        meta=meta,
    )


def _build_summary(
    score: float,
    grade: str,
    strengths: list[str],
    weaknesses: list[str],
    meta: dict,
) -> str:
    word_count = meta.get("word_count", 0)
    sent_count = meta.get("sentence_count", 0)
    dialogue_ratio = meta.get("dialogue_ratio", 0.0)

    level = (
        "xuất sắc" if score >= 90
        else "tốt" if score >= 80
        else "khá" if score >= 70
        else "trung bình" if score >= 60
        else "cần cải thiện"
    )

    lines = [
        f"Văn bản ({word_count} âm tiết, {sent_count} câu) đạt mức **{level}** "
        f"với điểm tổng {score}/100 (hạng {grade}).",
    ]

    if dialogue_ratio > 0.3:
        lines.append(
            f"Lưu ý: {dialogue_ratio:.1%} nội dung là lời thoại "
            "(không ảnh hưởng đến điểm tường thuật)."
        )

    if strengths:
        lines.append(f"Điểm mạnh: {', '.join(strengths[:3])}.")
    if weaknesses:
        lines.append(f"Cần cải thiện: {', '.join(weaknesses[:3])}.")

    return " ".join(lines)
