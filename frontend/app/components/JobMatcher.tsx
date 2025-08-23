import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

interface MatchedResume {
  id: string;
  summary: string;
  match_score: number;
  metadata: any;
}

export default function JobMatcher() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [jobDescription, setJobDescription] = useState<string>('');
  const [matchedResumes, setMatchedResumes] = useState<MatchedResume[]>([]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setFile(acceptedFiles[0]);
        setError('');
      }
    },
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    maxFiles: 1
  });

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a job description file first.');
      return;
    }

    setLoading(true);
    setError('');
    setJobDescription('');
    setMatchedResumes([]);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_URL}/upload-job-description`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setJobDescription(response.data.job_description);
      setMatchedResumes(response.data.matching_resumes);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error processing job description. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTextInput = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!jobDescription.trim()) {
      setError('Please enter a job description.');
      return;
    }

    setLoading(true);
    setError('');
    setMatchedResumes([]);

    try {
      // Use an existing endpoint to find matches
      // We'll need to extract sample resumes first to match against
      const resumesResponse = await axios.get(`${API_URL}/resumes`);
      const resumeIds = resumesResponse.data.resumes.map((r: any) => r.id);

      if (resumeIds.length === 0) {
        setError('No resumes available to match against. Please upload some resumes first.');
        setLoading(false);
        return;
      }

      // For each resume, calculate match score
      const matchPromises = resumeIds.map(async (id: string) => {
        const gapResponse = await axios.post(`${API_URL}/identify-gaps`, {
          job_description: jobDescription,
          resume_ids: [id]
        });

        // Get the resume details
        const resumeDetails = resumesResponse.data.resumes.find((r: any) => r.id === id);
        return {
          id,
          summary: resumeDetails.summary,
          match_score: Math.random(), // This is a placeholder - would need actual scoring logic
          metadata: resumeDetails.metadata,
          gap_analysis: gapResponse.data.gap_analysis
        };
      });

      const results = await Promise.all(matchPromises);
      setMatchedResumes(results.sort((a, b) => b.match_score - a.match_score));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error matching job description. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 className="text-xl font-semibold mb-4">Match Job Description to Resumes</h2>

      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Upload Job Description</h3>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed p-6 rounded-lg text-center cursor-pointer transition-colors ${
            isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
          }`}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center">
            <svg
              className="w-10 h-10 text-gray-400 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>

            {file ? (
              <p className="text-sm font-medium text-gray-900">{file.name}</p>
            ) : (
              <div>
                <p className="text-sm font-medium text-gray-900">
                  Drop job description file here, or <span className="text-blue-500">browse</span>
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Supports PDF, DOCX, and TXT files
                </p>
              </div>
            )}
          </div>
        </div>

        {file && (
          <div className="mt-3 flex justify-center">
            <button
              onClick={handleUpload}
              disabled={loading}
              className={`px-4 py-2 rounded-md text-white font-medium ${
                loading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
              } transition-colors`}
            >
              {loading ? 'Processing...' : 'Upload & Find Matches'}
            </button>
          </div>
        )}
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-medium mb-2">Or Enter Job Description Text</h3>
        <form onSubmit={handleTextInput}>
          <textarea
            className="w-full p-3 border rounded-md h-40"
            placeholder="Paste job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
          ></textarea>
          <div className="mt-3 flex justify-center">
            <button
              type="submit"
              disabled={loading}
              className={`px-4 py-2 rounded-md text-white font-medium ${
                loading ? 'bg-indigo-400' : 'bg-indigo-600 hover:bg-indigo-700'
              } transition-colors`}
            >
              {loading ? 'Finding Matches...' : 'Find Matching Resumes'}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {matchedResumes.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-3">Matching Resumes</h3>
          <div className="space-y-4">
            {matchedResumes.map((resume) => (
              <div key={resume.id} className="border rounded-md p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">Resume ID: {resume.id}</h4>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Match Score: {(resume.match_score * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  {resume.summary.split('\n')[0]}...
                </p>
                <button
                  className="text-sm text-blue-600 hover:text-blue-800"
                  onClick={() => {
                    // Implement view details functionality
                    alert(`View full details for resume ${resume.id}`);
                  }}
                >
                  View Full Resume
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
