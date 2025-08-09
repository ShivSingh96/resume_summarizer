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
    
    def summarize_resume(self, text: str, model: str, detail_level: str = "standard") -> str:
        if not text.strip():
            raise ResumeAnalyzerError("Resume text is empty")
        
        prompt = self._build_prompt(text, detail_level)
        
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
    
    def _build_prompt(self, text: str, detail_level: str) -> str:
        """Build a prompt based on the desired detail level"""
        
        # Base instructions for all detail levels
        base_instructions = """
You are an expert resume analyst helping recruiters and interviewers quickly assess candidates.
Extract and summarize the key information from the resume below.
Use clear formatting with headings, bullet points, and emojis where appropriate.
Focus only on professional qualifications and skills.
Ignore personal details like address, phone number, etc.
"""

        # Detail level specific instructions
        detail_instructions = {
            "brief": """
Create a very concise summary focusing only on:
1. Total experience (years)
2. Current/most recent position
3. Top 3-5 technical skills
4. Highest education level
Limit to 10 lines maximum.
""",
            "standard": """
Create a comprehensive professional summary including:

📊 **Experience Overview:**
- Total years of relevant experience
- Most recent role and company with duration

💼 **Key Work History:**
- Previous 2-3 roles with company names and timeframes
- List only the most relevant positions

🛠️ **Technical Skills:**
- Group by category (languages, frameworks, tools, etc.)
- Highlight expertise level where indicated

🎯 **Notable Achievements:**
- 2-3 most impressive professional accomplishments with metrics
- Focus on technical impact and business outcomes

🏆 **Education & Certifications:**
- Relevant degrees and technical certifications only

Keep the summary focused and concise, approximately 20-25 lines total.
""",
            "detailed": """
Create a detailed and structured professional analysis including:

📊 **Experience Overview:**
- Total years of relevant experience
- Career progression summary
- Current or most recent role details

💼 **Work History:**
- Comprehensive list of previous roles with exact durations
- Responsibilities and scope for each position
- Team size and reporting structure if mentioned

🛠️ **Technical Proficiency:**
- Detailed breakdown of technical skills by category
- Version/technology specific expertise
- Architecture and methodology knowledge

🎯 **Professional Achievements:**
- Quantified accomplishments with metrics and impact
- Project outcomes and business value delivered
- Leadership and mentorship contributions

🚀 **Notable Projects:**
- Key projects with description, technologies, and outcomes
- Role and specific contributions to each project
- Timeframes and scale of projects

🏆 **Education & Professional Development:**
- All degrees with institutions and graduation dates
- Certifications with dates and versions
- Continuous learning activities and self-development

Include a "Key Strengths" section that highlights what makes this candidate stand out.
Add a "Potential Interview Focus Areas" section suggesting 3-5 topics to explore further.
"""
        }
        
        # Get the appropriate instructions or default to brief
        instruction_text = detail_instructions.get(detail_level, detail_instructions["brief"])
        
        return f"""{base_instructions}
{instruction_text}

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
    
    def analyze(self, file_path: str, model: str, detail_level: str = "standard", verbose: bool = False) -> str:
        """Main analysis method"""
        file_path = Path(file_path).resolve()
        
        #logger.info(f"Analyzing resume: {file_path}")
        
        # Validate input
        self.validate_file(file_path)
        
        # Extract text
        #logger.info("Extracting text...")
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
        #logger.info(f"Generating summary using model: {model}, detail level: {detail_level}")
        summary = self.ollama_client.summarize_resume(text, model, detail_level)
        
        return summary

def main():
    parser = argparse.ArgumentParser(
        description="Resume Analyzer CLI - Quickly summarize resumes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python resume_analyzer_v3.py resume.pdf
  python resume_analyzer_v3.py resume.docx --model llama3 --detail brief
  python resume_analyzer_v3.py resume.txt --model mistral --detail detailed --verbose
        """
    )
    
    parser.add_argument(
        "filepath", 
        help="Path to resume file (.pdf, .docx, or .txt)"
    )
    parser.add_argument(
        "--model", 
        default="llama3", 
        help="Choose LLM model (default: llama3)"
    )
    parser.add_argument(
        "--detail", 
        choices=["brief", "standard", "detailed"],
        default="standard",
        help="Level of detail in summary (default: standard)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Print full extracted text before summarizing"
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
        summary = analyzer.analyze(args.filepath, args.model, args.detail, args.verbose)
        
        print("\n🧑‍💼 Candidate Summary:")
        print("=" * 50)
        print(summary)
        print("=" * 50)
        
        if args.detail == "brief":
            print("\nℹ️  For more details, try: --detail standard or --detail detailed")
        
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