import React, { useState } from 'react';

/**
 * Hero banner with inline smart search bar.
 * Typing and pressing Enter opens the floating chat assistant.
 */
const SmartSearchBanner = ({ onSearch }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && onSearch) {
      onSearch(query.trim());
      setQuery('');
    }
  };

  const examples = [
    'meal prep for the week',
    'cleaning supplies',
    'baby essentials',
    'pet food and toys',
  ];

  return (
    <div className="bg-gradient-to-r from-purple-700 via-purple-600 to-indigo-600 rounded-xl p-6 mb-6 shadow-md">
      {/* Title */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-2xl">🛒</span>
        <h2 className="text-xl font-bold text-white">Smart Shopping Assistant</h2>
      </div>
      <p className="text-purple-100 text-sm mb-4">
        Tell us what you need, and we'll create personalized product bundles for you!
      </p>

      {/* Search input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., 'ingredients for pasta dinner', 'supplies for birthday party'"
          className="flex-1 px-4 py-3 rounded-lg text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-400"
        />
        <button
          type="submit"
          className="bg-orange-500 hover:bg-orange-600 text-white font-semibold px-5 py-3 rounded-lg transition-colors whitespace-nowrap"
        >
          Find Bundles
        </button>
      </form>

      {/* Example queries */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        <span className="text-purple-200 text-xs">Try these examples:</span>
        {examples.map((ex) => (
          <button
            key={ex}
            onClick={() => { setQuery(ex); if (onSearch) onSearch(ex); }}
            className="text-xs bg-purple-800/50 hover:bg-purple-800 text-purple-100 px-2 py-0.5 rounded-full transition-colors"
          >
            "{ex}"
          </button>
        ))}
      </div>
    </div>
  );
};

export default SmartSearchBanner;
