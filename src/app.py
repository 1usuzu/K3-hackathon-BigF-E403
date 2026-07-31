import json
import os
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from agent import VLearnAgent  # noqa: E402
from pdf_utils import extract_pages_text, extract_structured_text  # noqa: E402

app = Flask(__name__, static_folder="../static")
vlearn_agent = VLearnAgent()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdfs")


def _pdf_path(filename: str) -> str | None:
    """Return absolute path if the PDF exists, else None."""
    if not filename:
        return None
    path = os.path.join(PDF_DIR, os.path.basename(filename))  # basename: no path traversal
    return path if os.path.exists(path) else None


# ── serve PDFs to frontend iframe ──────────────────────────────────────────────
@app.route("/pdfs/<path:filename>")
def serve_pdfs(filename):
    print("SERVE PDF ROUTE CALLED FOR:", filename, "IN", PDF_DIR, flush=True)
    return send_from_directory(PDF_DIR, filename, mimetype="application/pdf")


# ── generate mindmap + flashcard ───────────────────────────────────────────────
@app.route("/api/generate_study_material", methods=["POST"])
def generate_study_material():
    slide_text = ""
    student_history = []

    # Case 1: file upload (multipart form)
    if "pdf_file" in request.files:
        file = request.files["pdf_file"]
        if file.filename:
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    file.save(tmp.name)
                    slide_text = extract_structured_text(tmp.name)
                os.unlink(tmp.name)
            except Exception as e:
                return jsonify({"status": "error", "message": f"Lỗi đọc PDF: {e}"}), 500

        history_raw = request.form.get("student_history", "[]")
        try:
            student_history = json.loads(history_raw)
        except Exception:
            student_history = []

    # Case 2: JSON body with pdf_filename
    elif request.is_json:
        data = request.json
        student_history = data.get("student_history", [])
        os.makedirs(PDF_DIR, exist_ok=True)

        pdf_filename = data.get("pdf_filename")
        # Auto-pick first PDF if none specified
        if not pdf_filename:
            pdfs = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
            pdf_filename = pdfs[0] if pdfs else None

        path = _pdf_path(pdf_filename)
        if path:
            try:
                slide_text = extract_structured_text(path)
                print(f"[PDF] {pdf_filename} → {len(slide_text)} chars extracted", flush=True)
            except Exception as e:
                return jsonify({"status": "error", "message": f"Lỗi đọc file nội bộ: {e}"}), 500
        else:
            # Fallback: raw text from frontend (e.g. test harness)
            slide_text = data.get("slide_text", "")

    if not slide_text:
        return jsonify({
            "status": "error",
            "message": "Không tìm thấy file PDF nào trong thư mục data/pdfs.",
        }), 400

    result = vlearn_agent.generate_study_material(slide_text, student_history)
    return jsonify(result)


# ── generate flashcards for a specific mindmap section ─────────────────────────
@app.route("/api/generate_section_flashcards", methods=["POST"])
def generate_section_flashcards():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Expected JSON request."}), 400

    data = request.json
    pdf_filename = data.get("pdf_filename")
    slide_refs: list[int] = data.get("slide_refs", [])
    topic = data.get("topic", "")

    slide_text = ""
    path = _pdf_path(pdf_filename)
    if path and slide_refs:
        try:
            slide_text = extract_pages_text(path, slide_refs)
        except Exception as e:
            return jsonify({"status": "error", "message": f"Lỗi đọc PDF: {e}"}), 500

    if not slide_text:
        slide_text = "Nội dung mục này (chưa xác định slide cụ thể)."

    result = vlearn_agent.generate_section_flashcards(slide_text, topic)
    return jsonify(result)


# ── generate quiz from weak flashcards ─────────────────────────────────────────
@app.route("/api/generate_quiz", methods=["POST"])
def generate_quiz():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Expected JSON request."}), 400

    data = request.json
    history: list = data.get("history", [])
    if not history:
        return jsonify({"status": "error", "message": "Không có thẻ yếu nào để tạo Quiz."})

    pdf_filename = data.get("pdf_filename")
    slide_text = ""
    path = _pdf_path(pdf_filename)
    if path:
        try:
            # For quiz context we only need a summary, not the full structured text
            slide_text = extract_structured_text(path, max_chars=6000)
        except Exception:
            pass  # Quiz can still work without full slide context

    result = vlearn_agent.generate_quiz(history, slide_text)
    return jsonify(result)


if __name__ == "__main__":
    print("V-Learn AI Server is running at http://127.0.0.1:5001")
    app.run(port=5001, debug=True, use_reloader=False)
