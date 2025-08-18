# Resume Analyzer

A powerful AI-powered resume analysis tool built with FastAPI, Ollama, and Next.js. This application analyzes resumes, extracts key information, compares candidates, matches resumes with job descriptions, detects AI-generated content, and more.

## Table of Contents

- Features
- System Requirements
- Installation
- Usage
- Technical Architecture
- Troubleshooting

## Features

### Core Functionality
- **Resume Upload & Analysis**: Upload resumes in PDF, DOCX, or TXT format and get AI-generated summaries
- **Resume Storage**: Save analyzed resumes for later reference and comparison
- **Resume Management**: View, search, and manage your resume database

### Phase 2: Resume Comparison
- **Multi-Resume Comparison**: Compare multiple candidates side-by-side
- **Skill Gap Analysis**: Identify missing skills between a resume and job requirements
- **Candidate Ranking**: Rank multiple candidates for a specific job

### Phase 3: Enhanced Comparison
- **Resume Selection**: Select specific resumes for detailed comparison
- **Job Description Analysis**: Match resumes against job descriptions
- **Expanded Visualization**: View detailed comparisons with strengths and weaknesses

### Phase 4: Advanced Features
- **Job Matching**: Upload job descriptions and find matching candidates
- **Follow-up Questions**: Generate clarifying questions for ambiguous resumes
- **Fake Resume Detection**: Identify potentially AI-generated or fraudulent resumes
- **Feedback System**: Provide feedback to improve analysis quality

## System Requirements

- **Python 3.8+**
- **Node.js 16+**
- **Ollama** running locally or on a server
- **At least 8GB RAM** (16GB recommended for better performance)

## Installation

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/resume-analyzer.git
   cd resume-analyzer
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install and start Ollama (if not already running):
   ```bash
   # Follow Ollama installation instructions at https://ollama.ai/
   # Pull the required model
   ollama pull llama3
   ```

5. Start the backend server:
   ```bash
   cd resume-analyzer-backend
   python resume_analyzer_api.py
   ```
   The API will be available at http://localhost:8000

### Frontend Setup

1. Install frontend dependencies:
   ```bash
   cd resume-analyzer-ui
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```
   The UI will be available at http://localhost:3000

## Usage

### Upload and Analyze Resumes

1. From the main page, click on "Upload Resume"
2. Drag and drop your resume file (PDF, DOCX, or TXT)
3. Click "Analyze Resume" and wait for the AI to process it
4. View the comprehensive summary of the candidate
5. Provide feedback using the thumbs up/down buttons

### Manage Resumes

1. Click on "Manage Resumes" in the navigation bar
2. View all previously analyzed resumes
3. Select resumes by checking the boxes
4. Click "Compare Selected Resumes" to see a detailed comparison
5. Click "Expand" on any resume to see its full details
6. Generate follow-up questions for ambiguous resumes

### Job Description Analysis

1. From the "Manage Resumes" view, select one or more resumes
2. Scroll down to the Job Description form
3. Paste a job description in the text area
4. Click "Identify Skill Gaps" (for single resume) or "Rank Candidates" (for multiple resumes)
5. Review the analysis results

### Job Matcher

1. Click on "Job Matcher" in the navigation bar
2. Upload a job description file or paste text directly
3. Click "Find Matching Resumes"
4. Review the list of matching candidates ranked by relevance

### Fake Resume Detection

1. Click on "Fake Detector" in the navigation bar
2. Upload a resume you want to verify
3. Click "Analyze Resume"
4. Review the analysis for signs of AI generation or suspicious content
5. Check the confidence score and specific red flags identified

## Technical Architecture

### Backend Components

- **FastAPI Server**: Handles HTTP requests and orchestrates the analysis process
- **Resume Analyzer Core**: Extracts and processes resume text
- **Ollama Client**: Connects to Ollama for LLM inference
- **Agent System**: Specialized AI agents for different analysis tasks
- **Vector Database**: Stores resume embeddings for semantic search

### Frontend Components

- **Next.js Application**: React-based UI with server-side rendering
- **Resume Manager**: Interface for viewing and managing resumes
- **Job Description Form**: Interface for job matching and skill gap analysis
- **Fake Detector**: Interface for detecting AI-generated resumes

## Troubleshooting

### Common Issues

1. **Backend connection errors**:
   - Ensure the backend server is running at http://localhost:8000
   - Check if Ollama is running and accessible

2. **File upload errors**:
   - Verify the file is in a supported format (PDF, DOCX, TXT)
   - Ensure the file size is reasonable (under 10MB)

3. **Slow analysis times**:
   - LLM inference can take time, especially on first run
   - Consider using a more powerful machine or GPU acceleration

4. **"No resumes found" error**:
   - Upload some resumes first before using comparison features
   - Check if the backend storage is properly initialized

### Getting Help

If you encounter issues not covered here, please:
1. Check the console logs in both frontend and backend
2. Verify all dependencies are correctly installed
3. Create an issue in the GitHub repository with detailed information

---

Built with ❤️ using FastAPI, Next.js, and Ollama

############################################
1. Create a virtual environment (important!) 
python3 -m venv resume_env 
source resume_env/bin/activate 

2. Install the package 
pip3 install ./resume_summarizer-0.1-py3-none-any.whl 

3. Run it on any resume 
resume_summarizer path/to/resume.pdf 

Optional flags: 
 --verbose # Show extracted text
##############################################

