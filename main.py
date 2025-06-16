from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List
import zipfile, os, shutil, tempfile
import fitz  # PyMuPDF
from docx import Document
import httpx
from ragflow import RAGFlow

app = FastAPI()

# === Initialize RAGFlow (with local docs + Brave Search) ===
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
rag = RAGFlow(
    retriever_configs=[
        {"type": "local_docs"},
        {"type": "web", "provider": "custom", "retriever_fn": None}  # we’ll inject Brave below
    ]
)

async def brave_search(query: str) -> List[str]:
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": 5}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
    results = []
    for item in data.get("web", {}).get("results", []):
        snippet = item.get("snippet") or ""
        link = item.get("url") or ""
        results.append(f"{snippet} ({link})")
    return results

# === Document loaders ===
def load_txt(path): 
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def load_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def load_pdf(path):
    pdf = fitz.open(path)
    return "\n".join(page.get_text() for page in pdf)

def extract_docs(zip_path):
    tmpdir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(tmpdir)
    docs = []
    for root, _, files in os.walk(tmpdir):
        for fn in files:
            full = os.path.join(root, fn)
            ext = os.path.splitext(fn)[1].lower()
            try:
                if ext in (".txt", ".md"):
                    docs.append(load_txt(full))
                elif ext == ".docx":
                    docs.append(load_docx(full))
                elif ext == ".pdf":
                    docs.append(load_pdf(full))
            except:
                pass
    shutil.rmtree(tmpdir)
    return docs

@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    zip_file: UploadFile = Form(...),
    use_web_search: bool = Form(False)
):
    # save upload to temp
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    data = await zip_file.read()
    tmp.write(data)
    tmp.flush()
    docs = extract_docs(tmp.name)
    # web results if flagged
    web_results = await brave_search(question) if use_web_search else []
    # inject custom retriever function if needed
    if use_web_search:
        rag.retriever_configs[1]["retriever_fn"] = lambda q: brave_search(q)
    # run RAGFlow
    res = rag.run(question=question, documents=docs, use_web_search=use_web_search)
    return JSONResponse({"answer": res.answer, "citations": res.citations})

