"""Tests cho preprocessor module."""
import unicodedata
import pytest
from taka_score.preprocessor import preprocess


def test_unicode_normalization():
    # Chuỗi với combining characters (NFD) → NFC
    nfd = unicodedata.normalize("NFD", "tiếng Việt")
    nfc = unicodedata.normalize("NFC", "tiếng Việt")
    result = preprocess(nfd)
    assert result.clean_text == nfc


def test_quote_normalization():
    text = "\u201cXin chào\u201d anh nói."
    result = preprocess(text)
    assert "\u201c" not in result.clean_text
    assert "\u201d" not in result.clean_text
    assert '"Xin chào"' in result.clean_text


def test_ellipsis_normalization():
    text = "Anh nhìn ra xa... rồi thở dài."
    result = preprocess(text)
    assert "..." not in result.clean_text
    assert "…" in result.clean_text


def test_whitespace_cleanup():
    text = "Anh  đi   học."
    result = preprocess(text)
    assert "  " not in result.clean_text


def test_paragraph_count():
    text = "Đoạn một.\n\nĐoạn hai.\n\nĐoạn ba."
    result = preprocess(text)
    assert result.paragraph_count == 3


def test_word_count():
    text = "Anh đi học mỗi ngày."
    result = preprocess(text)
    assert result.word_count == 5


def test_preserves_content():
    text = "Nội dung gốc phải được giữ nguyên."
    result = preprocess(text)
    assert "Nội dung gốc phải được giữ nguyên" in result.clean_text
