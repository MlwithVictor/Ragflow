# Use official Python slim image
FROM python:3.10-slim

# Install system deps (for PDF parsing)
RUN apt-get update && \
    apt-get install -y build-essential libssl-dev poppler-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your repo (ragflow.yaml, docs folder, etc.)
COPY . .

# Ensure vector DB dir exists
RUN mkdir -p ./.ragflow_db

EXPOSE 8000

# Launch RAG Flow’s FastAPI server
CMD ["ragflow", "serve", "--host", "0.0.0.0", "--port", "8000"]
