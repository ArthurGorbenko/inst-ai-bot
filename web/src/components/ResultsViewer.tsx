'use client';

import { useState } from 'react';

interface ResultsViewerProps {
  results: Record<string, unknown>;
  onNewAnalysis: () => void;
}

export function ResultsViewer({ results, onNewAnalysis }: ResultsViewerProps) {
  const [selectedAnalysis, setSelectedAnalysis] = useState<string>(
    Object.keys(results)[0] || ''
  );

  const analysisTypes = Object.keys(results);

  const formatValue = (value: unknown): string => {
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const renderResultSection = (key: string, value: unknown) => {
    const isObject = typeof value === 'object' && value !== null;
    
    return (
      <div key={key} className="mb-6">
        <h4 className="text-lg font-medium text-gray-900 mb-3 capitalize">
          {key.replace(/_/g, ' ')}
        </h4>
        
        {isObject ? (
          <div className="bg-gray-50 rounded-lg p-4">
            {Array.isArray(value) ? (
              <div className="space-y-2">
                {value.map((item, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4">
                    <div className="text-sm text-gray-600">Item {index + 1}</div>
                    <div className="text-gray-800">{formatValue(item)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <pre className="text-sm text-gray-800 whitespace-pre-wrap overflow-x-auto">
                {formatValue(value)}
              </pre>
            )}
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-gray-800 whitespace-pre-wrap">{formatValue(value)}</div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
        <button
          onClick={onNewAnalysis}
          className="px-4 py-2 text-sm font-medium text-blue-600 border border-blue-300 rounded-md hover:bg-blue-50"
        >
          New Analysis
        </button>
      </div>

      {/* Analysis Type Tabs */}
      {analysisTypes.length > 1 && (
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {analysisTypes.map((type) => (
                <button
                  key={type}
                  onClick={() => setSelectedAnalysis(type)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    selectedAnalysis === type
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {type.charAt(0).toUpperCase() + type.slice(1)} Analysis
                </button>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Results Content */}
      <div className="space-y-6">
        {selectedAnalysis && results[selectedAnalysis] ? (
          (() => {
            const analysisData = results[selectedAnalysis];
            
            if (typeof analysisData === 'object' && analysisData !== null) {
              return Object.entries(analysisData).map(([key, value]) =>
                renderResultSection(key, value)
              );
            } else {
              return renderResultSection(selectedAnalysis, analysisData);
            }
          })()
        ) : (
          <div className="text-center py-8 text-gray-500">
            No results available for the selected analysis type.
          </div>
        )}
      </div>

      {/* Raw Data Toggle */}
      <details className="mt-8">
        <summary className="cursor-pointer text-sm font-medium text-gray-600 hover:text-gray-800">
          View Raw JSON Data
        </summary>
        <div className="mt-4 bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto">
          <pre className="text-xs">
            {JSON.stringify(results, null, 2)}
          </pre>
        </div>
      </details>
    </div>
  );
}