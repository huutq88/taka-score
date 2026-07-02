"""Tests cho splitter module."""
import pytest
from taka_score.splitter import split_paragraphs, split_sentences, split_text


def test_split_paragraphs():
    text = "Đoạn một.\n\nĐoạn hai.\n\nĐoạn ba."
    paras = split_paragraphs(text)
    assert len(paras) == 3


def test_split_sentences_basic():
    text = "Anh đi học. Cô ấy ở nhà. Bố mẹ đi làm."
    sents = split_sentences(text)
    assert len(sents) == 3


def test_dialogue_lines_separated():
    text = "Anh nhìn cô ấy.\n— Cô có ổn không?\nCô gật đầu."
    sents = split_sentences(text)
    # Dòng gạch ngang phải là câu riêng
    assert any("—" in s for s in sents)


def test_split_text_full():
    text = "Đoạn một.\n\nAnh đi học. Cô ở nhà."
    result = split_text(text)
    assert len(result.paragraphs) == 2
    assert len(result.sentences) >= 2
    assert len(result.sentences_per_paragraph) == 2
