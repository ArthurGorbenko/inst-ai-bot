'use client';

import { useState, useCallback } from 'react';
import { VideoUpload } from '@/components/VideoUpload';
import { JobStatus } from '@/components/JobStatus';
import { ResultsViewer } from '@/components/ResultsViewer';
import { useHealth } from '@/lib/api';

type AppState = 'upload' | 'processing' | 'results';

export default function Home() {
  const [appState, setAppState] = useState<AppState>('upload');
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, unknown> | null>(null);

  const { data: health } = useHealth();

  const handleUploadSuccess = (jobId: string) => {
    setCurrentJobId(jobId);
    setAppState('processing');
  };

  const handleJobComplete = useCallback((jobResults: Record<string, unknown>) => {
    setResults(jobResults);
    setAppState('results');
  }, []);

  const handleJobCancel = () => {
    setCurrentJobId(null);
    setAppState('upload');
  };

  const handleNewAnalysis = () => {
    setCurrentJobId(null);
    setResults(null);
    setAppState('upload');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Video Analysis System
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              {health && (
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  health.status === 'healthy' 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  <span className="w-1.5 h-1.5 bg-current rounded-full mr-1"></span>
                  {health.status === 'healthy' ? 'Server Online' : 'Server Offline'}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {appState === 'upload' && (
          <VideoUpload onUploadSuccess={handleUploadSuccess} />
        )}

        {appState === 'processing' && currentJobId && (
          <JobStatus
            jobId={currentJobId}
            onJobComplete={handleJobComplete}
            onJobCancel={handleJobCancel}
          />
        )}

        {appState === 'results' && results && (
          <ResultsViewer
            results={results}
            onNewAnalysis={handleNewAnalysis}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-500">
            Video Analysis System - Powered by AI
          </div>
        </div>
      </footer>
    </div>
  );
}