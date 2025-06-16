from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List
import zipfile, os, shutil
import fitz  # PyMuPDF
from docx import Document
import tempfile
import httpx

app = FastAPI()

# === Brave Search Wrapper ===
BRAVE_API_KEY = "your_brave_api_key_here"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

async def brave_search(query: str):
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": 5}
    async with httpx.AsyncClient() as client:
        resp = await client.get(BRAVE_SEARCH_URL, headers=headers, params=params)
        data = resp.json()
        return [item["title"] + " - " + item["url"] for item in data.get("web", {}).get("results", [])]

# === Document Loaders ===
def load_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def load_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def load_pdf(path):
    pdf = fitz.open(path)
    return "\n".join([page.get_text() for page in pdf])

def extract_texts_from_zip(zip_path):
    extract_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    docs = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            path = os.path.join(root, file)
            ext = os.path.splitext(file)[-1].lower()
            try:
                if ext in ['.txt', '.md']:
                    docs.append(load_txt(path))
                elif ext == '.docx':
                    docs.append(load_docx(path))
                elif ext == '.pdf':
                    docs.append(load_pdf(path))
            except Exception as e:
                print(f"Error loading {file}: {e}")
    shutil.rmtree(extract_dir)
    return docs

# === Mocked RAG Processor (replace with real RAGFlow later) ===
def run_rag(question: str, docs: List[str], web_results: List[str]):
    context = "\n".join(docs + web_results)
    return {
        "answer": f"Based on the documents and web, here's a response to: '{question}'",
        "sources": web_results
    }

# === API Endpoint ===
@app.post("/ask")
async def ask_question(question: str = Form(...), zip_file: UploadFile = Form(...), use_web_search: bool = Form(False)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            content = await zip_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        docs = extract_texts_from_zip(tmp_path)
        web_results = await brave_search(question) if use_web_search else []

        result = run_rag(question, docs, web_results)
        return JSONResponse(result)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
