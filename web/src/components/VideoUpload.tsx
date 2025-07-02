'use client';

import { useState, useCallback } from 'react';
import { useUploadVideo, useApiInfo } from '@/lib/api';

interface VideoUploadProps {
  onUploadSuccess: (jobId: string) => void;
}

export function VideoUpload({ onUploadSuccess }: VideoUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedAnalyses, setSelectedAnalyses] = useState<string[]>(['multimodal']);
  const [dragActive, setDragActive] = useState(false);

  const uploadMutation = useUploadVideo();
  const { data: apiInfo } = useApiInfo();

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('video/')) {
        setSelectedFile(file);
      }
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const handleAnalysisToggle = (analysis: string) => {
    setSelectedAnalyses(prev => 
      prev.includes(analysis)
        ? prev.filter(a => a !== analysis)
        : [...prev, analysis]
    );
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const result = await uploadMutation.mutateAsync({
        file: selectedFile,
        analyses: selectedAnalyses
      });
      onUploadSuccess(result.job_id);
      setSelectedFile(null);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Upload Video for Analysis</h2>
      
      {/* File Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          <div className="space-y-2">
            <div className="text-lg font-medium text-gray-900">{selectedFile.name}</div>
            <div className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</div>
            <button
              onClick={() => setSelectedFile(null)}
              className="text-red-600 hover:text-red-800 text-sm"
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-xl text-gray-600">
              Drag and drop your video file here
            </div>
            <div className="text-sm text-gray-500">
              or click to select a file
            </div>
            <input
              type="file"
              accept="video/*"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
            >
              Select Video File
            </label>
          </div>
        )}
      </div>

      {/* Analysis Selection */}
      <div className="mt-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Select Analysis Types</h3>
        <div className="space-y-2">
          {apiInfo?.supported_analyses?.map((analysis) => (
            <label key={analysis} className="flex items-center space-x-3">
              <input
                type="checkbox"
                checked={selectedAnalyses.includes(analysis)}
                onChange={() => handleAnalysisToggle(analysis)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="text-gray-700 capitalize">{analysis}</span>
              {apiInfo?.analysis_descriptions?.[analysis] && (
                <span className="text-sm text-gray-500">
                  - {apiInfo.analysis_descriptions[analysis]}
                </span>
              )}
            </label>
          )) || (
            <div className="space-y-2">
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={selectedAnalyses.includes('multimodal')}
                  onChange={() => handleAnalysisToggle('multimodal')}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-gray-700">Multimodal Analysis</span>
              </label>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={selectedAnalyses.includes('structured')}
                  onChange={() => handleAnalysisToggle('structured')}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-gray-700">Structured Analysis</span>
              </label>
            </div>
          )}
        </div>
      </div>

      {/* Upload Button */}
      <div className="mt-6">
        <button
          onClick={handleUpload}
          disabled={!selectedFile || selectedAnalyses.length === 0 || uploadMutation.isPending}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploadMutation.isPending ? 'Uploading...' : 'Start Analysis'}
        </button>
      </div>

      {/* Error Display */}
      {uploadMutation.error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="text-sm text-red-800">
            Upload failed: {uploadMutation.error.message}
          </div>
        </div>
      )}
    </div>
  );
}