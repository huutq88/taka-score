"""Cohesion Analyzer — Đánh giá sự liên kết giữa các câu và đoạn văn.

Sử dụng bộ từ điển từ nối tiếng Việt trong resources/connectors_vi.txt.
"""
from __future__ import annotations

import re
from importlib import resources as pkg_resources
from pathlib import Path

from taka_score.analyzers import BaseAnalyzer, AnalyzerResult

# Tỷ lệ câu có từ nối "tốt" tối thiểu
_CONNECTOR_RATIO_GOOD = 0.25
_CONNECTOR_RATIO_OK = 0.12

# Đại từ tham chiếu phổ biến tiếng Việt (dùng whole-word matching)
_REFERENCE_WORDS = [
    "anh ấy", "cô ấy", "họ", "nó", "chúng", "hắn", 
    "bà ấy", "ông ấy", "cậu ấy", "cô ta", "hắn ta",
    "điều đó", "điều này", "việc đó", "việc này",
    "đó", "này", "kia", "ấy", "vậy",
]
# Pre-compile regex cho reference words (whole word match)
_REFERENCE_RE = re.compile(
    r'\b(' + '|'.join(re.escape(w) for w in _REFERENCE_WORDS) + r')\b',
    re.IGNORECASE | re.UNICODE,
)

_RESOURCES_DIR = Path(__file__).parent.parent / "resources"


def _load_connectors() -> set[str]:
    path = _RESOURCES_DIR / "connectors_vi.txt"
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
        return {line.strip().lower() for line in lines if line.strip() and not line.startswith("#")}
    return set()


_CONNECTORS: set[str] = _load_connectors()


class CohesionAnalyzer(BaseAnalyzer):

    @property
    def name(self) -> str:
        return "cohesion"

    def analyze(
        self,
        sentences: list[str],
        tokenized: list[list[str]],
        paragraphs: list[str],
    ) -> AnalyzerResult:
        if not sentences:
            return AnalyzerResult(score=50.0)

        connector_score, conn_findings, conn_examples = self._connector_density(sentences)
        reference_score, ref_findings, ref_examples = self._reference_density(sentences)
        transition_score, trans_findings, _ = self._paragraph_transitions(paragraphs)

        # Khi chỉ có 1 đoạn, transition không đánh giá được → dồn weight vào connector
        if len(paragraphs) < 2:
            overall = connector_score * 0.70 + reference_score * 0.30
        else:
            overall = (
                connector_score * 0.50
                + reference_score * 0.20
                + transition_score * 0.30
            )

        return AnalyzerResult(
            score=round(overall, 1),
            findings=conn_findings + ref_findings + trans_findings,
            examples=(conn_examples + ref_examples)[:6],
            raw_metrics={
                "connector_score": connector_score,
                "reference_score": reference_score,
                "transition_score": transition_score,
            },
        )

    def _connector_density(
        self, sentences: list[str]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []

        connected = 0
        for sent in sentences:
            sent_lower = sent.lower()
            if any(conn in sent_lower for conn in _CONNECTORS):
                connected += 1

        ratio = connected / max(len(sentences), 1)

        if ratio >= _CONNECTOR_RATIO_GOOD:
            score = 100.0
            findings.append(f"Sử dụng tốt từ nối ({ratio:.1%} câu có từ nối).")
        elif ratio >= _CONNECTOR_RATIO_OK:
            score = 75.0
            findings.append(f"Từ nối ở mức trung bình ({ratio:.1%} câu có từ nối).")
        else:
            score = max(40.0, ratio / _CONNECTOR_RATIO_OK * 75.0)
            findings.append(
                f"Thiếu từ nối ({ratio:.1%} câu có từ nối). "
                "Các câu có thể cảm giác rời rạc, thiếu liên kết."
            )

        return round(score, 1), findings, examples

    def _reference_density(
        self, sentences: list[str]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []

        ref_count = 0
        for sent in sentences:
            if _REFERENCE_RE.search(sent):
                ref_count += 1

        ratio = ref_count / max(len(sentences), 1)

        # Một mức độ tham chiếu vừa phải là tốt
        if 0.08 <= ratio <= 0.5:
            score = 100.0
        elif ratio < 0.08:
            score = 70.0
            findings.append("Ít đại từ tham chiếu — các câu có thể lặp tên nhân vật.")
        else:
            score = 75.0  # quá nhiều tham chiếu → có thể mơ hồ

        return round(score, 1), findings, examples

    def _paragraph_transitions(
        self, paragraphs: list[str]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        if len(paragraphs) < 2:
            return 100.0, [], []  # không đánh giá khi chỉ có 1 đoạn

        transitions = 0
        for para in paragraphs[1:]:  # bỏ qua đoạn đầu tiên
            first_sent = para.split(".")[0].lower()
            if any(conn in first_sent for conn in _CONNECTORS):
                transitions += 1

        ratio = transitions / max(len(paragraphs) - 1, 1)
        if ratio >= 0.3:
            score = 100.0
        elif ratio >= 0.15:
            score = 75.0
        else:
            score = 55.0
            findings.append(
                f"Chuyển đoạn thiếu từ nối ({ratio:.1%} đoạn có từ nối chuyển tiếp)."
            )

        return round(score, 1), findings, []
