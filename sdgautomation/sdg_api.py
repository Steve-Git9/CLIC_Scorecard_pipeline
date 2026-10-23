from flask import Flask, request, jsonify
from docx import Document
import fitz
import tempfile
import os

from sdg_core import classify_document, embed_sdgs, load_model, load_sdgs

app = Flask(__name__)

# ====================================
# LOAD MODEL
# ====================================

print("Loading embedding model...")
model = load_model()

print("Loading SDGs...")

sdgs = load_sdgs()

print("Creating SDG embeddings...")

sdg_embeddings = embed_sdgs(model, sdgs)

print("Ready.")

# ====================================
# TEXT EXTRACTION
# ====================================

def extract_pdf(path):

    text = ""

    pdf = fitz.open(path)

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text


def extract_docx(path):

    document = Document(path)

    return "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
    )

# ====================================
# API
# ====================================

@app.route("/analyze", methods=["POST"])
def analyze():

    if "file" not in request.files:

        return jsonify({
            "error": "No file provided"
        }), 400

    uploaded_file = request.files["file"]

    extension = os.path.splitext(
        uploaded_file.filename
    )[1].lower()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension
    ) as tmp:

        uploaded_file.save(tmp.name)

        temp_path = tmp.name

    try:

        if extension == ".pdf":

            text = extract_pdf(temp_path)

        elif extension == ".docx":

            text = extract_docx(temp_path)

        else:

            return jsonify({
                "error": "Supported formats: PDF and DOCX"
            }), 400

        result = classify_document(text, model, sdgs, sdg_embeddings)

        return jsonify(result)

    finally:

        if os.path.exists(temp_path):

            os.remove(temp_path)

# ====================================
# START
# ====================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )