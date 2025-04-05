import os
import fitz
import spacy
from flask import Flask, render_template, request, jsonify

# Load NLP model
nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)

# Path to notes folder
NOTES_DIR = os.path.join(os.path.dirname(__file__), "notes")

# Subject to file mapping
FILE_MAP = {
    "chemistry": "Chemistry_chapter-1.pdf",
    "biology": "Biology_chapter-1.pdf",
    "physics": "Physics_chapter-1.pdf",
    "english": "English_chapter-1.pdf",
}

@app.route("/")
def index():
    subjects = ["Chemistry", "Biology", "Physics", "English"]
    return render_template("index.html", subjects=subjects)

@app.route("/notes", methods=["POST"])
def show_notes():
    subject = request.form["subject"].lower()
    level = request.form.get("level", "beginner").lower()

    if subject not in FILE_MAP:
        return "Error: Subject not found!", 404

    note_file = os.path.join(NOTES_DIR, FILE_MAP[subject])
    if not os.path.exists(note_file):
        return f"Error: File not found at {note_file}", 404

    text = extract_text_from_pdf(note_file)
    processed_content = modify_text_based_on_level(text, level)

    return render_template(
        "notes.html",
        subject=subject.capitalize(),
        level=level.capitalize(),
        key_points=processed_content.get("key_points", []),  
        paragraph=processed_content.get("paragraph", ""),  
        summary=processed_content.get("summary", "")  
    )

@app.route("/change_level", methods=["POST"])
def change_level():
    subject = request.form["subject"].lower()
    level = request.form["level"].lower()

    note_file = os.path.join(NOTES_DIR, FILE_MAP.get(subject, ""))
    if not os.path.exists(note_file):
        return jsonify({"error": "File not found"}), 404

    text = extract_text_from_pdf(note_file)
    modified_text = modify_text_based_on_level(text, level)

    return jsonify(modified_text)

# PDF text extraction
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    return text.strip()

# Modify text based on level
def modify_text_based_on_level(text, level):
    """Extracts structured content dynamically for different difficulty levels."""
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    if len(sentences) < 10:
        return {"key_points": ["Content too short!"], "summary": "Not enough data."}

    if level == "beginner":
        return {
            "key_points": sentences[:5],  # First 5 sentences as bullet points
            "summary": " ".join(sentences[5:10]),  # Summary from next 5 sentences
            "paragraph": ""  # No paragraphs for beginner
        }

    elif level == "intermediate":
        return {
            "key_points": sentences[:5],  # First 5 sentences as bullet points
            "paragraph": " ".join(sentences[5:10]),  # Middle section as a paragraph
            "summary": " ".join(sentences[10:15])  # Last part as summary
        }

    elif level == "advanced":
        # Organizing text into structured paragraphs
        paragraphs = []
        current_paragraph = []

        for sent in sentences:
            current_paragraph.append(sent)
            if len(current_paragraph) >= 5:  # Grouping sentences into paragraphs of 5 sentences each
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []

        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))  # Adding any remaining sentences

        return {
            "key_points": [],  # No bullet points for advanced
            "paragraph": "<br><br>".join(paragraphs),  # Structured paragraphs
            "summary": ""  # No summary for advanced
        }

    return {"key_points": [], "paragraph": "", "summary": text}  # Default case

if __name__ == "__main__":
    app.run(debug=True)
