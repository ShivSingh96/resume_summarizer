import os
from typing import List, Dict, Any, Optional
from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
import json
import time
from pathlib import Path

# Configuration
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
DEFAULT_MODEL = "llama3"
PERSIST_DIRECTORY = "chroma_db"
RESUME_DATABASE = "resume_database.json"

# Initialize the LLM with Ollama
llm = Ollama(
    model=DEFAULT_MODEL,
    base_url=OLLAMA_ENDPOINT,
    temperature=0.1
)

class ResumeStore:
    """Manages storage and retrieval of resume data"""
    
    def __init__(self, db_path: str = RESUME_DATABASE):
        self.db_path = db_path
        self.resumes = self._load_db()
        
        # Ensure vector store directory exists
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        
        # Initialize embedding function (using HuggingFace for free embeddings)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Initialize or load vector store
        if os.path.exists(PERSIST_DIRECTORY) and len(os.listdir(PERSIST_DIRECTORY)) > 0:
            self.vector_store = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=self.embeddings)
        else:
            self.vector_store = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=self.embeddings)
    
    def _load_db(self) -> Dict:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except:
                return {"resumes": {}}
        else:
            return {"resumes": {}}
    
    def _save_db(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.resumes, f)
    
    def add_resume(self, resume_id: str, resume_text: str, summary: str, metadata: Dict = None):
        """Add a resume to both the JSON store and vector database"""
        if metadata is None:
            metadata = {}
            
        # Add to simple JSON store
        self.resumes["resumes"][resume_id] = {
            "summary": summary,
            "metadata": metadata
        }
        self._save_db()
        
        # Add to vector store for semantic search
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(resume_text)
        
        for i, chunk in enumerate(chunks):
            self.vector_store.add_texts(
                texts=[chunk],
                metadatas=[{"resume_id": resume_id, "chunk_id": i, **metadata}],
                ids=[f"{resume_id}_chunk_{i}"]
            )
        
        self.vector_store.persist()
        return resume_id
    
    def get_resume(self, resume_id: str) -> Optional[Dict]:
        """Get a resume by ID"""
        if resume_id in self.resumes["resumes"]:
            return self.resumes["resumes"][resume_id]
        return None
    
    def get_all_resumes(self) -> List[Dict]:
        """Get all resumes with their IDs"""
        return [{"id": k, **v} for k, v in self.resumes["resumes"].items()]
    
    def search_resumes(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search resumes by semantic similarity"""
        results = self.vector_store.similarity_search(query, k=n_results)
        resume_ids = set([doc.metadata["resume_id"] for doc in results])
        
        return [{"id": rid, **self.resumes["resumes"][rid]} 
                for rid in resume_ids 
                if rid in self.resumes["resumes"]]
    
    def match_job_description(self, job_description: str, top_n: int = 5) -> List[Dict]:
        """Find resumes that match a job description"""
        # First use vector search to find potential matches
        try:
            results = self.vector_store.similarity_search(job_description, k=10)
            resume_ids = set([doc.metadata["resume_id"] for doc in results])
            
            # For each resume, calculate a more detailed match score
            matches = []
            for rid in resume_ids:
                resume = self.get_resume(rid)
                if resume:
                    # Calculate match score using our LLM
                    match_score = self._calculate_match_score(resume["summary"], job_description)
                    matches.append({
                        "id": rid,
                        "summary": resume["summary"],
                        "match_score": match_score,
                        "metadata": resume["metadata"]
                    })
            
            # Sort by match score and return top N
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            return matches[:top_n]
        except Exception as e:
            print(f"Error matching job description: {e}")
            return []
    
    def _calculate_match_score(self, resume_summary: str, job_description: str) -> float:
        """Calculate how well a resume matches a job description"""
        try:
            # Use a simple prompt to get a match percentage
            prompt = PromptTemplate(
                input_variables=["resume", "job"],
                template="""
                You are evaluating how well a candidate's resume matches a job description.
                
                Resume:
                {resume}
                
                Job Description:
                {job}
                
                On a scale of 0 to 100, where 100 means perfect match and 0 means no match at all,
                assign a score based on skills, experience, and qualifications match.
                Return ONLY the numeric score without explanation.
                """
            )
            
            chain = LLMChain(llm=llm, prompt=prompt)
            result = chain.run(resume=resume_summary, job=job_description)
            
            # Extract numeric score
            try:
                # Clean the result and extract just the number
                cleaned_result = result.strip().replace('%', '')
                return float(cleaned_result) / 100
            except ValueError:
                # If we can't parse a number, default to 0
                return 0
        except Exception as e:
            print(f"Error calculating match score: {e}")
            return 0
    
    def add_feedback(self, resume_id: str, is_positive: bool, feedback_text: str = None):
        """Add user feedback for a resume analysis"""
        if resume_id not in self.resumes["resumes"]:
            return False
        
        # Initialize feedback array if it doesn't exist
        if "feedback" not in self.resumes["resumes"][resume_id]:
            self.resumes["resumes"][resume_id]["feedback"] = []
        
        # Add the feedback
        self.resumes["resumes"][resume_id]["feedback"].append({
            "timestamp": time.time(),
            "is_positive": is_positive,
            "text": feedback_text
        })
        
        self._save_db()
        return True

    def get_feedback_stats(self):
        """Get statistics on feedback across all resumes"""
        total_positive = 0
        total_negative = 0
        resume_count = 0
        
        for resume_id, resume_data in self.resumes["resumes"].items():
            if "feedback" in resume_data:
                resume_count += 1
                for feedback in resume_data["feedback"]:
                    if feedback["is_positive"]:
                        total_positive += 1
                    else:
                        total_negative += 1
        
        return {
            "total_positive": total_positive,
            "total_negative": total_negative,
            "resume_count_with_feedback": resume_count,
            "total_resume_count": len(self.resumes["resumes"])
        }


class ResumeComparatorAgent:
    """Agent that compares multiple resumes"""
    
    def __init__(self, resume_store: ResumeStore):
        self.resume_store = resume_store
        self.llm = llm
        
        self.compare_prompt = PromptTemplate(
            input_variables=["resume_summaries"],
            template="""
            You are a resume comparison expert. Compare the following candidate summaries and highlight:
            1. Strengths and weaknesses of each candidate
            2. Key differentiating factors
            3. Technical skill comparison
            4. Experience level comparison
            
            Candidate resumes:
            {resume_summaries}
            
            Create a comparison table and provide a brief analysis of each candidate.
            """
        )
        
        self.compare_chain = LLMChain(llm=self.llm, prompt=self.compare_prompt)
    
    def compare_resumes(self, resume_ids: List[str]) -> str:
        """Compare multiple resumes by ID"""
        if len(resume_ids) < 2:
            return "Need at least 2 resumes to compare"
            
        resume_summaries = []
        for rid in resume_ids:
            resume = self.resume_store.get_resume(rid)
            if resume:
                resume_summaries.append(f"Resume ID: {rid}\n{resume['summary']}")
        
        if not resume_summaries:
            return "No valid resumes found to compare"
        
        try:
            result = self.compare_chain.run(resume_summaries="\n\n---\n\n".join(resume_summaries))
            return result
        except Exception as e:
            return f"Error comparing resumes: {str(e)}"


class SkillGapIdentifierAgent:
    """Agent that identifies skill gaps based on job requirements"""
    
    def __init__(self, resume_store: ResumeStore):
        self.resume_store = resume_store
        self.llm = llm
        
        self.gap_prompt = PromptTemplate(
            input_variables=["job_description", "resume_summary"],
            template="""
            You are a technical recruiter helping identify skill gaps between a job description and a candidate.
            
            Job description:
            {job_description}
            
            Candidate summary:
            {resume_summary}
            
            Identify the following:
            1. Required skills missing from the candidate's profile
            2. Experience gaps that need to be addressed
            3. Certifications or qualifications that would strengthen the application
            4. Overall skill gap severity (Low, Medium, High)
            
            Format your response as a structured analysis.
            """
        )
        
        self.gap_chain = LLMChain(llm=self.llm, prompt=self.gap_prompt)
    
    def identify_gaps(self, resume_id: str, job_description: str) -> str:
        """Identify gaps between resume and job description"""
        resume = self.resume_store.get_resume(resume_id)
        
        if not resume:
            return "Resume not found"
        
        try:
            result = self.gap_chain.run(
                job_description=job_description,
                resume_summary=resume["summary"]
            )
            return result
        except Exception as e:
            return f"Error identifying skill gaps: {str(e)}"


class CandidateRankerAgent:
    """Agent that ranks candidates based on job fit"""
    
    def __init__(self, resume_store: ResumeStore):
        self.resume_store = resume_store
        self.llm = llm
        
        self.rank_prompt = PromptTemplate(
            input_variables=["job_description", "resume_summaries"],
            template="""
            You are a talent acquisition specialist ranking candidates for a position.
            
            Job description:
            {job_description}
            
            Candidate summaries:
            {resume_summaries}
            
            Rank these candidates from most to least suitable. For each candidate:
            1. Assign a fit score (0-100)
            2. List their key strengths for this role
            3. List their key weaknesses for this role
            4. Provide a brief explanation for the ranking
            
            Return results as a ranked list with detailed justification for each candidate.
            """
        )
        
        self.rank_chain = LLMChain(llm=self.llm, prompt=self.rank_prompt)
    
    def rank_candidates(self, resume_ids: List[str], job_description: str) -> str:
        """Rank candidates based on job fit"""
        if not resume_ids:
            return "No resumes provided for ranking"
            
        resume_summaries = []
        for rid in resume_ids:
            resume = self.resume_store.get_resume(rid)
            if resume:
                resume_summaries.append(f"Candidate ID: {rid}\n{resume['summary']}")
        
        if not resume_summaries:
            return "No valid resumes found to rank"
        
        try:
            result = self.rank_chain.run(
                job_description=job_description,
                resume_summaries="\n\n---\n\n".join(resume_summaries)
            )
            return result
        except Exception as e:
            return f"Error ranking candidates: {str(e)}"
        
        
class QuestionGeneratorAgent:
    """Agent that generates follow-up questions for ambiguous resumes"""
    
    def __init__(self):
        self.llm = llm
        
        self.question_prompt = PromptTemplate(
            input_variables=["resume_summary"],
            template="""
            You are a technical recruiter reviewing a resume. For this candidate, identify 3-5 areas 
            where more information would be helpful to fully evaluate them. These should be ambiguous 
            or unclear aspects of their resume.
            
            Resume Summary:
            {resume_summary}
            
            Generate specific follow-up questions that would help clarify these ambiguities.
            Format your response as a JSON array of questions. Example:
            ["Question 1?", "Question 2?", "Question 3?"]
            """
        )
        
        self.question_chain = LLMChain(llm=self.llm, prompt=self.question_prompt)
    
    def generate_questions(self, resume_id: str, resume_store: ResumeStore) -> List[str]:
        """Generate follow-up questions for a resume"""
        resume = resume_store.get_resume(resume_id)
        
        if not resume:
            return ["Resume not found"]
        
        try:
            result = self.question_chain.run(resume_summary=resume["summary"])
            
            # Try to parse JSON response
            try:
                import json
                questions = json.loads(result)
                if isinstance(questions, list):
                    return questions
                return ["Error parsing questions"]
            except:
                # If JSON parsing fails, return the raw text
                return [q.strip() for q in result.split('\n') if q.strip() and '?' in q]
                
        except Exception as e:
            return [f"Error generating questions: {str(e)}"]
        
        
class FakeResumeDetectorAgent:
    """Agent that detects potentially fake or AI-written resumes"""
    
    def __init__(self):
        self.llm = llm
        
        self.detector_prompt = PromptTemplate(
            input_variables=["resume_text"],
            template="""
            You are an expert at identifying potentially fake or AI-generated resumes.
            Analyze the following resume and look for:
            
            1. Inconsistencies in career timeline
            2. Generic descriptions lacking specific details
            3. Perfect grammar with AI-like writing patterns
            4. Unrealistic combinations of skills or responsibilities
            5. Vague accomplishments without metrics
            
            Resume Text:
            {resume_text}
            
            Provide your analysis as a JSON object with the following structure:
            {{
                "is_suspicious": true/false,
                "confidence_score": 0-100,
                "reasons": ["reason 1", "reason 2"],
                "red_flags": ["specific suspicious text 1", "specific suspicious text 2"]
            }}
            """
        )
        
        self.detector_chain = LLMChain(llm=self.llm, prompt=self.detector_prompt)
    
    def detect_fake_resume(self, resume_text: str) -> Dict:
        """Analyze a resume for signs of being fake or AI-generated"""
        try:
            result = self.detector_chain.run(resume_text=resume_text)
            
            # Try to parse JSON response
            try:
                import json
                analysis = json.loads(result)
                return analysis
            except:
                # If JSON parsing fails, return a basic response
                return {
                    "is_suspicious": False,
                    "confidence_score": 0,
                    "reasons": ["Failed to parse analysis"],
                    "red_flags": []
                }
                
        except Exception as e:
            return {
                "is_suspicious": False,
                "confidence_score": 0,
                "reasons": [f"Error analyzing resume: {str(e)}"],
                "red_flags": []
            }


def setup_agents():
    """Initialize and return the resume store and agents"""
    resume_store = ResumeStore()
    comparator_agent = ResumeComparatorAgent(resume_store)
    gap_identifier_agent = SkillGapIdentifierAgent(resume_store)
    ranker_agent = CandidateRankerAgent(resume_store)
    question_agent = QuestionGeneratorAgent()
    fake_detector_agent = FakeResumeDetectorAgent()
    
    return resume_store, comparator_agent, gap_identifier_agent, ranker_agent, question_agent, fake_detector_agent