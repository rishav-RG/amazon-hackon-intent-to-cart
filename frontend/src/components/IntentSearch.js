import React, { useState } from 'react';
import { useCart } from '../context/CartContext';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const IntentSearch = () => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const { addToCart } = useCart();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setIsOpen(true);

    try {
      const response = await fetch(`${API_BASE}/v1/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': 'demo-user-1',
        },
        body: JSON.stringify({ query: query.trim() }),
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = (product) => {
    addToCart({
      id: product.product_id,
      title: product.name,
      price: product.discount_price || product.price,
      image: product.image_url,
    });
  };

  const handleAddBundle = (bundle) => {
    bundle.items.forEach((product) => {
      handleAddProduct(product);
    });
  };

  const getTierLabel = (tier) => {
    switch (tier) {
      case 'budget': return '💰 Budget';
      case 'classic': return '⭐ Classic (Recommended)';
      case 'premium': return '👑 Premium';
      default: return tier;
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'budget': return 'border-green-400 bg-green-50';
      case 'classic': return 'border-orange-400 bg-orange-50';
      case 'premium': return 'border-purple-400 bg-purple-50';
      default: return 'border-gray-300';
    }
  };

  return (
    <div className="relative w-full">
      {/* Search Input */}
      <form onSubmit={handleSearch} className="flex w-full">
        <input
          type="text"
          placeholder="Try: 'I need baby shampoo' or 'party snacks for 10 people'"
          className="flex-1 px-4 py-2 text-gray-900 focus:outline-none text-sm rounded-l-md"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results && setIsOpen(true)}
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-orange-400 hover:bg-orange-500 px-4 py-2 rounded-r-md disabled:opacity-50"
        >
          {loading ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          )}
        </button>
      </form>

      {/* Results Panel (dropdown) */}
      {isOpen && (results || loading || error) && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-2xl border border-gray-200 max-h-[80vh] overflow-y-auto z-50">
          {/* Close button */}
          <div className="sticky top-0 bg-white border-b px-4 py-2 flex justify-between items-center">
            <span className="text-sm text-gray-600">
              {results ? `${results.total_results} products found` : 'Searching...'}
            </span>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Loading */}
          {loading && (
            <div className="p-8 text-center">
              <svg className="w-8 h-8 animate-spin mx-auto text-orange-400" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p className="mt-2 text-gray-600">AI is finding the best products for you...</p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="p-4 bg-red-50 text-red-700 text-sm">
              <p className="font-medium">Search failed</p>
              <p>{error}</p>
            </div>
          )}

          {/* Results */}
          {results && !loading && (
            <div className="p-4">
              {/* Intent Badge */}
              <div className="mb-4 flex items-center gap-2 flex-wrap">
                <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                  Intent: {results.intent.intent_type.replace('_', ' ')}
                </span>
                <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                  Confidence: {(results.intent.confidence * 100).toFixed(0)}%
                </span>
                {results.intent.llm_used && (
                  <span className="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded">
                    AI-powered
                  </span>
                )}
              </div>

              {/* Bundles */}
              {results.bundles.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">
                    Smart Bundles for You
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {results.bundles.map((bundle) => (
                      <div
                        key={bundle.tier}
                        className={`border-2 rounded-lg p-3 ${getTierColor(bundle.tier)}`}
                      >
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-medium">{getTierLabel(bundle.tier)}</span>
                          <span className="text-sm font-bold">Rs.{bundle.total.toFixed(0)}</span>
                        </div>
                        <ul className="text-xs text-gray-600 space-y-1 mb-3">
                          {bundle.items.map((item) => (
                            <li key={item.product_id} className="truncate">
                              {item.name} - Rs.{item.price}
                            </li>
                          ))}
                        </ul>
                        <button
                          onClick={() => handleAddBundle(bundle)}
                          className="w-full bg-orange-400 hover:bg-orange-500 text-xs font-medium py-1.5 rounded"
                        >
                          Add Bundle to Cart
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Individual Products */}
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                All Matching Products
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {results.products.map((product) => (
                  <div key={product.product_id} className="border rounded-lg p-2 hover:shadow-md transition-shadow">
                    {product.image_url && (
                      <img
                        src={product.image_url}
                        alt={product.name}
                        className="w-full h-24 object-cover rounded mb-2"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    )}
                    <p className="text-xs font-medium text-gray-900 line-clamp-2 mb-1">
                      {product.name}
                    </p>
                    <p className="text-xs text-gray-500 mb-1">{product.brand}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-gray-900">
                        Rs.{product.discount_price || product.price}
                      </span>
                      {product.discount_price && product.discount_price < product.price && (
                        <span className="text-xs text-gray-400 line-through">
                          Rs.{product.price}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleAddProduct(product)}
                      className="w-full mt-2 bg-yellow-400 hover:bg-yellow-500 text-xs font-medium py-1.5 rounded"
                    >
                      Add to Cart
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default IntentSearch;
