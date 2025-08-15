import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import requests

# ---- App setup ----
app = Flask(__name__, static_folder="static", template_folder="templates")

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---- Ollama API ----
OLLAMA_BASE = "http://127.0.0.1:11434/api"

# ---- RAG pipeline (PDF-only) ----
from rag import RagPipeline
rag = RagPipeline()   # uses nomic-embed-text for embeddings inside rag.py


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------- Routes ----------------------

@app.route("/")
def index():
    """Serve the frontend."""
    return render_template("index.html")


@app.route("/api/models", methods=["GET"])
def list_models():
    """
    Return available text-generation models from Ollama as:
    [ {"name": "llama3:latest"}, {"name": "mistral:latest"} ]
    Embedding models are filtered out.
    """
    try:
        r = requests.get(f"{OLLAMA_BASE}/tags", timeout=10)
        r.raise_for_status()
        data = r.json()
        models_raw = data.get("models", [])
        models = []
        for m in models_raw:
            name = m.get("name", "")
            # filter out embedding models (e.g., nomic-embed-text)
            if not name.startswith("nomic-embed"):
                models.append({"name": name})
        return jsonify(models)
    except Exception as e:
        # Always return an array (frontend expects it)
        return jsonify([]), 200


@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    """Upload and ingest a PDF into the vector store."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed."}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {e}"}), 500

    try:
        rag.ingest(save_path)
        return jsonify({"message": "PDF ingested successfully!"})
    except Exception as e:
        return jsonify({"error": f"Ingestion failed: {e}"}), 500


@app.route("/api/ask", methods=["POST"])
def ask():
    """
    PDF-only RAG answering:
    - Retrieve top chunks from vector store
    - Build a helpful prompt
    - Generate with selected model
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    model = (data.get("model") or "").strip()
    # default 0.2; clamp to [0,1]
    try:
        temperature = float(data.get("temperature", 0.2))
    except Exception:
        temperature = 0.2
    temperature = max(0.0, min(1.0, temperature))

    if not question:
        return jsonify({"error": "Question is required."}), 400
    if not model:
        return jsonify({"error": "Model is required."}), 400

    # must have ingested docs
    try:
        context = rag.query(question)
    except Exception as e:
        # e.g., "No PDF ingested yet"
        return jsonify({"error": str(e)}), 400

    prompt = (
        "You are an expert assistant. Use ONLY the provided context to answer the user’s question. "
        "If the answer is not contained in the context, say you cannot find it in the document.\n\n"
        f"{context}\n\n"
        f"Question: {question}\n"
        "Answer clearly, concisely, and completely:"
    )

    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,               # return a single JSON object
                "options": {"temperature": temperature}
            },
            timeout=120
        )
        if resp.status_code != 200:
            return jsonify({"error": f"Ollama error: {resp.text}"}), 502

        payload = resp.json()
        # Some versions use "response", others might use "output"
        answer = payload.get("response") or payload.get("output") or ""
        return jsonify({"answer": answer.strip() or "(empty response)"}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to contact Ollama: {e}"}), 502
    except Exception as e:
        return jsonify({"error": f"Generation failed: {e}"}), 500


# ---------------------- Main ----------------------
if __name__ == "__main__":
    # Ensure uploads dir exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Run Flask
    app.run(host="0.0.0.0", port=5000, debug=True)

