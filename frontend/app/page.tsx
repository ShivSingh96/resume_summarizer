"use client";

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

// Import all components
import ResumeManager from './components/ResumeManager';
import JobMatcher from './components/JobMatcher';
import FakeDetector from './components/FakeDetector';

// Import UI components
import Header from './components/ui/Header';
import Navigation from './components/ui/Navigation';
import Card from './components/ui/Card';
import Button from './components/ui/Button';

const API_URL = 'http://localhost:8000';

interface FileWithPreview extends File {
  preview?: string;
}

export default function Home() {
  const [file, setFile] = useState<FileWithPreview | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [summary, setSummary] = useState<string>('');
  const [view, setView] = useState<'upload' | 'manage' | 'job-matcher' | 'fake-detector'>('upload');
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

  const navigationViews = [
    { id: 'upload', label: 'Upload Resume' },
    { id: 'manage', label: 'Manage Resumes' },
    { id: 'job-matcher', label: 'Job Matcher' },
    { id: 'fake-detector', label: 'Fake Detector' }
  ];

  return (
    <main className="min-h-screen p-4 md:p-8 bg-gradient-to-b from-gray-50 to-gray-100">
      <div className="max-w-5xl mx-auto">
        <Header 
          title="Resume Analyzer" 
          subtitle="AI-powered resume analysis and candidate evaluation" 
        />

        {/* Navigation Tabs */}
        <Navigation 
          activeView={view}
          onViewChange={(v) => setView(v as any)}
          views={navigationViews}
        />
        
        {/* Upload Resume View */}
        {view === 'upload' && (
          <>
            <Card variant="elevated" className="mb-8">
              <div 
                {...getRootProps()} 
                className={`border-2 border-dashed p-8 rounded-lg text-center cursor-pointer transition-all duration-300 ${
                  isDragActive ? 'border-blue-500 bg-blue-50 shadow-inner' : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50/30'
                }`}
              >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center">
                  <svg 
                    className={`w-16 h-16 mb-4 transition-colors duration-300 ${
                      isDragActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-blue-500'
                    }`}
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
                        Drop your resume here, or <span className="text-blue-600 hover:text-blue-800 transition-colors">browse</span>
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
                  <Button
                    onClick={handleSubmit}
                    disabled={loading}
                    variant="primary"
                    size="md"
                  >
                    {loading ? 'Analyzing...' : 'Analyze Resume'}
                  </Button>
                </div>
              )}
              
              {error && (
                <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 shadow-sm flex items-center">
                  <svg className="w-5 h-5 mr-2 text-red-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {error}
                </div>
              )}
            </Card>
            
            {summary && (
              <Card variant="elevated" title="🧑‍💼 Candidate Summary">
                <div className="prose max-w-none prose-headings:text-blue-800 prose-p:text-gray-700 prose-strong:text-gray-900">
                  {summary.split('\n').map((line, index) => (
                    <div key={index}>
                      {line.trim() ? (
                        line.startsWith('**') ? (
                          <h3 className="font-bold text-lg mt-6 mb-3 text-indigo-700 border-b border-gray-100 pb-1">{line.replace(/\*\*/g, '')}</h3>
                        ) : line.startsWith('•') || line.startsWith('-') ? (
                          <p className="ml-4 my-1 flex items-start">
                            <span className="text-blue-500 mr-2 inline-block">•</span>
                            <span>{line.replace(/^[•-]\s*/, '')}</span>
                          </p>
                        ) : (
                          <p className="my-2">{line}</p>
                        )
                      ) : (
                        <br />
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </>
        )}
        
        {/* Manage Resumes View */}
        {view === 'manage' && (
          <ResumeManager onSelectResumes={handleResumeSelection} />
        )}

        {/* Job Description View */}
        {/* Job Description section removed as it was redundant */}

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
