'use client';

import { useEffect } from 'react';
import { useJobStatus, useCancelJob } from '@/lib/api';

interface JobStatusProps {
  jobId: string;
  onJobComplete: (results: Record<string, unknown>) => void;
  onJobCancel: () => void;
}

export function JobStatus({ jobId, onJobComplete, onJobCancel }: JobStatusProps) {
  const { data: job, isLoading, error } = useJobStatus(jobId);
  const cancelMutation = useCancelJob();

  // Handle job completion - use useEffect to avoid calling setState during render
  useEffect(() => {
    if (job?.status === 'completed' && job.results) {
      onJobComplete(job.results);
    }
  }, [job?.status, job?.results, onJobComplete]);

  const handleCancel = async () => {
    try {
      await cancelMutation.mutateAsync(jobId);
      onJobCancel();
    } catch (error) {
      console.error('Failed to cancel job:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'processing':
        return 'text-blue-600 bg-blue-100';
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'processing':
        return '⚙️';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '❓';
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
        <div className="text-red-600">
          <h3 className="text-lg font-medium mb-2">Error Loading Job Status</h3>
          <p className="text-sm">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
        <div className="text-gray-600">
          <h3 className="text-lg font-medium">Job not found</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Analysis Status</h2>
        {(job.status === 'pending' || job.status === 'processing') && (
          <button
            onClick={handleCancel}
            disabled={cancelMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-red-600 border border-red-300 rounded-md hover:bg-red-50 disabled:opacity-50"
          >
            {cancelMutation.isPending ? 'Cancelling...' : 'Cancel'}
          </button>
        )}
      </div>

      {/* Job Info */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Job ID</label>
          <div className="mt-1 text-sm text-gray-600 font-mono">{jobId}</div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Status</label>
          <div className="mt-1">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
              <span className="mr-2">{getStatusIcon(job.status)}</span>
              {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
            </span>
          </div>
        </div>

        {/* Progress indicator for active jobs */}
        {(job.status === 'pending' || job.status === 'processing') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Progress</label>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-in-out"
                style={{ 
                  width: job.status === 'pending' ? '10%' : '60%',
                  animation: job.status === 'processing' ? 'pulse 2s infinite' : 'none'
                }}
              ></div>
            </div>
            <div className="mt-2 text-sm text-gray-600">
              {job.status === 'pending' ? 'Queued for processing...' : 'Analyzing video...'}
            </div>
          </div>
        )}

        {/* Error display */}
        {job.status === 'failed' && job.error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <h4 className="text-sm font-medium text-red-800 mb-2">Error Details</h4>
            <p className="text-sm text-red-700">{job.error}</p>
          </div>
        )}

        {/* Success message */}
        {job.status === 'completed' && (
          <div className="p-4 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center">
              <span className="text-green-600 mr-2">✅</span>
              <span className="text-sm font-medium text-green-800">
                Analysis completed successfully!
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}