"""Readability Analyzer — Đo độ dễ đọc của văn bản tiếng Việt.

Dùng các metrics phù hợp với tiếng Việt thay vì công thức phương Tây
(Flesch-Kincaid không áp dụng được cho tiếng Việt).
"""
from __future__ import annotations

import re
import statistics

from taka_score.analyzers import BaseAnalyzer, AnalyzerResult

# Ngưỡng mật độ dấu phẩy (phẩy / câu)
_COMMA_HIGH = 2.5    # > 2.5 phẩy/câu → phức tạp
_COMMA_OK = 1.5

# Ngưỡng mật độ mệnh đề phụ (từ kết nối phụ / câu)
_SUBCLAUSE_RE = re.compile(
    r'\b(mặc dù|tuy nhiên|bởi vì|vì|do|khi|nếu|mà|để|nhưng|'
    r'dù|dẫu|hễ|miễn là|với điều kiện|chỉ cần|trừ khi|'
    r'sau khi|trước khi|trong khi|ngay khi)\b',
    re.IGNORECASE | re.UNICODE,
)

# Câu quá dài (từ): xem sentence_rhythm — ở đây tập trung vào mệnh đề
_MAX_COMFORTABLE_SYLLABLES = 30   # âm tiết/câu

# Ngưỡng paragraph density (câu/đoạn)
_PARA_DENSE_THRESHOLD = 8   # > 8 câu/đoạn → đoạn dày đặc


class ReadabilityAnalyzer(BaseAnalyzer):

    @property
    def name(self) -> str:
        return "readability"

    def analyze(
        self,
        sentences: list[str],
        tokenized: list[list[str]],
        paragraphs: list[str],
    ) -> AnalyzerResult:
        if not sentences:
            return AnalyzerResult(score=50.0)

        # 1. Mật độ dấu phẩy
        comma_score, comma_findings, comma_examples = self._comma_density(sentences)

        # 2. Mật độ mệnh đề phụ
        subclause_score, sub_findings, sub_examples = self._subclause_density(sentences)

        # 3. Mật độ đoạn văn
        para_score, para_findings, para_examples = self._paragraph_density(
            paragraphs, sentences
        )

        # 4. Câu gây vấp (syllable quá dài)
        hard_score, hard_findings, hard_examples = self._hard_sentences(sentences)

        overall = (
            comma_score * 0.40
            + subclause_score * 0.30
            + para_score * 0.15
            + hard_score * 0.15
        )

        # Trích xuất các câu nghi vấn cho LobeChat
        suspicious = []
        for s in sentences:
            s_clean = s.strip()
            # Câu nhiều phẩy
            if s.count(",") >= 3:
                suspicious.append({"text": s_clean, "reason": "Câu có mật độ dấu phẩy cao (có thể quá phức tạp)"})
            # Câu quá dài
            elif len(s.split()) > _MAX_COMFORTABLE_SYLLABLES:
                suspicious.append({"text": s_clean, "reason": f"Câu quá dài ({len(s.split())} âm tiết), dễ gây vấp khi đọc"})

        return AnalyzerResult(
            score=round(overall, 1),
            findings=comma_findings + sub_findings + para_findings + hard_findings,
            examples=(comma_examples + sub_examples + para_examples + hard_examples)[:8],
            raw_metrics={
                "comma_score": comma_score,
                "subclause_score": subclause_score,
                "para_density_score": para_score,
                "hard_sentence_score": hard_score,
                "suspicious_sentences": suspicious[:5],  # giới hạn max 5 câu nổi bật nhất
            },
        )

    def _comma_density(
        self, sentences: list[str]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []
        densities = []

        for sent in sentences:
            comma_count = sent.count(",") + sent.count("，")
            densities.append(comma_count)

        if not densities:
            return 100.0, [], []

        avg = statistics.mean(densities)

        if avg > _COMMA_HIGH:
            score = max(30.0, 100.0 - (avg - _COMMA_OK) * 20)
            findings.append(
                f"Mật độ dấu phẩy cao ({avg:.1f} phẩy/câu). "
                "Nhiều câu phức với quá nhiều mệnh đề."
            )
            # Ví dụ câu nhiều phẩy nhất
            worst = max(sentences, key=lambda s: s.count(","))
            examples.append(f'Câu nhiều phẩy nhất: "{worst[:80]}…"')
        elif avg > _COMMA_OK:
            score = 80.0
        else:
            score = 100.0

        return round(score, 1), findings, examples

    def _subclause_density(
        self, sentences: list[str]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []
        ratios = []

        for sent in sentences:
            matches = _SUBCLAUSE_RE.findall(sent)
            # Số từ nối phụ / độ dài câu (âm tiết)
            syllables = len(sent.split())
            ratio = len(matches) / max(syllables, 1)
            ratios.append(ratio)

        if not ratios:
            return 100.0, [], []

        avg = statistics.mean(ratios)
        heavy_count = sum(1 for r in ratios if r > 0.15)

        if heavy_count > len(ratios) * 0.25:
            score = max(50.0, 100.0 - heavy_count * 3)
            findings.append(
                f"{heavy_count} câu có mật độ mệnh đề phụ cao "
                f"({heavy_count/len(ratios):.1%} tổng câu)."
            )
        else:
            score = 100.0

        return round(score, 1), findings, examples

    def _paragraph_density(
        self, paragraphs: list[str], sentences: list[str]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []

        if not paragraphs:
            return 100.0, [], []

        # Đếm số câu per đoạn (ước tính bằng dấu câu)
        sent_counts = []
        for para in paragraphs:
            count = len(re.findall(r'[.!?…]+', para))
            sent_counts.append(max(count, 1))

        avg = statistics.mean(sent_counts)
        heavy_paras = sum(1 for c in sent_counts if c > _PARA_DENSE_THRESHOLD)

        if heavy_paras > len(paragraphs) * 0.3:
            score = max(60.0, 100.0 - heavy_paras * 5)
            findings.append(
                f"{heavy_paras} đoạn văn dày đặc (>{_PARA_DENSE_THRESHOLD} câu/đoạn). "
                "Cân nhắc xuống dòng thêm để dễ đọc."
            )
        else:
            score = 100.0

        return round(score, 1), findings, examples

    def _hard_sentences(
        self, sentences: list[str]
    ) -> tuple[float, list[str], list[str]]:
        findings: list[str] = []
        examples: list[str] = []

        hard = [s for s in sentences if len(s.split()) > _MAX_COMFORTABLE_SYLLABLES]
        ratio = len(hard) / max(len(sentences), 1)

        if ratio > 0.2:
            score = max(50.0, 100.0 - ratio * 100)
            findings.append(
                f"{len(hard)} câu gây vấp (>{_MAX_COMFORTABLE_SYLLABLES} âm tiết), "
                f"chiếm {ratio:.1%}."
            )
            for s in hard[:3]:
                examples.append(f'Câu dài: "{s[:90]}…"')
        else:
            score = 100.0

        return round(score, 1), findings, examples
