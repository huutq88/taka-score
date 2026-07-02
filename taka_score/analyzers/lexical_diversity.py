"""Lexical Diversity Analyzer — Đo độ đa dạng từ vựng.

Dùng MATTR (Moving Average TTR) thay TTR thông thường để tránh bias theo độ dài.
Cũng tính CTTR và tỷ lệ từ hiếm.
"""
from __future__ import annotations

import math
from collections import Counter

from taka_score.analyzers import BaseAnalyzer, AnalyzerResult

# Window size cho MATTR (từ)
_MATTR_WINDOW = 100
# Ngưỡng MATTR "tốt" cho văn xuôi tiếng Việt
_MATTR_GOOD = 0.72
_MATTR_POOR = 0.50


class LexicalDiversityAnalyzer(BaseAnalyzer):

    @property
    def name(self) -> str:
        return "lexical_diversity"

    def analyze(
        self,
        sentences: list[str],
        tokenized: list[list[str]],
        paragraphs: list[str],
    ) -> AnalyzerResult:
        all_words = [w.lower() for sent in tokenized for w in sent if w.strip()]
        total = len(all_words)

        if total < 20:
            return AnalyzerResult(
                score=50.0,
                findings=["Văn bản quá ngắn để đánh giá độ đa dạng từ vựng"],
            )

        mattr = self._mattr(all_words)
        cttr = self._cttr(all_words)
        unique_ratio = len(set(all_words)) / total

        # Score từ MATTR (trọng số cao nhất)
        if mattr >= _MATTR_GOOD:
            mattr_score = 100.0
        elif mattr <= _MATTR_POOR:
            mattr_score = 40.0
        else:
            mattr_score = 40.0 + (mattr - _MATTR_POOR) / (_MATTR_GOOD - _MATTR_POOR) * 60.0

        # Score từ CTTR
        cttr_score = min(100.0, cttr * 10)

        overall = mattr_score * 0.6 + cttr_score * 0.4

        findings: list[str] = []
        examples: list[str] = []

        if mattr < _MATTR_POOR:
            findings.append(
                f"Độ đa dạng từ vựng thấp (MATTR={mattr:.3f}). "
                "Văn bản lặp lại nhiều từ giống nhau."
            )
        elif mattr < _MATTR_GOOD:
            findings.append(f"Độ đa dạng từ vựng trung bình (MATTR={mattr:.3f}).")
        else:
            findings.append(f"Từ vựng phong phú (MATTR={mattr:.3f}).")

        # Top 5 từ hay gặp nhất (loại stop words ngắn)
        freq = Counter(w for w in all_words if len(w) > 1)
        top_words = freq.most_common(5)
        if top_words:
            examples.append(
                "Từ xuất hiện nhiều nhất: "
                + ", ".join(f'"{w}"×{c}' for w, c in top_words)
            )

        return AnalyzerResult(
            score=round(overall, 1),
            findings=findings,
            examples=examples,
            raw_metrics={
                "mattr": round(mattr, 4),
                "cttr": round(cttr, 4),
                "unique_ratio": round(unique_ratio, 4),
                "total_words": total,
                "unique_words": len(set(all_words)),
                "window_size": _MATTR_WINDOW,
            },
        )

    def _mattr(self, words: list[str]) -> float:
        """Moving Average Type-Token Ratio."""
        if len(words) <= _MATTR_WINDOW:
            types = len(set(words))
            return types / len(words) if words else 0.0

        ttrs: list[float] = []
        for i in range(len(words) - _MATTR_WINDOW + 1):
            window = words[i : i + _MATTR_WINDOW]
            ttrs.append(len(set(window)) / _MATTR_WINDOW)

        return sum(ttrs) / len(ttrs)

    def _cttr(self, words: list[str]) -> float:
        """Corrected TTR = Types / sqrt(2 * Tokens)."""
        types = len(set(words))
        tokens = len(words)
        if tokens == 0:
            return 0.0
        return types / math.sqrt(2 * tokens)
