"""Tokenizer — Vietnamese word segmentation wrapper.

Dùng underthesea.word_tokenize để tách từ tiếng Việt.
Có cache đơn giản để tránh re-tokenize cùng đoạn text.
"""
from __future__ import annotations

import functools
import re
from typing import Callable

_tokenize_fn: Callable | None = None


def _get_tokenize_fn() -> Callable:
    """Lazy-load underthesea để không block startup."""
    global _tokenize_fn
    if _tokenize_fn is None:
        try:
            from underthesea import word_tokenize
            _tokenize_fn = word_tokenize
        except ImportError:
            # Fallback: tách bằng khoảng trắng (kém chính xác hơn)
            _tokenize_fn = lambda text: text.split()  # noqa: E731
    return _tokenize_fn


@functools.lru_cache(maxsize=512)
def tokenize(text: str) -> tuple[str, ...]:
    """
    Tách từ tiếng Việt. Trả về tuple để có thể cache.
    
    VD: "học sinh đi học" → ("học sinh", "đi", "học")
    """
    fn = _get_tokenize_fn()
    tokens = fn(text, format="text")
    # underthesea trả về string với _ nối các âm tiết của cùng 1 từ
    # VD: "học_sinh đi học" → split theo space
    words = tokens.split()
    # Bỏ dấu câu thuần túy
    words = [w for w in words if re.search(r'\w', w, re.UNICODE)]
    return tuple(words)


def tokenize_sentences(sentences: list[str]) -> list[list[str]]:
    """Tokenize danh sách câu, trả về list of list of words."""
    return [list(tokenize(sent)) for sent in sentences]


def count_words(text: str) -> int:
    """Đếm số từ (đã segment) trong text."""
    return len(tokenize(text))
