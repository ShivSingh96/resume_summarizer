import argparse
import fitz  # PyMuPDF
import docx
import requests
import os
import logging
from pathlib import Path
from typing import Optional
import sys

# Configuration
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
REQUEST_TIMEOUT = 30

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResumeAnalyzerError(Exception):
    """Custom exception for resume analyzer errors"""
    pass

class FileExtractor:
    """Handles text extraction from different file formats"""
    
    @staticmethod
    def extract_text_from_pdf(file_path: Path) -> str:
        try:
            doc = fitz.open(file_path)
            text = "\n".join([page.get_text() for page in doc])
            doc.close()
            return text
        except Exception as e:
            raise ResumeAnalyzerError(f"Failed to extract text from PDF: {e}")

    @staticmethod
    def extract_text_from_docx(file_path: Path) -> str:
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            raise ResumeAnalyzerError(f"Failed to extract text from DOCX: {e}")

    @staticmethod
    def extract_text_from_txt(file_path: Path) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                raise ResumeAnalyzerError(f"Failed to read text file: {e}")
        except Exception as e:
            raise ResumeAnalyzerError(f"Failed to extract text from TXT: {e}")

    def extract_text(self, file_path: Path) -> str:
        """Extract text based on file extension"""
        extension = file_path.suffix.lower()
        
        extractors = {
            ".pdf": self.extract_text_from_pdf,
            ".docx": self.extract_text_from_docx,
            ".txt": self.extract_text_from_txt
        }
        
        if extension not in extractors:
            raise ResumeAnalyzerError(f"Unsupported file format: {extension}")
        
        return extractors[extension](file_path)

class OllamaClient:
    """Handles communication with Ollama API"""
    
    def __init__(self, endpoint: str = OLLAMA_ENDPOINT):
        self.endpoint = endpoint
    
    def summarize_resume(self, text: str, model: str) -> str:
        if not text.strip():
            raise ResumeAnalyzerError("Resume text is empty")
        
        prompt = self._build_prompt(text)
        
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            if "response" not in result:
                raise ResumeAnalyzerError("Invalid response format from Ollama")
            
            return result["response"]
            
        except requests.exceptions.ConnectionError:
            raise ResumeAnalyzerError("Cannot connect to Ollama. Is it running?")
        except requests.exceptions.Timeout:
            raise ResumeAnalyzerError("Request timed out. Try again later.")
        except requests.exceptions.RequestException as e:
            raise ResumeAnalyzerError(f"API request failed: {e}")
        except Exception as e:
            raise ResumeAnalyzerError(f"Unexpected error: {e}")
    
    def _build_prompt(self, text: str) -> str:
        return f"""
You are an expert resume analyst helping interviewers quickly assess a candidate.
Given the following resume content, extract and summarize key details:

📊 **Experience Overview:**
- Total years of experience
- Most recent role and company

💼 **Work History:**
- Previous roles (title + company + duration)

🎯 **Key Achievements:**
- Technical contributions with measurable impact
- Leadership or project management experience

🛠️ **Technical Skills:**
- Programming languages
- Frameworks and tools
- Platforms and technologies

🚀 **Notable Projects:**
- Project names with brief descriptions
- Technologies used

🏆 **Certifications & Education:**
- Relevant certifications
- Degrees (if mentioned)

Return a well-structured summary using bullet points and emojis. Focus on professional qualifications only.

Resume Content:
{text}
"""

class ResumeAnalyzer:
    """Main application class"""
    
    def __init__(self):
        self.extractor = FileExtractor()
        self.ollama_client = OllamaClient()
    
    def validate_file(self, file_path: Path) -> None:
        """Validate file exists and has supported extension"""
        if not file_path.exists():
            raise ResumeAnalyzerError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ResumeAnalyzerError(f"Path is not a file: {file_path}")
        
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            supported = ", ".join(SUPPORTED_EXTENSIONS)
            raise ResumeAnalyzerError(f"Unsupported file format. Supported: {supported}")
        
        # Check file size (limit to 10MB)
        if file_path.stat().st_size > 10 * 1024 * 1024:
            raise ResumeAnalyzerError("File too large (max 10MB)")
    
    def analyze(self, file_path: str, model: str, verbose: bool = False) -> str:
        """Main analysis method"""
        file_path = Path(file_path).resolve()
        
        logger.info(f"Analyzing resume: {file_path}")
        
        # Validate input
        self.validate_file(file_path)
        
        # Extract text
        logger.info("Extracting text...")
        text = self.extractor.extract_text(file_path)
        
        if not text.strip():
            raise ResumeAnalyzerError("No text found in the document")
        
        if verbose:
            print("\n📄 Extracted Resume Text:\n")
            print("-" * 50)
            print(text)
            print("-" * 50)
            print("\n🔍 Summarizing...\n")
        
        # Generate summary
        logger.info(f"Generating summary using model: {model}")
        summary = self.ollama_client.summarize_resume(text, model)
        
        return summary

def main():
    parser = argparse.ArgumentParser(
        description="Resume Analyzer CLI (Ollama Edition)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py resume.pdf
  python cli.py resume.docx --model llama3.1 --verbose
  python cli.py resume.txt --model mistral
        """
    )
    
    parser.add_argument(
        "filepath", 
        help="Path to resume file (.pdf, .docx, or .txt)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Print full extracted text before summarizing"
    )
    parser.add_argument(
        "--model", 
        default="llama3", 
        help="Choose LLM model (default: llama3)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress info messages"
    )

    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    try:
        analyzer = ResumeAnalyzer()
        summary = analyzer.analyze(args.filepath, args.model, args.verbose)
        
        print("\n🧑‍💼 Candidate Summary:")
        print("=" * 50)
        print(summary)
        print("=" * 50)
        
    except ResumeAnalyzerError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error occurred. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()