import os
import tempfile
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from pathlib import Path
import asyncio

# Import your existing analyzer components
from resume_analyzer_v7 import FileExtractor, ResumeValidator, OllamaClient, ResumeAnalyzerError

# Import the agent components
from resume_agents import setup_agents

app = FastAPI(title="Resume Analyzer API", description="API for analyzing resumes using LLMs")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("./uploads")
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
DEFAULT_MODEL = "llama3"
REQUEST_TIMEOUT = 30

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(exist_ok=True)

# Classes
class SummaryRequest(BaseModel):
    file_id: str
    model: Optional[str] = DEFAULT_MODEL

class SummaryResponse(BaseModel):
    summary: str
    file_id: str

class JobDescriptionRequest(BaseModel):
    job_description: str
    resume_ids: List[str]

class CompareRequest(BaseModel):
    resume_ids: List[str]
    
class FeedbackRequest(BaseModel):
    resume_id: str
    is_positive: bool
    feedback_text: Optional[str] = None

# Utility functions
def is_valid_file_type(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS

# Initialize components
file_extractor = FileExtractor()
resume_validator = ResumeValidator()
ollama_client = OllamaClient(timeout=REQUEST_TIMEOUT)

# Initialize agents
resume_store, comparator_agent, gap_identifier_agent, ranker_agent, question_agent, fake_detector_agent = setup_agents()

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file (PDF, DOCX, or TXT)
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not is_valid_file_type(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    # Create a unique file ID and save path
    file_id = f"{os.urandom(8).hex()}_{file.filename}"
    file_path = UPLOAD_DIR / file_id
    
    # Save the uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    return {"file_id": file_id, "filename": file.filename}

@app.post("/summarize", response_model=SummaryResponse)
async def summarize_resume(request: SummaryRequest, background_tasks: BackgroundTasks):
    """
    Analyze and summarize a previously uploaded resume
    """
    file_path = UPLOAD_DIR / request.file_id
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Extract text
        text = file_extractor.extract_text(file_path)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text found in document")
        
        # Validate if it's a resume
        is_resume, confidence, explanation = resume_validator.is_resume(text)
        
        if not is_resume:
            raise HTTPException(
                status_code=400,
                detail=f"This document doesn't appear to be a resume (confidence: {confidence:.0%}). {explanation}"
            )
        
        # Generate summary
        summary = ollama_client.summarize_resume(text, request.model)
        
        # Store the resume in our database
        resume_store.add_resume(request.file_id, text, summary)
        
        # Schedule file cleanup (optional, comment out if you want to keep files)
        # background_tasks.add_task(cleanup_file, file_path)
        
        return {
            "summary": summary,
            "file_id": request.file_id
        }
        
    except ResumeAnalyzerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

# New endpoints for agent capabilities
@app.get("/resumes")
async def list_resumes():
    """List all stored resumes"""
    resumes = resume_store.get_all_resumes()
    return {"resumes": resumes}

@app.post("/compare")
async def compare_resumes(request: CompareRequest):
    """Compare multiple resumes"""
    if len(request.resume_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 resumes to compare")
    
    comparison = comparator_agent.compare_resumes(request.resume_ids)
    return {"comparison": comparison}

@app.post("/identify-gaps")
async def identify_gaps(request: JobDescriptionRequest):
    """Identify skill gaps for a specific job"""
    if len(request.resume_ids) != 1:
        raise HTTPException(status_code=400, detail="Please provide exactly one resume ID")
    
    analysis = gap_identifier_agent.identify_gaps(request.resume_ids[0], request.job_description)
    return {"gap_analysis": analysis}

@app.post("/rank-candidates")
async def rank_candidates(request: JobDescriptionRequest):
    """Rank candidates for a specific job"""
    if len(request.resume_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 resumes to rank")
    
    ranking = ranker_agent.rank_candidates(request.resume_ids, request.job_description)
    return {"ranking": ranking}

@app.post("/search-resumes")
async def search_resumes(query: str = Form(...), n_results: int = Form(5)):
    """Search resumes by semantic similarity"""
    results = resume_store.search_resumes(query, n_results)
    return {"results": results}

@app.post("/upload-job-description")
async def upload_job_description(file: UploadFile = File(...)):
    """Upload a job description file and extract text"""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Create a unique file ID and save path
    file_id = f"job_{uuid.uuid4().hex}"
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    # Save the uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Extract text from the job description
        text = file_extractor.extract_text(file_path)
        
        # Clean up the file
        os.remove(file_path)
        
        # Find matching resumes
        matching_results = resume_store.match_job_description(text)
        
        return {
            "job_description": text,
            "matching_resumes": matching_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process job description: {str(e)}")

@app.get("/generate-questions/{resume_id}")
async def generate_questions(resume_id: str):
    """Generate technical interview questions based on the candidate's resume"""
    questions = question_agent.generate_questions(resume_id, resume_store)
    return {"questions": questions}

@app.post("/detect-fake-resume")
async def detect_fake_resume(file: UploadFile = File(...)):
    """Analyze a resume for signs of being fake or AI-generated"""
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not is_valid_file_type(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    
    # Create a temp file
    file_id = f"temp_{uuid.uuid4().hex}"
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Extract text
        text = file_extractor.extract_text(file_path)
        
        # Analyze for fake content
        analysis = fake_detector_agent.detect_fake_resume(text)
        
        # Clean up the file
        os.remove(file_path)
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze resume: {str(e)}")

@app.post("/feedback")
async def add_feedback(request: FeedbackRequest):
    """Add feedback for a resume analysis"""
    success = resume_store.add_feedback(
        request.resume_id, 
        request.is_positive, 
        request.feedback_text
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return {"status": "success"}

@app.get("/feedback-stats")
async def get_feedback_stats():
    """Get statistics on feedback across all resumes"""
    stats = resume_store.get_feedback_stats()
    return stats

def cleanup_file(file_path: Path):
    """Remove uploaded file after processing"""
    try:
        if file_path.exists():
            os.remove(file_path)
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")

if __name__ == "__main__":
    uvicorn.run("resume_analyzer_api:app", host="0.0.0.0", port=8000, reload=True)
