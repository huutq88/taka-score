"""TAKA Score — MCP server chính.

Cung cấp tool `evaluate_vietnamese_style_technical` qua MCP protocol.
"""
from __future__ import annotations

import os
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP

from taka_score.preprocessor import preprocess
from taka_score.splitter import split_text
from taka_score.tokenizer import tokenize_sentences
from taka_score.dialogue_detector import detect_dialogue
from taka_score.analyzers.repetition import RepetitionAnalyzer
from taka_score.analyzers.lexical_diversity import LexicalDiversityAnalyzer
from taka_score.analyzers.sentence_rhythm import SentenceRhythmAnalyzer
from taka_score.analyzers.readability import ReadabilityAnalyzer
from taka_score.analyzers.structure_pattern import StructurePatternAnalyzer
from taka_score.analyzers.cohesion import CohesionAnalyzer
from taka_score.scorer import ScoreAggregator
from taka_score.report_generator import generate_report
from taka_score.schemas.request import EvaluateRequest, MIN_WORDS, MAX_WORDS

# ──────────────────────────────────────────────────────────────
# Server definition
# ──────────────────────────────────────────────────────────────

mcp = FastMCP(
    "taka-score",
    instructions=(
        "TAKA Score là công cụ đánh giá kỹ thuật viết văn tiếng Việt (Rule-based).\n\n"
        "HƯỚNG DẪN CHO AGENT (LobeChat/thothan.ai):\n"
        "1. Khi nhận văn bản từ user, gọi tool `evaluate_vietnamese_style_technical` để lấy điểm kỹ thuật.\n"
        "2. Đọc danh sách câu nghi vấn trong `suspicious_sentences` từ kết quả trả về của tool.\n"
        "3. Sử dụng trí thông minh của bạn (LLM) để đánh giá ĐỘ TỰ NHIÊN (Naturalness) của các câu này (chấm điểm sượng, hành văn lủng củng, dịch thuật hóa).\n"
        "4. Hãy tự chấm điểm 'Độ tự nhiên (Naturalness)' cho toàn bộ chương truyện (từ 0-100) và đưa điểm này vào bảng điểm cuối cùng.\n"
        "5. Trình bày báo cáo Markdown đẹp mắt gồm: Bảng điểm tổng hợp (kèm điểm Naturalness bạn vừa tự chấm), điểm mạnh/yếu, và gợi ý viết lại cụ thể cho từng câu nghi vấn."
    ),
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8002")),
)

# Khởi tạo analyzers (singleton)
_analyzers = {
    "repetition": RepetitionAnalyzer(),
    "lexical_diversity": LexicalDiversityAnalyzer(),
    "sentence_rhythm": SentenceRhythmAnalyzer(),
    "readability": ReadabilityAnalyzer(),
    "structure_pattern": StructurePatternAnalyzer(),
    "cohesion": CohesionAnalyzer(),
}

_aggregator = ScoreAggregator()


def create_app():
    """Factory cho uvicorn khi chạy HTTP transport."""
    return mcp.sse_app()


# ──────────────────────────────────────────────────────────────
# Tool
# ──────────────────────────────────────────────────────────────

@mcp.tool()
def evaluate_vietnamese_style_technical(
    text: Annotated[str, "Văn bản tiếng Việt cần đánh giá (chương truyện, đoạn văn...). Tối thiểu 100 âm tiết."],
    mode: Annotated[str, "Chế độ: 'chapter' (chương truyện), 'paragraph' (đoạn văn), 'excerpt' (trích đoạn). Mặc định: 'chapter'"] = "chapter",
    detail_level: Annotated[str, "Mức chi tiết báo cáo: 'low', 'medium', 'high'. Mặc định: 'medium'"] = "medium",
    include_examples: Annotated[bool, "Có kèm ví dụ cụ thể không. Mặc định: True"] = True,
) -> dict[str, Any]:
    """
    Đánh giá kỹ thuật diễn đạt của văn bản tiếng Việt.

    Chỉ đánh giá các yếu tố kỹ thuật:
    - Lặp từ và lặp cấu trúc câu
    - Độ đa dạng từ vựng (MATTR)
    - Nhịp câu (phân bố độ dài câu)
    - Độ dễ đọc (metrics tiếng Việt)
    - Mẫu cấu trúc câu
    - Liên kết văn bản

    KHÔNG đánh giá cốt truyện, nhân vật, cảm xúc hay giá trị nghệ thuật.
    """
    # ── 1. Validate input ────────────────────────────────────────
    word_count_estimate = len(text.split())
    if word_count_estimate < MIN_WORDS:
        return {
            "ok": False,
            "error": f"Văn bản quá ngắn ({word_count_estimate} âm tiết). Cần tối thiểu {MIN_WORDS} âm tiết.",
            "code": "TEXT_TOO_SHORT",
        }
    if word_count_estimate > MAX_WORDS:
        return {
            "ok": False,
            "error": f"Văn bản quá dài ({word_count_estimate} âm tiết). Tối đa {MAX_WORDS} âm tiết.",
            "code": "TEXT_TOO_LONG",
        }

    try:
        # ── 2. Preprocess ────────────────────────────────────────
        prep = preprocess(text)

        # ── 3. Split ─────────────────────────────────────────────
        split = split_text(prep.clean_text)

        if len(split.sentences) < 3:
            return {
                "ok": False,
                "error": "Không nhận diện được đủ câu để phân tích. Kiểm tra định dạng văn bản.",
                "code": "INVALID_INPUT",
            }

        # ── 4. Tokenize ──────────────────────────────────────────
        tokenized = tokenize_sentences(split.sentences)

        # ── 5. Dialogue detection ─────────────────────────────────
        dialogue = detect_dialogue(split.sentences)

        # Chỉ analyze narration sentences nếu có đủ
        if len(dialogue.narration_sentences) >= 5:
            narration_tokenized = tokenize_sentences(dialogue.narration_sentences)
            analysis_sentences = dialogue.narration_sentences
            analysis_tokenized = narration_tokenized
        else:
            analysis_sentences = split.sentences
            analysis_tokenized = tokenized

        # ── 6. Run analyzers ──────────────────────────────────────
        analyzer_results = {}
        for name, analyzer in _analyzers.items():
            try:
                analyzer_results[name] = analyzer.analyze(
                    sentences=analysis_sentences,
                    tokenized=analysis_tokenized,
                    paragraphs=split.paragraphs,
                )
            except Exception as e:
                # Không để 1 analyzer fail làm hỏng toàn bộ
                from taka_score.analyzers import AnalyzerResult
                analyzer_results[name] = AnalyzerResult(
                    score=75.0,
                    findings=[f"Analyzer lỗi: {str(e)}"],
                )

        # ── 7. Aggregate scores ───────────────────────────────────
        overall_score, grade, breakdown = _aggregator.aggregate(analyzer_results)

        # ── 8. Generate report ────────────────────────────────────
        meta = {
            "word_count": prep.word_count,
            "syllable_count": prep.syllable_count,
            "sentence_count": len(split.sentences),
            "paragraph_count": prep.paragraph_count,
            "dialogue_ratio": dialogue.dialogue_ratio,
            "mode": mode,
        }

        report = generate_report(
            overall_score=overall_score,
            grade=grade,
            breakdown=breakdown,
            analyzer_results=analyzer_results,
            meta=meta,
            detail_level=detail_level,
            include_examples=include_examples,
        )

        return report.model_dump()

    except Exception as e:
        return {
            "ok": False,
            "error": f"Lỗi nội bộ: {str(e)}",
            "code": "INTERNAL_ERROR",
        }
