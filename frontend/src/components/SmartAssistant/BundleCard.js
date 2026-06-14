import React from 'react';

/**
 * Renders a single bundle as a selectable card.
 */
const BundleCard = ({ bundle, isRecommended, onSelect, isLoading }) => {
  const tierColors = {
    budget: 'border-green-400 bg-green-50',
    classic: 'border-blue-400 bg-blue-50',
    premium: 'border-purple-400 bg-purple-50',
  };

  const tierIcons = {
    budget: '💰',
    classic: '⭐',
    premium: '👑',
  };

  const borderColor = tierColors[bundle.bundle_type] || 'border-gray-300 bg-gray-50';

  return (
    <div
      className={`border-2 rounded-xl p-3 ${borderColor} ${
        isRecommended ? 'ring-2 ring-orange-400' : ''
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <span className="text-lg">{tierIcons[bundle.bundle_type] || '📦'}</span>
          <span className="font-semibold text-sm text-gray-900">{bundle.bundle_name}</span>
        </div>
        {isRecommended && (
          <span className="bg-orange-400 text-white text-xs px-2 py-0.5 rounded-full font-medium">
            Recommended
          </span>
        )}
      </div>

      {/* Items list */}
      <ul className="space-y-1 mb-3">
        {bundle.items.map((item, idx) => (
          <li key={idx} className="flex justify-between text-xs text-gray-700">
            <span className="truncate mr-2">
              • {item.name}
              {item.is_substituted && (
                <span className="text-orange-600 ml-1">(substituted)</span>
              )}
            </span>
            <span className="font-medium whitespace-nowrap">₹{item.unit_price}</span>
          </li>
        ))}
      </ul>

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-gray-200">
        <div>
          <span className="text-base font-bold text-gray-900">₹{bundle.total_price.toFixed(2)}</span>
          <span className="text-xs text-gray-500 ml-1">({bundle.items.length} items)</span>
        </div>
        <button
          onClick={() => onSelect(bundle)}
          disabled={isLoading}
          className="bg-orange-400 hover:bg-orange-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Adding...' : 'Add to Cart'}
        </button>
      </div>
    </div>
  );
};

export default BundleCard;
