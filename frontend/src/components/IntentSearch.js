import React, { useState } from 'react';
import { searchAndGetBundles } from '../services/intentService';

const IntentSearch = ({ onBundlesReceived, onError }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [confidence, setConfidence] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      return;
    }

    setLoading(true);
    setConfidence(null);

    try {
      const result = await searchAndGetBundles(searchQuery);
      
      // Update confidence display
      setConfidence(result.confidence);
      
      // Pass bundles to parent component
      if (onBundlesReceived) {
        onBundlesReceived(result);
      }
    } catch (error) {
      console.error('Search failed:', error);
      if (onError) {
        onError(error);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="intent-search-container bg-gradient-to-r from-blue-500 to-purple-600 p-6 rounded-lg shadow-lg mb-6">
      <h2 className="text-white text-2xl font-bold mb-4">
        🛒 Smart Shopping Assistant
      </h2>
      <p className="text-white text-sm mb-4">
        Tell us what you need, and we'll create personalized product bundles for you!
      </p>
      
      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="e.g., 'ingredients for pasta dinner', 'supplies for birthday party'"
          className="flex-1 px-4 py-3 rounded-lg border-2 border-white focus:outline-none focus:ring-2 focus:ring-yellow-400"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold px-8 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Finding...
            </span>
          ) : (
            'Find Bundles'
          )}
        </button>
      </form>

      {confidence !== null && (
        <div className="mt-4 bg-white bg-opacity-20 rounded-lg p-3">
          <div className="flex items-center justify-between text-white text-sm">
            <span>Understanding Confidence:</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-white bg-opacity-30 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${confidence >= 0.7 ? 'bg-green-400' : 'bg-yellow-400'}`}
                  style={{ width: `${confidence * 100}%` }}
                />
              </div>
              <span className="font-bold">{(confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      )}

      <div className="mt-3 text-white text-xs">
        <strong>Try these examples:</strong> "meal prep for the week" • "cleaning supplies" • "baby essentials" • "pet food and toys"
      </div>
    </div>
  );
};

export default IntentSearch;
