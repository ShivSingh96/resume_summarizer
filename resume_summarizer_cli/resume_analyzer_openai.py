# import argparse
# import fitz  # PyMuPDF
# import docx
# import requests
# import os
# from dotenv import load_dotenv
# from openai import OpenAI

# # Load environment variables in a file called .env

# load_dotenv(override=True)
# api_key = os.getenv('OPENAI_API_KEY')

# # Check the key

# if not api_key:
#     print("No API key was found - please head over to the troubleshooting notebook in this folder to identify & fix!")
# elif not api_key.startswith("sk-proj-"):
#     print("An API key was found, but it doesn't start sk-proj-; please check you're using the right key - see troubleshooting notebook")
# elif api_key.strip() != api_key:
#     print("An API key was found, but it looks like it might have space or tab characters at the start or end - please remove them - see troubleshooting notebook")
# else:
#     print("API key found and looks good so far!")

# openai = OpenAI(api_key=api_key)

# # To give you a preview -- calling OpenAI with these messages is this easy. Any problems, head over to the Troubleshooting notebook.

# # message = "Hello, GPT! This is my first ever message to you! Hi!"
# # response = openai.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":message}])
# # print(response.choices[0].message.content)



# def extract_text_from_pdf(file_path):
#     doc = fitz.open(file_path)
#     return "\n".join([page.get_text() for page in doc])

# def extract_text_from_docx(file_path):
#     doc = docx.Document(file_path)
#     return "\n".join([para.text for para in doc.paragraphs])

# def summarize_resume(text):
#     prompt = f"""
# You are an expert resume analyst helping interviewers quickly assess a candidate.
# Given the following resume content, extract and summarize key details:
# - Total years of experience
# - Most recent role and company
# - Previous roles (title + company + dates if present)
# - Key technical contributions with impact
# - Tech stack: languages, tools, platforms
# - Notable projects (name + one-line description)
# - Certifications (if any)

# Return a structured summary in bullet points. Ignore personal details.

# Resume Content:
# {text}
# """
#     response = openai.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return response.choices[0].message.content

# def main():
#     parser = argparse.ArgumentParser(description="Resume Analyzer CLI (OpenAI Edition)")
#     parser.add_argument("filepath", help="Path to resume (PDF or DOCX)")

#     args = parser.parse_args()
#     filepath = args.filepath

#     if not os.path.exists(filepath):
#         print("❌ File not found.")
#         return

#     ext = filepath.lower().split(".")[-1]
#     if ext == "pdf":
#         text = extract_text_from_pdf(filepath)
#     elif ext == "docx":
#         text = extract_text_from_docx(filepath)
#     else:
#         print("❌ Unsupported file format. Use PDF or DOCX.")
#         return

#     print("📄 Analyzing resume with OpenAI...")

#     summary = summarize_resume(text)
#     print("\n🧑‍💼 Candidate Summary:\n")
#     print(summary)


# if __name__ == "__main__":
#     main()

