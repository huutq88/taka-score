FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml .
COPY taka_score/ taka_score/

# Install dependencies
RUN uv pip install --system -e .

# Download underthesea models
RUN python -c "from underthesea import word_tokenize; word_tokenize('test')"

EXPOSE 8002

CMD ["taka-score", "--http"]
