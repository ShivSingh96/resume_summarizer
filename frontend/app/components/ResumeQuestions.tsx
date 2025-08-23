import { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ResumeQuestionsProps {
  resumeId: string;
}

export default function ResumeQuestions({ resumeId }: ResumeQuestionsProps) {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [questions, setQuestions] = useState<string[]>([]);
  const [showQuestions, setShowQuestions] = useState<boolean>(false);

  const generateQuestions = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`${API_URL}/generate-questions/${resumeId}`);
      
      // Check if response.data.questions exists and is an array
      if (response.data.questions && Array.isArray(response.data.questions)) {
        setQuestions(response.data.questions);
      } else if (typeof response.data.questions === 'string') {
        // If it's a string, try to parse it as JSON
        try {
          const parsedQuestions = JSON.parse(response.data.questions);
          if (Array.isArray(parsedQuestions)) {
            setQuestions(parsedQuestions);
          } else {
            // If not an array after parsing, create an array with the single item
            setQuestions([response.data.questions]);
          }
        } catch (parseError) {
          // If parsing fails, put the string in an array
          setQuestions([response.data.questions]);
        }
      } else {
        // Fallback to empty array if questions is not defined or not in expected format
        setQuestions([]);
        setError('Received unexpected response format from server');
        console.error('Unexpected questions format:', response.data);
      }
      
      setShowQuestions(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate interview questions. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-6">
      {!showQuestions ? (
        <button
          onClick={generateQuestions}
          disabled={loading}
          className={`px-4 py-2 rounded-md text-white font-medium ${
            loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
          } transition-colors shadow-sm`}
        >
          {loading ? 'Generating...' : 'Generate Interview Questions'}
        </button>
      ) : (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-3">
            <h4 className="text-lg font-semibold text-gray-800">Technical Interview Questions</h4>
            <button
              onClick={() => setShowQuestions(false)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Hide
            </button>
          </div>
          
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-100 shadow-sm">
            {questions.length > 0 ? (
              <>
                <ol className="space-y-6">
                  {questions.map((question, index) => {
                    // Extract question title and context if possible
                    let questionTitle = "";
                    let questionContext = "";
                    
                    // Try to extract "Question X:" pattern
                    const questionMatch = question.match(/^\s*(?:\*\*)?(?:Question\s+\d+:?|Q\d+:?)(?:\*\*)?\s*(.*?)(?:\s*(?:Context:|$))/i);
                    if (questionMatch && questionMatch[1]) {
                      questionTitle = questionMatch[1].trim();
                    }
                    
                    // Try to extract context
                    const contextMatch = question.match(/Context:?\s*(.*?)$/i);
                    if (contextMatch && contextMatch[1]) {
                      questionContext = contextMatch[1].trim();
                    }
                    
                    // If we couldn't parse it, just use the whole question
                    if (!questionTitle) {
                      questionTitle = question;
                    }
                    
                    return (
                      <li key={index} className="bg-white rounded-lg p-4 shadow-sm">
                        <div className="flex items-start">
                          <span className="flex-shrink-0 bg-blue-600 text-white rounded-full h-7 w-7 flex items-center justify-center mr-3 font-medium text-sm">{index + 1}</span>
                          <div className="flex-1">
                            <h5 className="font-medium text-gray-800 mb-2">{questionTitle}</h5>
                            {questionContext && (
                              <div className="mt-2 text-sm text-gray-600 border-t border-gray-100 pt-2">
                                <p className="italic">Context: {questionContext}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ol>
                
                <div className="mt-4 pt-3 border-t border-blue-100 text-sm text-gray-600 italic">
                  These questions are tailored to the candidate's specific experience and skills as mentioned in their resume.
                </div>
              </>
            ) : (
              <div className="text-gray-600 py-4 text-center">
                No questions were generated. Try refreshing or uploading a more detailed resume.
              </div>
            )}
          </div>
        </div>
      )}
      
      {error && (
        <div className="mt-3 p-3 bg-red-50 text-red-700 text-sm rounded-md border border-red-100">
          {error}
        </div>
      )}
    </div>
  );
}
