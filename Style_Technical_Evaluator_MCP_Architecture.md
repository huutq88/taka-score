# Style Technical Evaluator MCP Architecture

## 1. Mục tiêu

MCP tool này dùng để đánh giá **kỹ thuật diễn đạt** của một chương truyện tiếng Việt.

**Không chấm:**
- Cốt truyện
- Nhân vật
- Cảm xúc
- Ý tưởng nghệ thuật

**Chỉ chấm:**
- Độ trôi chảy (Fluency)
- Độ tự nhiên (Naturalness - Ủy thác cho thothan.ai Agent)
- Độ lặp từ (Repetition)
- Độ lặp cấu trúc câu (Structure Pattern)
- Độ đa dạng từ vựng (Lexical Diversity)
- Nhịp câu (Sentence Rhythm)
- Độ dễ đọc (Readability - Tiêu chuẩn tiếng Việt)
- Sự liên kết (Cohesion)

---

## 2. Kiến trúc tổng thể

```text
Novel Chapter Text / chapter_id
        │
        ▼ (db.py / Postgres Fetcher)
Raw Chapter Text
        │
        ▼
Preprocessor (Unicode NFC & Normalization)
        │
        ▼
Sentence / Paragraph Splitter (Abbreviations & Dialogue)
        │
        ▼
Vietnamese Word Segmenter (underthesea)
        │
        ├───────────────────────────────────────────────────────┐
        ▼ (Rule-based Analyzers)                                ▼ (Suspicious Extract)
Technical Analyzers                                     Suspicious Sentences
  ├── Repetition Analyzer (15-word window & n-gram)        (Câu quá dài, sượng,
  ├── Lexical Diversity Analyzer (MATTR & CTTR)            lặp cấu trúc câu)
  ├── Sentence Rhythm Analyzer (CV distribution)                │
  ├── Readability Analyzer (Comma & syllable density)           │
  └── Cohesion Analyzer (Connectors & references)                │
        │                                                       │
        ▼                                                       ▼
Score Aggregator                                     EvaluateResponse JSON
        │                                                       │
        └──────────────────────────┬────────────────────────────┘
                                   ▼
                            MCP Response JSON
                                   │
                                   ▼ (SSE / HTTP)
                       [ thothan.ai / LobeChat ]
                                   │
                                   ▼ (AI Agent LLM)
                    1. Đọc list suspicious_sentences
                    2. Đánh giá Naturalness (Độ tự nhiên)
                    3. Gợi ý sửa đổi & Render Markdown Report
```

---

## 3. Thành phần hệ thống

### 3.1 Preprocessor
- Chuẩn hóa Unicode NFC (combining $\rightarrow$ precomposed).
- Chuẩn hóa dấu câu, ngoặc kép (`"`, `«`, `»` $\rightarrow$ `"`).
- Chuẩn hóa khoảng trắng và dòng trống.
- Thống kê sơ bộ từ, âm tiết, đoạn văn.

### 3.2 Sentence / Paragraph Splitter
- Tách đoạn văn qua dòng trống.
- Tách câu tiếng Việt thông minh, xử lý các từ viết tắt phổ biến (TP., PGS.TS., GS...) để tránh chia cắt câu sai.
- Tách riêng biệt lời thoại (dấu gạch ngang `—` đầu dòng) để tránh phạt điểm phong cách khẩu ngữ.

### 3.3 Vietnamese Word Segmenter (underthesea)
- Thực hiện tách từ tiếng Việt để đảm bảo các phép đo lặp từ (repetition) và đa dạng từ vựng (TTR) hoạt động chính xác trên đơn vị "từ" thay vì "âm tiết".
- Sử dụng cache (LRU cache) để tối ưu hiệu năng đối với văn bản dài.

---

## 4. Technical Analyzers

### Repetition Analyzer
- **Word Repetition:** Sử dụng sliding window 15 từ để phát hiện lặp lại từ dày đặc.
- **N-gram Repetition:** Phát hiện lặp cụm từ (bigram, trigram) qua tỷ lệ extra repeats.
- **Sentence Opener:** Phát hiện lặp mẫu mở đầu câu (2 từ đầu).

