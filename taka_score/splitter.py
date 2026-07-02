"""Splitter — Tách đoạn và câu trong văn bản tiếng Việt.

Xử lý các edge cases:
- Viết tắt phổ biến tiếng Việt (TP., GS., PGS.TS., ...)
- Ellipsis (…) cuối câu
- Dấu chấm trong ngoặc kép
- Câu hỏi/cảm thán liên tiếp
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# ── Viết tắt tiếng Việt thường gặp (không tách câu sau dấu chấm này) ──────────
_ABBREVS = {
    "tp", "ths", "gs", "pgs", "ts", "bs", "ks", "kts",
    "th", "bv", "cty", "nxb", "tphcm", "hn",
    "vd", "vv", "vvv", "tt", "vs", "đ", "tr",
    # Thứ / tháng
    "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10", "t11", "t12",
    "cn", "th2", "th3", "th4", "th5", "th6", "th7",
    # La-tinh
    "st", "mr", "ms", "dr", "prof",
}

# Pattern nhận diện kết thúc câu (tách khi không phải viết tắt)
_SENTENCE_SPLIT_RE = re.compile(
    r'(?<=[^\s{abbr}])([.!?…]+)'      # dấu câu kết thúc
    r'(?!\s*["\u201d])'                # không theo sau bởi ngoặc kép đóng
    r'(?=\s+[A-ZĐÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ])',
    re.UNICODE,
)

# Pattern tách đoạn
_PARA_SPLIT_RE = re.compile(r'\n\s*\n')

# Nhận diện đầu dòng thoại (gạch ngang)
_DIALOGUE_LINE_RE = re.compile(r'^[—–-]\s')


@dataclass
class SplitResult:
    paragraphs: list[str] = field(default_factory=list)
    sentences: list[str] = field(default_factory=list)
    sentences_per_paragraph: list[list[str]] = field(default_factory=list)


def split_paragraphs(text: str) -> list[str]:
    """Tách đoạn văn bằng dòng trắng."""
    return [p.strip() for p in _PARA_SPLIT_RE.split(text) if p.strip()]


def split_sentences(text: str) -> list[str]:
    """
    Tách câu trong một đoạn, xử lý edge cases tiếng Việt.
    """
    # 1. Tách theo dòng (mỗi dòng gạch ngang đầu = 1 câu thoại)
    lines = text.splitlines()
    result_sentences: list[str] = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if _DIALOGUE_LINE_RE.match(line):
            # Lưu buffer trước (nếu có)
            if buffer.strip():
                result_sentences.extend(_split_by_punctuation(buffer.strip()))
                buffer = ""
            result_sentences.append(line)
        else:
            buffer = (buffer + " " + line).strip()

    if buffer.strip():
        result_sentences.extend(_split_by_punctuation(buffer.strip()))

    return [s for s in result_sentences if s.strip()]


def _split_by_punctuation(text: str) -> list[str]:
    """Tách câu theo dấu câu, bỏ qua viết tắt."""
    # Chia theo dấu chấm/hỏi/than/ellipsis đơn giản
    parts = re.split(r'([.!?…]+)', text)
    sentences: list[str] = []
    i = 0
    current = ""

    while i < len(parts):
        chunk = parts[i]
        if i + 1 < len(parts) and re.match(r'[.!?…]+', parts[i + 1]):
            punct = parts[i + 1]
            tentative = current + chunk + punct

            # Kiểm tra viết tắt
            word_before = chunk.rstrip().split()[-1].lower() if chunk.strip() else ""
            if word_before in _ABBREVS and punct == ".":
                current = tentative + " "
                i += 2
                continue

            sentences.append(tentative.strip())
            current = ""
            i += 2
        else:
            current += chunk
            i += 1

    if current.strip():
        sentences.append(current.strip())

    return [s for s in sentences if s.strip()]


def split_text(text: str) -> SplitResult:
    """Tách toàn bộ văn bản thành đoạn và câu."""
    paragraphs = split_paragraphs(text)
    all_sentences: list[str] = []
    sentences_per_para: list[list[str]] = []

    for para in paragraphs:
        para_sents = split_sentences(para)
        sentences_per_para.append(para_sents)
        all_sentences.extend(para_sents)

    return SplitResult(
        paragraphs=paragraphs,
        sentences=all_sentences,
        sentences_per_paragraph=sentences_per_para,
    )
