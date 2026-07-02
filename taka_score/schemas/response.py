"""Response schema cho MCP tool evaluate_vietnamese_style_technical."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class ScoreBreakdown(BaseModel):
    fluency: float
    repetition: float
    lexical_diversity: float
    sentence_rhythm: float
    readability: float
    structure_pattern: float
    cohesion: float


class TechnicalFinding(BaseModel):
    analyzer: str
    message: str
    severity: str   # "info" | "warning" | "error"


class SuspiciousSentence(BaseModel):
    text: str
    reason: str


class EvaluateResponse(BaseModel):
    ok: bool = True
    overall_score: float
    grade: str           # A+, A, A-, B+, B, B-, C+, C, D
    scores: ScoreBreakdown
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    technical_findings: list[TechnicalFinding]
    suspicious_sentences: list[SuspiciousSentence] = []
    examples: list[str]
    meta: dict           # word_count, sentence_count, paragraph_count, dialogue_ratio


class EvaluateError(BaseModel):
    ok: bool = False
    error: str
    code: str            # TEXT_TOO_SHORT | TEXT_TOO_LONG | INVALID_INPUT | INTERNAL_ERROR
    detail: Optional[str] = None
