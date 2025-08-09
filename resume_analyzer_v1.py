import argparse
import fitz  # PyMuPDF
import docx
import requests
import os

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"  # or "mistral", "gemma", etc.

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join([page.get_text() for page in doc])

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def summarize_resume(text):
    prompt = f"""
You are an expert resume analyst helping interviewers quickly assess a candidate.
Given the following resume content, extract and summarize key details:
- Total years of experience
- Most recent role and company
- Previous roles (title + company + dates if present)
- Key technical contributions with impact
- Tech stack: languages, tools, platforms
- Notable projects (name + one-line description)
- Certifications (if any)

Return a structured summary in bullet points. Ignore personal details.

Resume Content:
{text}
"""

    response = requests.post(OLLAMA_ENDPOINT, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })

    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"❌ Error from Ollama: {response.status_code} - {response.text}"

def main():
    parser = argparse.ArgumentParser(description="Resume Analyzer CLI (Ollama Edition)")
    parser.add_argument("filepath", help="Path to resume (PDF or DOCX)")

    args = parser.parse_args()
    filepath = args.filepath

    if not os.path.exists(filepath):
        print("❌ File not found.")
        return

    ext = filepath.lower().split(".")[-1]
    if ext == "pdf":
        text = extract_text_from_pdf(filepath)
    elif ext == "docx":
        text = extract_text_from_docx(filepath)
    else:
        print("❌ Unsupported file format. Use PDF or DOCX.")
        return

    print("📄 Analyzing resume with Ollama...")

    summary = summarize_resume(text)
    print("\n🧑‍💼 Candidate Summary:\n")
    print(summary)

if __name__ == "__main__":
    main()

