"""Structure Pattern Analyzer — Phát hiện lặp mẫu ngữ pháp và cấu trúc câu."""
from __future__ import annotations

from collections import Counter

from taka_score.analyzers import BaseAnalyzer, AnalyzerResult

# Số từ đầu để so sánh opener pattern
_OPENER_LEN = 3
# Chuỗi câu cùng pattern liên tiếp tối thiểu coi là "có vấn đề"
_CONSECUTIVE_THRESHOLD = 3
# Tỷ lệ câu bị lặp pattern để phạt điểm
_PATTERN_RATIO_THRESHOLD = 0.20


class StructurePatternAnalyzer(BaseAnalyzer):

    @property
    def name(self) -> str:
        return "structure_pattern"

    def analyze(
        self,
        sentences: list[str],
        tokenized: list[list[str]],
        paragraphs: list[str],
    ) -> AnalyzerResult:
        if len(tokenized) < 4:
            return AnalyzerResult(score=100.0)

        opener_score, opener_findings, opener_examples = self._opener_patterns(tokenized)
        consec_score, consec_findings, consec_examples = self._consecutive_same_opener(tokenized)

        overall = opener_score * 0.5 + consec_score * 0.5

        return AnalyzerResult(
            score=round(overall, 1),
            findings=opener_findings + consec_findings,
            examples=(opener_examples + consec_examples)[:6],
            raw_metrics={
                "opener_score": opener_score,
                "consecutive_score": consec_score,
            },
        )

    def _opener_patterns(
        self, tokenized: list[list[str]]
    ) -> tuple[float, list[str], list[str]]:
        """Phát hiện các mẫu mở đầu câu bị lặp nhiều."""
        findings: list[str] = []
        examples: list[str] = []

        openers_3 = []
        openers_2 = []
        for words in tokenized:
            if len(words) >= 3:
                openers_3.append(" ".join(w.lower() for w in words[:3]))
            if len(words) >= 2:
                openers_2.append(" ".join(w.lower() for w in words[:2]))

        total = len(tokenized)
        penalty = 0.0

        for openers, n in [(openers_3, 3), (openers_2, 2)]:
            c = Counter(openers)
            for pattern, count in c.most_common(5):
                ratio = count / total
                if ratio > _PATTERN_RATIO_THRESHOLD and count > 2:
                    penalty += ratio * 30
                    findings.append(
                        f'Mẫu mở đầu {n} từ "{pattern}" lặp {count} lần ({ratio:.1%})'
                    )
                    examples.append(
                        f'Pattern "{pattern}" × {count} câu'
                    )

        score = max(0.0, 100.0 - penalty)
        return round(score, 1), findings, examples

    def _consecutive_same_opener(
        self, tokenized: list[list[str]]
    ) -> tuple[float, list[str], list[str]]:
        """Phát hiện chuỗi câu liên tiếp có cùng mẫu mở đầu."""
        findings: list[str] = []
        examples: list[str] = []

        if not tokenized:
            return 100.0, [], []

        openers = []
        for words in tokenized:
            if words:
                openers.append(words[0].lower())  # chỉ từ đầu tiên
            else:
                openers.append("")

        max_consecutive = 1
        current_run = 1
        runs: list[tuple[str, int]] = []  # (pattern, length)

        for i in range(1, len(openers)):
            if openers[i] == openers[i - 1] and openers[i]:
                current_run += 1
            else:
                if current_run >= _CONSECUTIVE_THRESHOLD:
                    runs.append((openers[i - 1], current_run))
                max_consecutive = max(max_consecutive, current_run)
                current_run = 1

        if current_run >= _CONSECUTIVE_THRESHOLD:
            runs.append((openers[-1], current_run))
        max_consecutive = max(max_consecutive, current_run)

        penalty = 0.0
        for pattern, run_len in runs:
            penalty += run_len * 5
            findings.append(
                f'{run_len} câu liên tiếp bắt đầu bằng "{pattern}"'
            )
            examples.append(
                f'Chuỗi {run_len} câu liên tiếp: "{pattern} …"'
            )

        score = max(0.0, 100.0 - penalty)
        return round(score, 1), findings, examples
