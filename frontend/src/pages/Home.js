import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import ProductGrid from '../components/ProductGrid';
import IntentSearch from '../components/IntentSearch';
import BundleDisplay from '../components/BundleDisplay';

const Home = ({ searchQuery, searchCategory }) => {
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [bundleData, setBundleData] = useState(null);
  const [showBundles, setShowBundles] = useState(false);
  const [error, setError] = useState(null);

  const handleCategoryFilter = (filter) => {
    setCategoryFilter(filter);
  };

  const handleBundlesReceived = (data) => {
    setBundleData(data);
    setShowBundles(true);
    setError(null);
  };

  const handleError = (err) => {
    setError(err.message || 'Failed to fetch bundles. Make sure the backend is running.');
    setShowBundles(false);
  };

  const handleBackToProducts = () => {
    setShowBundles(false);
    setBundleData(null);
    setError(null);
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar onCategoryFilter={handleCategoryFilter} />
      
      {/* Main Content */}
      <div className="flex-1 lg:ml-0 p-6">
        {/* Intent Search Component */}
        <IntentSearch 
          onBundlesReceived={handleBundlesReceived}
          onError={handleError}
        />

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Connection Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                  <p className="mt-1">Make sure your backend server is running on http://localhost:8000</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Toggle between Bundles and Regular Products */}
        {showBundles && bundleData && (
          <div className="mb-4">
            <button
              onClick={handleBackToProducts}
              className="text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-2"
            >
              ← Back to all products
            </button>
          </div>
        )}

        {/* Bundle Display or Product Grid */}
        {showBundles && bundleData ? (
          <BundleDisplay bundleData={bundleData} />
        ) : (
          <ProductGrid 
            categoryFilter={categoryFilter} 
            onClearFilter={handleCategoryFilter}
            searchQuery={searchQuery}
            searchCategory={searchCategory}
          />
        )}
      </div>
    </div>
  );
};

export default Home;