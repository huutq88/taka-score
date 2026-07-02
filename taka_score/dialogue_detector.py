"""Dialogue Detector — Tách lời thoại khỏi phần tường thuật.

Trong tiểu thuyết tiếng Việt, lời thoại thường được đánh dấu bằng:
- Dấu gạch ngang đầu dòng: — Anh ấy nói.
- Nội dung trong dấu ngoặc kép: "Anh ấy nói."

Lời thoại có style khác tường thuật nên cần đánh giá riêng.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class TextSegment:
    text: str
    kind: str   # "dialogue" | "narration"
    line_index: int


@dataclass
class DialogueResult:
    segments: list[TextSegment] = field(default_factory=list)
    narration_sentences: list[str] = field(default_factory=list)
    dialogue_sentences: list[str] = field(default_factory=list)
    dialogue_ratio: float = 0.0   # tỷ lệ lời thoại / tổng


# Gạch ngang đầu dòng (EM dash, EN dash, hoặc hyphen)
_DASH_DIALOGUE_RE = re.compile(r'^[—–-]\s*(.+)', re.UNICODE)

# Ngoặc kép bao quanh câu
_QUOTE_DIALOGUE_RE = re.compile(r'^"(.+)"$', re.UNICODE)


def detect_dialogue(sentences: list[str]) -> DialogueResult:
    """
    Phân loại từng câu là dialogue hay narration.
    """
    segments: list[TextSegment] = []
    narration: list[str] = []
    dialogue: list[str] = []

    for idx, sent in enumerate(sentences):
        s = sent.strip()
        if not s:
            continue

        is_dialogue = bool(
            _DASH_DIALOGUE_RE.match(s)
            or _QUOTE_DIALOGUE_RE.match(s)
        )

        kind = "dialogue" if is_dialogue else "narration"
        segments.append(TextSegment(text=s, kind=kind, line_index=idx))

        if is_dialogue:
            dialogue.append(s)
        else:
            narration.append(s)

    total = len(segments)
    ratio = len(dialogue) / total if total > 0 else 0.0

    return DialogueResult(
        segments=segments,
        narration_sentences=narration,
        dialogue_sentences=dialogue,
        dialogue_ratio=round(ratio, 3),
    )
