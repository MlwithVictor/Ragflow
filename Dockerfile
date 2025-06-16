# Use official Python slim image
FROM python:3.10-slim

# Install system deps for PDF parsing and Git for pip install from GitHub
RUN apt-get update && \
    apt-get install -y build-essential libssl-dev poppler-utils git && \
    rm -rf /var/lib/apt/lists/*
