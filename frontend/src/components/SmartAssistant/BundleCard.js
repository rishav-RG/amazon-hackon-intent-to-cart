import React, { useState } from 'react';

/**
 * Renders a single bundle as a selectable card with a "View Details" dialog.
 */
const BundleCard = ({ bundle, isRecommended, onSelect, isLoading }) => {
  const [showDetail, setShowDetail] = useState(false);

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
    <>
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

        {/* Items list (compact) */}
        <ul className="space-y-1 mb-3">
          {bundle.items.slice(0, 3).map((item, idx) => (
            <li key={idx} className="flex items-center justify-between text-xs text-gray-700">
              <div className="flex items-center gap-1.5 truncate mr-2">
                <span className="w-5 h-5 rounded bg-gray-100 flex items-center justify-center flex-shrink-0 text-[10px] font-bold text-gray-500">
                  {(item.name || '?').charAt(0).toUpperCase()}
                </span>
                <span className="truncate">
                  {item.name}
                  {item.is_substituted && (
                    <span className="text-orange-600 ml-1">(sub)</span>
                  )}
                </span>
              </div>
              <span className="font-medium whitespace-nowrap">₹{item.unit_price}</span>
            </li>
          ))}
          {bundle.items.length > 3 && (
            <li className="text-xs text-gray-500 italic pl-6">
              +{bundle.items.length - 3} more items...
            </li>
          )}
        </ul>

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-200">
          <div>
            <span className="text-base font-bold text-gray-900">₹{bundle.total_price.toFixed(2)}</span>
            <span className="text-xs text-gray-500 ml-1">({bundle.items.length} items)</span>
          </div>
          <div className="flex gap-1.5">
            <button
              onClick={() => setShowDetail(true)}
              className="bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 text-xs font-medium px-2.5 py-1.5 rounded-lg transition-colors"
            >
              View Details
            </button>
            <button
              onClick={() => onSelect(bundle)}
              disabled={isLoading}
              className="bg-orange-400 hover:bg-orange-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Adding...' : 'Add to Cart'}
            </button>
          </div>
        </div>
      </div>

      {/* Detail Dialog */}
      {showDetail && (
        <BundleDetailDialog
          bundle={bundle}
          isRecommended={isRecommended}
          onClose={() => setShowDetail(false)}
          onAddToCart={() => { setShowDetail(false); onSelect(bundle); }}
          isLoading={isLoading}
        />
      )}
    </>
  );
};

/**
 * Full-screen overlay dialog showing bundle products with images.
 */
const BundleDetailDialog = ({ bundle, isRecommended, onClose, onAddToCart, isLoading }) => {
  const tierIcons = { budget: '💰', classic: '⭐', premium: '👑' };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[80vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Dialog Header */}
        <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-xl">{tierIcons[bundle.bundle_type] || '📦'}</span>
            <div>
              <h3 className="font-bold text-gray-900 text-sm">{bundle.bundle_name}</h3>
              <p className="text-xs text-gray-500">
                {bundle.items.length} items • ₹{bundle.total_price.toFixed(2)}
                {isRecommended && <span className="text-orange-500 ml-1 font-medium">★ Recommended</span>}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none p-1"
            aria-label="Close details"
          >
            ×
          </button>
        </div>

        {/* Product List */}
        <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
          {bundle.items.map((item, idx) => (
            <div key={idx} className="px-5 py-3 flex items-center gap-3">
              {/* Product Image */}
              <div className="w-14 h-14 flex-shrink-0 rounded-lg border border-gray-100 bg-gray-50 overflow-hidden flex items-center justify-center">
                {item.image_url ? (
                  <img
                    src={item.image_url}
                    alt={item.name}
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      // Replace broken image with initials placeholder
                      e.target.style.display = 'none';
                      e.target.parentNode.innerHTML = `<div class="w-full h-full flex items-center justify-center bg-orange-100 text-orange-600 font-bold text-lg">${(item.name || '?').charAt(0).toUpperCase()}</div>`;
                    }}
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-orange-100 text-orange-600 font-bold text-lg">
                    {(item.name || '?').charAt(0).toUpperCase()}
                  </div>
                )}
              </div>

              {/* Product Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 line-clamp-2 leading-tight">
                  {item.name}
                </p>
                <div className="flex items-center gap-2 mt-0.5">
                  {item.brand && (
                    <span className="text-xs text-gray-500">{item.brand}</span>
                  )}
                  {item.category && (
                    <span className="text-xs text-gray-400">• {item.category}</span>
                  )}
                </div>
                {item.is_substituted && (
                  <span className="text-xs text-orange-600 font-medium">↻ Substituted</span>
                )}
                {item.eta_label && (
                  <span className="text-xs text-green-600 ml-1">🚚 {item.eta_label}</span>
                )}
              </div>

              {/* Price & Qty */}
              <div className="text-right flex-shrink-0">
                <p className="text-sm font-bold text-gray-900">₹{item.unit_price}</p>
                <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Dialog Footer */}
        <div className="px-5 py-3 border-t border-gray-200 flex items-center justify-between flex-shrink-0 bg-gray-50">
          <div>
            <p className="text-lg font-bold text-gray-900">₹{bundle.total_price.toFixed(2)}</p>
            <p className="text-xs text-gray-500">{bundle.items.length} items total</p>
          </div>
          <button
            onClick={onAddToCart}
            disabled={isLoading}
            className="bg-orange-500 hover:bg-orange-600 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Adding...' : `Add Bundle to Cart`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default BundleCard;
