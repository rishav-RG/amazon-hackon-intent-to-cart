import React from 'react';
import { useCart } from '../context/CartContext';

const BundleDisplay = ({ bundleData }) => {
  const { addToCart } = useCart();

  if (!bundleData || !bundleData.bundles) {
    return null;
  }

  const { recommended, options } = bundleData.bundles;

  const handleAddBundleToCart = (bundle) => {
    // Add all items from the bundle to cart
    bundle.items.forEach(item => {
      for (let i = 0; i < item.quantity; i++) {
        addToCart({
          id: item.product_id,
          title: item.name,
          price: item.unit_price,
          image: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop', // Placeholder
        });
      }
    });
    
    alert(`Added "${bundle.bundle_name}" to cart!`);
  };

  const BundleCard = ({ bundle, isRecommended = false }) => (
    <div className={`bg-white rounded-lg shadow-lg p-6 border-2 ${
      isRecommended ? 'border-yellow-400 relative' : 'border-gray-200'
    }`}>
      {isRecommended && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-yellow-400 text-gray-900 font-bold px-4 py-1 rounded-full text-sm">
          ⭐ Recommended for You
        </div>
      )}
      
      <div className="mt-2">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          {bundle.bundle_name}
        </h3>
        
        <div className="flex items-baseline gap-2 mb-4">
          <span className="text-3xl font-bold text-gray-900">
            ${bundle.total_price.toFixed(2)}
          </span>
          {bundle.original_price && bundle.original_price > bundle.total_price && (
            <span className="text-lg text-gray-500 line-through">
              ${bundle.original_price.toFixed(2)}
            </span>
          )}
        </div>

        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-semibold text-gray-700">Bundle Score:</span>
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500"
                style={{ width: `${Math.min(bundle.score * 10, 100)}%` }}
              />
            </div>
            <span className="text-sm font-bold text-gray-900">
              {bundle.score.toFixed(1)}/10
            </span>
          </div>
        </div>

        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            📦 Includes {bundle.items.length} items:
          </h4>
          <ul className="space-y-1">
            {bundle.items.map((item, idx) => (
              <li key={idx} className="text-sm text-gray-600 flex justify-between">
                <span>
                  • {item.name} {item.quantity > 1 && `(x${item.quantity})`}
                </span>
                <span className="font-semibold">
                  ${(item.unit_price * item.quantity).toFixed(2)}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {bundle.substitutions && bundle.substitutions.length > 0 && (
          <div className="mb-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
            <h4 className="text-sm font-semibold text-yellow-800 mb-1">
              ⚠️ Substitutions Applied
            </h4>
            {bundle.substitutions.map((sub, idx) => (
              <p key={idx} className="text-xs text-yellow-700">
                {sub.original_name} → {sub.replacement_name}
              </p>
            ))}
          </div>
        )}

        <div className="flex gap-2 text-xs text-gray-500 mb-4">
          {bundle.avg_eta_minutes && (
            <span className="flex items-center gap-1">
              🚚 {bundle.avg_eta_minutes} min delivery
            </span>
          )}
          {bundle.in_stock_count && bundle.items.length && (
            <span>
              ✓ {bundle.in_stock_count}/{bundle.items.length} in stock
            </span>
          )}
        </div>

        <button
          onClick={() => handleAddBundleToCart(bundle)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition-colors"
        >
          Add Bundle to Cart
        </button>
      </div>
    </div>
  );

  return (
    <div className="bundle-display-container">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Your Personalized Bundles
        </h2>
        <p className="text-gray-600">
          Intent: <span className="font-semibold">{bundleData.intentType}</span> • 
          Confidence: <span className="font-semibold">{(bundleData.confidence * 100).toFixed(0)}%</span>
          {bundleData.fromCache && (
            <span className="ml-2 text-green-600 text-sm">• ⚡ From Cache</span>
          )}
        </p>
      </div>

      {bundleData.clarificationQuestion && (
        <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
          <h3 className="text-sm font-semibold text-blue-900 mb-1">
            Need Clarification
          </h3>
          <p className="text-sm text-blue-800">
            {bundleData.clarificationQuestion}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {recommended && (
          <BundleCard bundle={recommended} isRecommended={true} />
        )}
        
        {options && options.filter(b => b.bundle_name !== recommended?.bundle_name).map((bundle, idx) => (
          <BundleCard key={idx} bundle={bundle} />
        ))}
      </div>
    </div>
  );
};

export default BundleDisplay;
