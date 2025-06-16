# Use official Python slim image
FROM python:3.10-slim

# Install system deps for PDF parsing
RUN apt-get update && \
    apt-get install -y build-essential libssl-dev poppler-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependencies list and install
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project (ragflow.yaml, docs folder)
COPY . .

# Ensure the vector DB directory exists
RUN mkdir -p ./.ragflow_db

# Expose the port
EXPOSE 8000

# Start the RAG Flow server
CMD ["ragflow", "serve", "--host", "0.0.0.0", "--port", "8000"]
