"""Analyzers package — base class cho tất cả technical analyzers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AnalyzerResult:
    score: float                          # 0–100
    findings: list[str] = field(default_factory=list)   # mô tả chi tiết
    examples: list[str] = field(default_factory=list)   # ví dụ cụ thể từ văn bản
    raw_metrics: dict = field(default_factory=dict)     # số liệu thô


class BaseAnalyzer(ABC):
    """Interface chung cho tất cả technical analyzers."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def analyze(
        self,
        sentences: list[str],
        tokenized: list[list[str]],
        paragraphs: list[str],
    ) -> AnalyzerResult: ...
