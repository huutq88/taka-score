"""Preprocessor — Chuẩn hóa văn bản tiếng Việt trước khi phân tích."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass
class PreprocessResult:
    original_text: str
    clean_text: str
    word_count: int          # ước tính bằng cách đếm khoảng trắng
    syllable_count: int      # trong tiếng Việt, âm tiết ≈ token khoảng trắng
    paragraph_count: int
    sentence_count_estimate: int  # ước tính sơ bộ trước splitter


# Dấu ngoặc kép các kiểu → chuẩn hóa về " "
_QUOTE_MAP = str.maketrans({
    "\u201c": '"', "\u201d": '"',  # " "
    "\u2018": "'", "\u2019": "'",  # ' '
    "\u00ab": '"', "\u00bb": '"',  # « »
    "\u2039": "'", "\u203a": "'",  # ‹ ›
})

# Ellipsis chuẩn hóa: ... → …
_ELLIPSIS_RE = re.compile(r'\.{2,}')

# Khoảng trắng dư
_WHITESPACE_RE = re.compile(r'[ \t]+')
_MULTI_NEWLINE_RE = re.compile(r'\n{3,}')

# Câu kết thúc bằng dấu câu (ước tính sơ bộ)
_SENTENCE_END_RE = re.compile(r'[.!?…]+')


def preprocess(text: str) -> PreprocessResult:
    """
    Chuẩn hóa văn bản tiếng Việt:
    - Unicode NFC normalization
    - Chuẩn hóa ngoặc kép
    - Chuẩn hóa ellipsis
    - Chuẩn hóa khoảng trắng
    - Thống kê cơ bản
    """
    original = text

    # 1. Unicode NFC — chuẩn hóa dấu tiếng Việt (combining → precomposed)
    text = unicodedata.normalize("NFC", text)

    # 2. Chuẩn hóa ngoặc kép
    text = text.translate(_QUOTE_MAP)

    # 3. Chuẩn hóa ellipsis
    text = _ELLIPSIS_RE.sub("…", text)

    # 4. Chuẩn hóa khoảng trắng trong dòng
    text = _WHITESPACE_RE.sub(" ", text)

    # 5. Bỏ khoảng trắng đầu/cuối từng dòng
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    # 6. Chuẩn hóa đoạn văn (không để quá 2 dòng trắng liên tiếp)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    text = text.strip()

    # Thống kê
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    syllable_count = len(text.split())          # âm tiết ≈ whitespace tokens
    word_count = syllable_count                 # placeholder trước khi có tokenizer
    sentence_count_est = len(_SENTENCE_END_RE.findall(text))

    return PreprocessResult(
        original_text=original,
        clean_text=text,
        word_count=word_count,
        syllable_count=syllable_count,
        paragraph_count=len(paragraphs),
        sentence_count_estimate=max(sentence_count_est, 1),
    )
