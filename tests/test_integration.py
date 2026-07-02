"""Integration test — chạy full pipeline với sample chapter."""
from pathlib import Path
import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "sample_chapter.txt"


def test_full_pipeline():
    from taka_score.mcp_server import evaluate_vietnamese_style_technical

    text = FIXTURE.read_text(encoding="utf-8")
    result = evaluate_vietnamese_style_technical(text=text, mode="chapter", detail_level="medium")

    assert result["ok"] is True
    assert 0 <= result["overall_score"] <= 100
    assert result["grade"] in {"A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"}
    assert "scores" in result
    assert "strengths" in result
    assert "weaknesses" in result


def test_text_too_short():
    from taka_score.mcp_server import evaluate_vietnamese_style_technical

    result = evaluate_vietnamese_style_technical(text="Văn bản quá ngắn.", mode="chapter")
    assert result["ok"] is False
    assert result["code"] == "TEXT_TOO_SHORT"
