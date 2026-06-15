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
  <div className="bg-gradient-to-r from-[#111111] via-[#1A1A1A] to-[#232F3E] rounded-xl p-6 mb-6 shadow-lg border border-[#2E2E2E]">
    {/* Title */}
    <div className="flex items-center gap-2 mb-2">
      <span className="text-2xl">🛒</span>
      <h2 className="text-xl font-bold text-white">
        Smart Shopping Assistant
      </h2>
    </div>

    <p className="text-gray-300 text-sm mb-4">
      Tell us what you need, and we'll create personalized product bundles for you!
    </p>

    {/* Search input */}
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g., 'ingredients for pasta dinner', 'supplies for birthday party'"
        className="flex-1 px-4 py-3 rounded-lg bg-white text-gray-900 placeholder-gray-500 border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
      />

      <button
        type="submit"
        className="bg-[#FF9900] hover:bg-[#E68A00] text-black font-semibold px-5 py-3 rounded-lg transition-colors whitespace-nowrap shadow-sm"
      >
        Shop <span className="black">⚡</span>
      </button>
    </form>

    {/* Example queries */}
    <div className="mt-3 flex flex-wrap gap-1.5">
      <span className="text-gray-400 text-xs">
        Try these examples:
      </span>

      {examples.map((ex) => (
        <button
          key={ex}
          onClick={() => {
            setQuery(ex);
            if (onSearch) onSearch(ex);
          }}
          className="text-xs bg-[#2A2A2A] hover:bg-[#3A3A3A] text-gray-200 px-2 py-0.5 rounded-full border border-[#404040] transition-colors"
        >
          "{ex}"
        </button>
      ))}
    </div>
  </div>
);
};

export default SmartSearchBanner;
