# Ollama RAG Flask – Agentic PDF Q&A

Local, private, and fast question-answering over your PDFs using a Retrieval-Augmented Generation (RAG) pipeline with an agentic multi-step planner. Backend runs on Flask with [Ollama](https://ollama.com) models, embeddings stored in ChromaDB. Frontend is a clean single-page UI with model/temperature/top-k controls and drag-and-drop PDF ingestion.

## Features
- ⚡ Local LLMs via Ollama (`llama3.1`, `qwen2`, etc.)
- 🔎 RAG with ChromaDB persistent vector store
- 🧠 Agentic planning: auto-generates sub-questions and synthesizes final answer
- 📎 Source citations with page numbers
- 🖥️ Frontend controls: model picker, temperature slider, top-k, system prompt
- 📄 Multi-PDF ingestion

## Quickstart
### 0) Prereqs
- Python 3.10+
- Ollama installed and running: https://ollama.com/download
- Pull a chat model and an embedding model:
  ```bash
  ollama pull llama3.1
  ollama pull nomic-embed-text
  ```

### 1) Create and activate venv, install deps
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Run the server
```bash
export OLLAMA_BASE_URL=http://localhost:11434  # set if your Ollama is non-default
python app.py
```
Visit http://127.0.0.1:5000

### 3) Ingest PDFs
Use the UI drag-and-drop (top bar) or `curl`:
```bash
curl -F "files=@/path/to/file1.pdf" -F "files=@/path/to/file2.pdf" http://127.0.0.1:5000/api/ingest
```

### 4) Ask questions
Use the UI. The API is also available:
```bash
curl -X POST http://127.0.0.1:5000/api/ask   -H 'Content-Type: application/json'   -d '{"question":"What are the main findings?","model":"llama3.1","temperature":0.2,"top_k":6,"system":"You are a helpful research assistant."}'
```

## Project structure
```
.
├── app.py                # Flask server & API
├── rag.py                # RAG pipeline (ingest, retrieve, agent plan, synthesize)
├── requirements.txt
├── static/
│   └── app.js            # Frontend logic
├── templates/
│   └── index.html        # Frontend UI (Tailwind + vanilla JS)
└── vectorstore/          # ChromaDB persistence (auto-created)
```

## Notes
- Default embedding model: `nomic-embed-text` via Ollama.
- You can change defaults via env or query params. See `app.py` for options.
- For large PDFs, first run may take a while to embed; subsequent queries are fast.
