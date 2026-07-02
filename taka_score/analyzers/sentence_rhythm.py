"""Sentence Rhythm Analyzer — Đo nhịp và độ đa dạng độ dài câu."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from taka_score.analyzers import BaseAnalyzer, AnalyzerResult

# Phân loại độ dài câu (theo số từ đã segment)
_SHORT_MAX = 7       # <= 7 từ: câu ngắn
_MEDIUM_MAX = 20     # 8–20 từ: câu vừa
_LONG_THRESHOLD = 40 # > 40 từ: câu quá dài (có thể gây khó đọc)

# Hệ số biến thiên (CV = std/mean) lý tưởng
_CV_IDEAL_MIN = 0.3
_CV_IDEAL_MAX = 0.9


class SentenceRhythmAnalyzer(BaseAnalyzer):

    @property
    def name(self) -> str:
        return "sentence_rhythm"

    def analyze(
        self,
        sentences: list[str],
        tokenized: list[list[str]],
        paragraphs: list[str],
    ) -> AnalyzerResult:
        lengths = [len(words) for words in tokenized if words]

        if len(lengths) < 3:
            return AnalyzerResult(
                score=50.0,
                findings=["Quá ít câu để đánh giá nhịp văn."],
            )

        avg_len = statistics.mean(lengths)
        std_len = statistics.stdev(lengths) if len(lengths) > 1 else 0.0
        cv = std_len / avg_len if avg_len > 0 else 0.0

        short = sum(1 for l in lengths if l <= _SHORT_MAX)
        medium = sum(1 for l in lengths if _SHORT_MAX < l <= _MEDIUM_MAX)
        long_ = sum(1 for l in lengths if l > _MEDIUM_MAX)
        too_long = sum(1 for l in lengths if l > _LONG_THRESHOLD)

        total = len(lengths)
        short_ratio = short / total
        too_long_ratio = too_long / total

        findings: list[str] = []
        examples: list[str] = []

        # Đánh giá CV (biến thiên nhịp câu)
        if cv < _CV_IDEAL_MIN:
            cv_score = 50.0
            findings.append(
                f"Nhịp câu đơn điệu (CV={cv:.2f}). "
                "Các câu quá đồng đều về độ dài, thiếu biến tấu."
            )
        elif cv > _CV_IDEAL_MAX:
            cv_score = 70.0
            findings.append(
                f"Nhịp câu không ổn định (CV={cv:.2f}). "
                "Độ dài câu thay đổi quá đột ngột."
            )
        else:
            cv_score = 100.0

        # Đánh giá tỷ lệ câu quá dài
        if too_long_ratio > 0.15:
            long_penalty = too_long_ratio * 50
            findings.append(
                f"Có {too_long} câu quá dài (>{_LONG_THRESHOLD} từ), "
                f"chiếm {too_long_ratio:.1%} — có thể gây khó đọc."
            )
        else:
            long_penalty = 0.0

        # Đánh giá phân bố
        if short_ratio > 0.6:
            dist_score = 70.0
            findings.append(
                f"Quá nhiều câu ngắn ({short_ratio:.1%}). "
                "Văn bản có thể cảm giác bị đứt đoạn, rời rạc."
            )
        elif short_ratio < 0.1 and too_long_ratio > 0.3:
            dist_score = 65.0
            findings.append("Quá nhiều câu dài, thiếu câu ngắn để tạo nhịp.")
        else:
            dist_score = 100.0

        overall = (cv_score * 0.5 + dist_score * 0.3 + max(0, 100 - long_penalty) * 0.2)

        examples.append(
            f"Độ dài trung bình: {avg_len:.1f} từ/câu | "
            f"Ngắn: {short} | Vừa: {medium} | Dài: {long_} | Rất dài: {too_long}"
        )

        # Ví dụ câu quá dài
        for sent, words in zip(sentences, tokenized):
            if len(words) > _LONG_THRESHOLD and len(examples) < 5:
                preview = " ".join(words[:12]) + "…"
                examples.append(f'Câu {len(words)} từ: "{preview}"')

        return AnalyzerResult(
            score=round(overall, 1),
            findings=findings,
            examples=examples,
            raw_metrics={
                "avg_length": round(avg_len, 2),
                "std_length": round(std_len, 2),
                "cv": round(cv, 3),
                "short_count": short,
                "medium_count": medium,
                "long_count": long_,
                "too_long_count": too_long,
                "total_sentences": total,
            },
        )
