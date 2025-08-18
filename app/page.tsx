"use client";

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

// Import all components
import ResumeManager from './components/ResumeManager';
import JobDescriptionForm from './components/JobDescriptionForm';
import JobMatcher from './components/JobMatcher';
import FakeDetector from './components/FakeDetector';

const API_URL = 'http://localhost:8000';

interface FileWithPreview extends File {
  preview?: string;
}

export default function Home() {
  const [file, setFile] = useState<FileWithPreview | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [summary, setSummary] = useState<string>('');
  const [view, setView] = useState<'upload' | 'manage' | 'job-description' | 'job-matcher' | 'fake-detector'>('upload');
  const [selectedResumeIds, setSelectedResumeIds] = useState<string[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0] as FileWithPreview);
      setError('');
      setSummary('');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    maxFiles: 1
  });

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a resume file first.');
      return;
    }

    setLoading(true);
    setError('');
    setSummary('');

    try {
      // Step 1: Upload the file
      const formData = new FormData();
      formData.append('file', file);

      const uploadResponse = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const { file_id } = uploadResponse.data;

      // Step 2: Request summary
      const summaryResponse = await axios.post(`${API_URL}/summarize`, {
        file_id: file_id,
        model: 'llama3'
      });

      setSummary(summaryResponse.data.summary);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error processing resume. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handler for selecting resumes in the ResumeManager
  const handleResumeSelection = (ids: string[]) => {
    setSelectedResumeIds(ids);
  };

  return (
    <main className="min-h-screen p-8 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Resume Analyzer</h1>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-6 overflow-x-auto">
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <button
              onClick={() => setView('upload')}
              className={`px-4 py-2 text-sm font-medium ${
                view === 'upload' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
              style={{borderTopLeftRadius: '0.375rem', borderBottomLeftRadius: '0.375rem'}}
            >
              Upload Resume
            </button>
            <button
              onClick={() => setView('manage')}
              className={`px-4 py-2 text-sm font-medium ${
                view === 'manage' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Manage Resumes
            </button>
            <button
              onClick={() => setView('job-description')}
              className={`px-4 py-2 text-sm font-medium ${
                view === 'job-description' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Job Description
            </button>
            <button
              onClick={() => setView('job-matcher')}
              className={`px-4 py-2 text-sm font-medium ${
                view === 'job-matcher' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Job Matcher
            </button>
            <button
              onClick={() => setView('fake-detector')}
              className={`px-4 py-2 text-sm font-medium ${
                view === 'fake-detector' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
              style={{borderTopRightRadius: '0.375rem', borderBottomRightRadius: '0.375rem'}}
            >
              Fake Detector
            </button>
          </div>
        </div>
        
        {/* Upload Resume View */}
        {view === 'upload' && (
          <>
            <div className="bg-white p-6 rounded-lg shadow-md mb-8">
              <div 
                {...getRootProps()} 
                className={`border-2 border-dashed p-8 rounded-lg text-center cursor-pointer transition-colors ${
                  isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
                }`}
              >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center">
                  <svg 
                    className="w-12 h-12 text-gray-400 mb-4" 
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
                      <p className="text-base font-medium text-gray-900">
                        Drop your resume here, or <span className="text-blue-500">browse</span>
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        Supports PDF, DOCX, and TXT files
                      </p>
                    </div>
                  )}
                </div>
              </div>
              
              {file && (
                <div className="mt-4 flex justify-center">
                  <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className={`px-4 py-2 rounded-md text-white font-medium ${
                      loading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
                    } transition-colors`}
                  >
                    {loading ? 'Analyzing...' : 'Analyze Resume'}
                  </button>
                </div>
              )}
              
              {error && (
                <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md">
                  {error}
                </div>
              )}
            </div>
            
            {summary && (
              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold">🧑‍💼 Candidate Summary</h2>
                  <div className="flex space-x-2">
                    <button 
                      className="flex items-center text-sm text-green-600 bg-green-50 hover:bg-green-100 px-3 py-1 rounded-md"
                      onClick={() => {
                        axios.post(`${API_URL}/feedback`, {
                          resume_id: file?.name,
                          is_positive: true
                        }).then(() => {
                          alert('Thanks for your feedback!');
                        }).catch(err => {
                          console.error('Feedback error:', err);
                        });
                      }}
                    >
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                        <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"></path>
                      </svg>
                      Helpful
                    </button>
                    <button 
                      className="flex items-center text-sm text-red-600 bg-red-50 hover:bg-red-100 px-3 py-1 rounded-md"
                      onClick={() => {
                        axios.post(`${API_URL}/feedback`, {
                          resume_id: file?.name,
                          is_positive: false
                        }).then(() => {
                          alert('Thanks for your feedback!');
                        }).catch(err => {
                          console.error('Feedback error:', err);
                        });
                      }}
                    >
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                        <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"></path>
                      </svg>
                      Not Helpful
                    </button>
                  </div>
                </div>
                <div className="prose max-w-none">
                  {summary.split('\n').map((line, index) => (
                    <div key={index}>
                      {line.trim() ? (
                        line.startsWith('**') ? (
                          <h3 className="font-bold text-lg mt-4 mb-2">{line.replace(/\*\*/g, '')}</h3>
                        ) : line.startsWith('•') || line.startsWith('-') ? (
                          <p className="ml-4 my-1">{line}</p>
                        ) : (
                          <p className="my-2">{line}</p>
                        )
                      ) : (
                        <br />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        
        {/* Manage Resumes View */}
        {view === 'manage' && (
          <ResumeManager onSelectResumes={handleResumeSelection} />
        )}

        {/* Job Description View */}
        {view === 'job-description' && (
          <JobDescriptionForm resumeIds={selectedResumeIds} />
        )}

        {/* Job Matcher View */}
        {view === 'job-matcher' && (
          <JobMatcher />
        )}

        {/* Fake Detector View */}
        {view === 'fake-detector' && (
          <FakeDetector />
        )}
      </div>
    </main>
  );
}