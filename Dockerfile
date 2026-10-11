# Part B: the agent harness as one container.
FROM python:3.11-slim

# pdftotext (poppler) is what the project's quote verifiers read the PDFs with.
RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./requirements.txt
COPY harness/requirements.txt ./harness/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r harness/requirements.txt
COPY . .

# Run folders live here; mount a volume at /data to keep them across deploys.
ENV HARNESS_RUNS_DIR=/data/runs \
    PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["sh", "-c", "uvicorn harness.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