### Lexical Diversity Analyzer
- Sử dụng **MATTR** (Moving Average Type-Token Ratio) với window 100 từ để chấm điểm sự phong phú của từ vựng mà không bị ảnh hưởng bởi độ dài chương truyện.
- Kết hợp công thức **CTTR** (Corrected Type-Token Ratio).

### Sentence Rhythm Analyzer
- Đo độ biến thiên nhịp câu qua hệ số CV (Coefficient of Variation) của độ dài câu.
- Đánh giá phân bố câu ngắn ($\le7$ từ), vừa, dài, câu quá dài ($>40$ từ).

### Readability Analyzer
- Phép đo được tùy chỉnh hoàn toàn cho tiếng Việt:
  - Mật độ dấu phẩy trong câu.
  - Mật độ mệnh đề phụ (connector keywords).
  - Mật độ câu trong đoạn (tránh đoạn văn quá dày đặc).
  - Nhận diện câu gây vấp ($>30$ âm tiết).

### Cohesion Analyzer
- Đo mật độ từ nối liên kết thông qua từ điển `connectors_vi.txt`.
- Đo mật độ đại từ tham chiếu chuẩn (dùng regex word-boundary).
- Đánh giá chất lượng chuyển tiếp giữa các đoạn văn.

---

## 5. Security & DB Persistence Layer

### Database Layer (`db.py`)
- **Neo4j Graph DB:** Lấy `document_id`, `story_title`, `title` từ node Chapter. Sau khi có điểm, tự động cập nhật `style_score`, `style_grade` và thời gian đánh giá lên node Chapter.
- **Postgres DB:** Lấy trực tiếp văn bản thô của chương từ bảng `agent_documents` thông qua `document_id`.

### Security API (`api_server.py`)
- MCP chạy trên cổng HTTP/SSE mặc định là `8002`.
- Bảo mật bằng middleware `MCPAuthMiddleware` yêu cầu token `Authorization: Bearer <API_KEY>` trong Header để chống spam trên Production.

---

## 6. MCP Specification

### Tools

#### 1. `evaluate_vietnamese_style_technical`
Chấm điểm trực tiếp từ văn bản thô truyền vào.

* **Input JSON:**
```json
{
  "text": "Nội dung chương truyện...",
  "mode": "chapter",
  "detail_level": "medium",
  "include_examples": true
}
```

* **Output JSON:**
```json
{
  "ok": true,
  "overall_score": 84.9,
  "grade": "B",
  "scores": {
    "fluency": 96.0,
    "repetition": 84.0,
    "lexical_diversity": 80.0,
    "sentence_rhythm": 78.0,
    "readability": 86.2,
    "structure_pattern": 50.0,
    "cohesion": 80.0
  },
  "summary": "...",
  "strengths": ["Độ trôi chảy (96/100)"],
  "weaknesses": ["Đa dạng cấu trúc (50/100)"],
  "technical_findings": [
    {
      "analyzer": "readability",
      "message": "Mật độ dấu phẩy cao (6.0 phẩy/câu)...",
      "severity": "warning"
    }
  ],
  "suspicious_sentences": [
    {
      "text": "Anh đi học, mang theo sách, mang theo vở...",
      "reason": "Câu có mật độ dấu phẩy cao (có thể quá phức tạp)"
    }
  ],
  "examples": [],
  "meta": {
    "word_count": 2781,
    "sentence_count": 485,
    "paragraph_count": 12,
    "dialogue_ratio": 0.15,
    "mode": "chapter"
  }
}
```

#### 2. `evaluate_chapter_by_id`
Chấm điểm trực tiếp bằng `chapter_id` từ database (Neo4j/Postgres).

* **Input JSON:**
```json
{
  "chapter_id": "chap_01",
  "detail_level": "medium",
  "include_examples": true
}
```
* **Output JSON:** Tương tự như trên, tự động bổ sung metadata chương và ghi kết quả style score ngược lại Neo4j.
