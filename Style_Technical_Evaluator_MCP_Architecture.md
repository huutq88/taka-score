# Style Technical Evaluator MCP

## 1. Mục tiêu

MCP tool này dùng để đánh giá **kỹ thuật diễn đạt** của một chương
truyện tiếng Việt.

**Không chấm:** - Cốt truyện - Nhân vật - Cảm xúc - Ý tưởng nghệ thuật

**Chỉ chấm:** - Độ trôi chảy - Độ tự nhiên - Độ lặp từ - Độ lặp cấu trúc
câu - Độ đa dạng từ vựng - Nhịp câu - Độ dễ đọc - Mức ổn định văn phong

------------------------------------------------------------------------

## 2. Kiến trúc tổng thể

``` text
Novel Chapter Text
        │
        ▼
Preprocessor
        │
        ▼
Sentence / Paragraph Splitter
        │
        ▼
Technical Analyzers
        │
        ├── Repetition Analyzer
        ├── Lexical Diversity Analyzer
        ├── Sentence Rhythm Analyzer
        ├── Readability Analyzer
        ├── Structure Pattern Analyzer
        ├── Cohesion Analyzer
        └── VietQuill Adapter
        │
        ▼
Score Aggregator
        │
        ▼
Report Generator
        │
        ▼
MCP Response JSON
```

------------------------------------------------------------------------

## 3. Module

### 3.1 Preprocessor

-   Chuẩn hóa dấu câu
-   Chuẩn hóa khoảng trắng
-   Giữ nguyên nội dung gốc
-   Thống kê số từ, số đoạn

### 3.2 Sentence / Paragraph Splitter

-   Tách đoạn
-   Tách câu
-   Tách mệnh đề (tùy chọn)

------------------------------------------------------------------------

## 4. Technical Analyzers

### Repetition Analyzer

Đánh giá:

-   Lặp từ
-   Lặp cụm từ
-   Lặp hình ảnh
-   Lặp cấu trúc mở đầu câu

------------------------------------------------------------------------

### Lexical Diversity Analyzer

Đo:

-   Type Token Ratio
-   Unique Word Ratio
-   Vocabulary Richness
-   Rare Word Ratio

------------------------------------------------------------------------

### Sentence Rhythm Analyzer

Đo:

-   Độ dài trung bình câu
-   Phân bố câu ngắn/vừa/dài
-   Độ biến thiên nhịp câu
-   Tỷ lệ câu quá dài

------------------------------------------------------------------------

### Readability Analyzer

Đánh giá:

-   Độ dễ đọc
-   Độ dày đoạn văn
-   Mật độ dấu phẩy
-   Mật độ mệnh đề phụ
-   Các câu gây vấp

------------------------------------------------------------------------

### Structure Pattern Analyzer

Phát hiện:

-   Lặp mẫu mở đầu câu
-   Lặp mẫu ngữ pháp
-   Lặp nhịp diễn đạt

------------------------------------------------------------------------

### Cohesion Analyzer

Đánh giá:

-   Liên kết giữa các câu
-   Từ nối
-   Đại từ tham chiếu
-   Chuyển đoạn

------------------------------------------------------------------------

### VietQuill Adapter

Vai trò:

-   Paraphrase Quality
-   Naturalness Estimation
-   Semantic Stability
-   Awkward Sentence Detection

> Lưu ý: VietQuill chỉ hỗ trợ đánh giá chất lượng diễn đạt, không đánh
> giá giá trị văn học.

------------------------------------------------------------------------

## 5. Score Aggregator

Các tiêu chí:

  Metric                Weight
  ------------------- --------
  Fluency                  20%
  Naturalness              15%
  Repetition               15%
  Lexical Diversity        15%
  Sentence Rhythm          15%
  Readability              10%
  Cohesion                 10%

------------------------------------------------------------------------

## 6. Report Generator

Sinh:

-   Tổng điểm
-   Điểm từng tiêu chí
-   Điểm mạnh
-   Điểm cần cải thiện
-   Ví dụ cụ thể
-   Gợi ý chỉnh sửa (nếu bật)

------------------------------------------------------------------------

## 7. MCP Tool

### Tool Name

``` text
evaluate_vietnamese_style_technical
```

### Input

``` json
{
  "text": "...",
  "mode": "chapter",
  "detail_level": "medium",
  "include_examples": true,
  "include_rewrite_suggestions": false
}
```

### Output

``` json
{
  "overall_score": 82,
  "grade": "A-",
  "scores": {
    "fluency": 86,
    "naturalness": 84,
    "repetition": 72,
    "lexical_diversity": 81,
    "sentence_rhythm": 82,
    "readability": 78,
    "cohesion": 85
  },
  "summary": "...",
  "strengths": [],
  "weaknesses": [],
  "technical_findings": [],
  "examples": []
}
```

------------------------------------------------------------------------

## 8. Cấu trúc dự án

``` text
style-tech-evaluator/
├── README.md
├── pyproject.toml
├── server.py
├── config.py
│
├── app/
│   ├── preprocessor.py
│   ├── splitter.py
│   ├── scorer.py
│   ├── report_generator.py
│   │
│   ├── analyzers/
│   │   ├── repetition.py
│   │   ├── lexical_diversity.py
│   │   ├── sentence_rhythm.py
│   │   ├── readability.py
│   │   ├── structure_pattern.py
│   │   └── cohesion.py
│   │
│   ├── adapters/
│   │   └── vietquill_adapter.py
│   │
│   └── schemas/
│       ├── request.py
│       └── response.py
│
├── tests/
└── examples/
```

------------------------------------------------------------------------

## 9. Roadmap

### Phase 1

-   Rule-based metrics
-   Không dùng LLM
-   Không dùng VietQuill

### Phase 2

-   Tích hợp VietQuill
-   Naturalness
-   Paraphrase Quality
-   Awkward Sentence Detection

### Phase 3

-   LLM chỉ để diễn giải báo cáo
-   Không tham gia tính điểm

------------------------------------------------------------------------

## 10. Định hướng

Ưu tiên:

1.  Rule-based Technical Metrics
2.  VietQuill
3.  LLM (tuỳ chọn)

Điểm số cuối cùng nên dựa trên các chỉ số khách quan thay vì đánh giá
chủ quan về giá trị văn học.
