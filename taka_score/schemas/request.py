"""Request schema cho MCP tool evaluate_vietnamese_style_technical."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator

MIN_WORDS = 100
MAX_WORDS = 50_000


class EvaluateRequest(BaseModel):
    text: str = Field(..., description="Văn bản tiếng Việt cần đánh giá")
    mode: Literal["chapter", "paragraph", "excerpt"] = Field(
        default="chapter",
        description="Chế độ đánh giá: chapter (chương truyện), paragraph (đoạn văn), excerpt (trích đoạn)",
    )
    detail_level: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Mức độ chi tiết của báo cáo",
    )
    include_examples: bool = Field(
        default=True,
        description="Có bao gồm ví dụ cụ thể từ văn bản không",
    )
    include_rewrite_suggestions: bool = Field(
        default=False,
        description="Có gợi ý chỉnh sửa không (Phase 3 — hiện chưa khả dụng)",
    )

    @field_validator("text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        word_count = len(v.split())
        if word_count < MIN_WORDS:
            raise ValueError(
                f"Văn bản quá ngắn ({word_count} âm tiết). "
                f"Cần tối thiểu {MIN_WORDS} âm tiết để đánh giá có ý nghĩa."
            )
        if word_count > MAX_WORDS:
            raise ValueError(
                f"Văn bản quá dài ({word_count} âm tiết). "
                f"Tối đa {MAX_WORDS} âm tiết."
            )
        return v
