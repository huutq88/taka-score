"""Repetition Analyzer — Phát hiện lặp từ, cụm từ, cấu trúc mở đầu câu."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from taka_score.analyzers import BaseAnalyzer, AnalyzerResult

# Cửa sổ tìm lặp từ (đơn vị: từ)
_WORD_REPEAT_WINDOW = 15
# Ngưỡng: từ xuất hiện >= N lần trong cửa sổ là lặp
_WORD_REPEAT_THRESHOLD = 4
# N-gram để phát hiện lặp cụm từ
_NGRAM_SIZES = (2, 3)
# Tỷ lệ n-gram có xuất hiện > 1 lần để coi là "có vấn đề"
_NGRAM_REPEAT_RATIO_THRESHOLD = 0.08
# Số từ đầu câu để so sánh pattern mở đầu
_OPENER_WORDS = 2


class RepetitionAnalyzer(BaseAnalyzer):

    @property
    def name(self) -> str:
        return "repetition"

    def analyze(
        self,
        sentences: list[str],
        tokenized: list[list[str]],
        paragraphs: list[str],
    ) -> AnalyzerResult:
        if not tokenized:
            return AnalyzerResult(score=100.0)

        word_score, word_findings, word_examples = self._word_repetition(tokenized)
        ngram_score, ngram_findings, ngram_examples = self._ngram_repetition(tokenized)
        opener_score, opener_findings, opener_examples = self._opener_repetition(tokenized)

        overall = (word_score * 0.4 + ngram_score * 0.3 + opener_score * 0.3)

        return AnalyzerResult(
            score=round(overall, 1),
            findings=word_findings + ngram_findings + opener_findings,
            examples=(word_examples + ngram_examples + opener_examples)[:8],
            raw_metrics={
                "word_repeat_score": word_score,
                "ngram_repeat_score": ngram_score,
                "opener_repeat_score": opener_score,
            },
        )

    # ──────────────────────────────────────────────────────────────
    # Word-level repetition (sliding window)
    # ──────────────────────────────────────────────────────────────
    def _word_repetition(
        self, tokenized: list[list[str]]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []
        repeat_count = 0

        all_words = [w.lower() for sent in tokenized for w in sent]
        total = len(all_words)
        if total == 0:
            return 100.0, [], []

        for i in range(len(all_words) - _WORD_REPEAT_WINDOW):
            window = all_words[i : i + _WORD_REPEAT_WINDOW]
            c = Counter(window)
            for word, freq in c.items():
                if freq >= _WORD_REPEAT_THRESHOLD and len(word) > 1:
                    repeat_count += 1
                    if len(examples) < 4:
                        examples.append(f'Từ "{word}" lặp {freq} lần trong {_WORD_REPEAT_WINDOW} từ liên tiếp')

        ratio = repeat_count / max(total, 1)
        if ratio > 0.05:
            findings.append(f"Lặp từ nhiều: {repeat_count} trường hợp trong toàn văn bản")
        score = max(0.0, 100.0 - ratio * 500)
        return round(score, 1), findings, examples

    # ──────────────────────────────────────────────────────────────
    # N-gram repetition
    # ──────────────────────────────────────────────────────────────
    def _ngram_repetition(
        self, tokenized: list[list[str]]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []
        all_words = [w.lower() for sent in tokenized for w in sent]
        total_penalty = 0.0

        for n in _NGRAM_SIZES:
            ngrams = [
                " ".join(all_words[i : i + n])
                for i in range(len(all_words) - n + 1)
            ]
            if not ngrams:
                continue
            c = Counter(ngrams)
            # Số n-gram xuất hiện nhiều hơn 1 lần (unique repeated)
            repeated = {ng: cnt for ng, cnt in c.items() if cnt > 1}
            # Tỷ lệ = số lượt bị lặp thêm / tổng
            extra_repeats = sum(cnt - 1 for cnt in repeated.values())
            ratio = extra_repeats / max(len(ngrams), 1)

            if ratio > _NGRAM_REPEAT_RATIO_THRESHOLD:
                findings.append(
                    f"Lặp cụm {n} từ: {len(repeated)} cụm bị lặp "
                    f"(tỷ lệ {ratio:.1%})"
                )
                total_penalty += ratio * 60  # tăng penalty

            for ng, cnt in sorted(repeated.items(), key=lambda x: -x[1])[:2]:
                if len(examples) < 4:
                    examples.append(f'Cụm "{ng}" lặp {cnt} lần')

        score = max(0.0, 100.0 - total_penalty)
        return round(score, 1), findings, examples

    # ──────────────────────────────────────────────────────────────
    # Sentence opener repetition
    # ──────────────────────────────────────────────────────────────
    def _opener_repetition(
        self, tokenized: list[list[str]]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []
        openers = []

        for words in tokenized:
            if words:
                opener = " ".join(w.lower() for w in words[:_OPENER_WORDS])
                openers.append(opener)

        if not openers:
            return 100.0, [], []

        c = Counter(openers)
        total = len(openers)
        repeated_openers = {op: cnt for op, cnt in c.items() if cnt > 2}
        penalty = 0.0

        for op, cnt in sorted(repeated_openers.items(), key=lambda x: -x[1])[:3]:
            ratio = cnt / total
            penalty += ratio * 40
            findings.append(
                f'Mở đầu câu "{op}" lặp {cnt}/{total} lần ({ratio:.1%})'
            )
            examples.append(f'Câu bắt đầu bằng "{op}" × {cnt}')

        score = max(0.0, 100.0 - penalty)
        return round(score, 1), findings, examples
