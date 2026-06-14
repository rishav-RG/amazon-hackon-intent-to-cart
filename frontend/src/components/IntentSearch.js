import React, { useState, useRef, useEffect } from 'react';
import { useCart } from '../context/CartContext';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const IntentSearch = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResults, setLastResults] = useState(null);
  const [expandedBundle, setExpandedBundle] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { addToCart } = useCart();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleOpen = () => {
    setIsOpen(true);
    if (messages.length === 0) {
      setMessages([{
        type: 'ai',
        content: "How can I help you today?",
      }]);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || loading) return;

    const userMsg = inputValue.trim();
    setInputValue('');
    setMessages(prev => [...prev, { type: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/v1/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': 'demo-user-1',
        },
        body: JSON.stringify({ query: userMsg }),
      });

      if (!response.ok) throw new Error(`Error ${response.status}`);

      const data = await response.json();

      if (data.needs_clarification) {
        // Backend is asking for clarification
        setMessages(prev => [...prev, {
          type: 'ai',
          content: data.clarification_question,
          intent: data.intent,
        }]);
      } else {
        // Got products!
        setLastResults(data);
        setMessages(prev => [...prev, {
          type: 'ai-results',
          content: `Found ${data.total_results} products for "${data.query}"`,
          data: data,
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'ai',
        content: `Sorry, something went wrong: ${err.message}. Please try again.`,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = (product) => {
    addToCart({
      id: product.product_id,
      title: product.name,
      price: product.discount_price || product.price,
      image: product.image_url || 'https://via.placeholder.com/100x100?text=Product',
    });
    setMessages(prev => [...prev, {
      type: 'system',
      content: `Added "${product.name}" to cart!`,
    }]);
  };

  const handleAddBundle = (bundle) => {
    bundle.items.forEach((product) => {
      addToCart({
        id: product.product_id,
        title: product.name,
        price: product.discount_price || product.price,
        image: product.image_url || 'https://via.placeholder.com/100x100?text=Product',
      });
    });
    setMessages(prev => [...prev, {
      type: 'system',
      content: `Added ${bundle.items.length} items (${bundle.tier} bundle) to cart! Total: Rs.${bundle.total.toFixed(0)}`,
    }]);
  };

  const getTierLabel = (tier) => {
    switch (tier) {
      case 'budget': return '💰 Budget';
      case 'classic': return '⭐ Recommended';
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

  // Collapsed state — just a search bar
  if (!isOpen) {
    return (
      <div className="flex-1 max-w-2xl mx-2 sm:mx-4">
        <div
          onClick={handleOpen}
          className="flex items-center bg-white rounded-md px-4 py-2 cursor-pointer hover:ring-2 hover:ring-orange-400 transition-all"
        >
          <svg className="w-5 h-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <span className="text-gray-400 text-sm">Ask AI: "I need baby shampoo" or "party snacks"...</span>
        </div>
      </div>
    );
  }

  // Expanded chat window
  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-40" onClick={() => setIsOpen(false)} />

      {/* Chat Window */}
      <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl h-[80vh] bg-white rounded-xl shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-900 rounded-t-xl">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-orange-400 rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 className="text-white font-medium text-sm">Intent-to-Cart AI</h3>
            </div>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx}>
              {msg.type === 'user' && (
                <div className="flex justify-end">
                  <div className="bg-blue-600 text-white px-4 py-2 rounded-2xl rounded-br-md max-w-[80%] text-sm">
                    {msg.content}
                  </div>
                </div>
              )}

              {msg.type === 'ai' && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-2xl rounded-bl-md max-w-[80%] text-sm">
                    {msg.content}
                    {msg.intent && (
                      <div className="mt-2 flex gap-1 flex-wrap">
                        <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded">
                          {msg.intent.intent_type.replace('_', ' ')}
                        </span>
                        <span className="bg-gray-200 text-gray-600 text-xs px-2 py-0.5 rounded">
                          {(msg.intent.confidence * 100).toFixed(0)}% sure
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {msg.type === 'system' && (
                <div className="flex justify-center">
                  <div className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-medium">
                    ✓ {msg.content}
                  </div>
                </div>
              )}

              {msg.type === 'ai-results' && msg.data && (
                <div className="space-y-3">
                  {/* Intent info */}
                  <div className="flex justify-start">
                    <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-2xl rounded-bl-md text-sm">
                      {msg.content}
                      <div className="mt-2 flex gap-1 flex-wrap">
                        <span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded">
                          {msg.data.intent.intent_type.replace('_', ' ')}
                        </span>
                        {msg.data.intent.llm_used && (
                          <span className="bg-purple-100 text-purple-700 text-xs px-2 py-0.5 rounded">
                            AI-powered
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Bundles — Side by Side, Clickable */}
                  {msg.data.bundles.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-gray-500 px-2 mb-2">Smart Bundles (click to expand):</p>
                      <div className="grid grid-cols-3 gap-2">
                        {msg.data.bundles.map((bundle) => (
                          <div
                            key={bundle.tier}
                            onClick={() => setExpandedBundle(expandedBundle?.tier === bundle.tier ? null : bundle)}
                            className={`border-2 rounded-lg p-2 cursor-pointer transition-all hover:shadow-md ${getTierColor(bundle.tier)} ${expandedBundle?.tier === bundle.tier ? 'ring-2 ring-blue-500' : ''}`}
                          >
                            <div className="text-center">
                              <span className="text-xs font-medium block">{getTierLabel(bundle.tier)}</span>
                              <span className="text-sm font-bold block mt-1">Rs.{bundle.total.toFixed(0)}</span>
                              <span className="text-xs text-gray-500">{bundle.items.length} items</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Expanded Bundle Detail */}
                  {expandedBundle && (
                    <BundleDetail
                      bundle={expandedBundle}
                      onClose={() => setExpandedBundle(null)}
                      onAddToCart={handleAddBundle}
                      onAddProduct={handleAddProduct}
                    />
                  )}

                  {/* Individual products */}
                  <div>
                    <p className="text-xs font-medium text-gray-500 px-2 mb-2">Or pick individual items:</p>
                    <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
                      {msg.data.products.slice(0, 8).map((product) => (
                        <div key={product.product_id} className="border rounded-lg p-2 bg-white hover:shadow-md transition-shadow">
                          {product.image_url && (
                            <img
                              src={product.image_url}
                              alt={product.name}
                              className="w-full h-16 object-cover rounded mb-1"
                              onError={(e) => { e.target.style.display = 'none'; }}
                            />
                          )}
                          <p className="text-xs font-medium line-clamp-2">{product.name}</p>
                          <p className="text-xs text-gray-500">{product.brand}</p>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-xs font-bold">Rs.{product.discount_price || product.price}</span>
                            {product.product_url && (
                              <a href={product.product_url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-700">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                              </a>
                            )}
                          </div>
                          <button
                            onClick={() => handleAddProduct(product)}
                            className="w-full mt-1 bg-yellow-400 hover:bg-yellow-500 text-xs px-2 py-1 rounded font-medium"
                          >
                            Add to Cart
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-bl-md flex items-center gap-2">
                <svg className="w-5 h-5 animate-spin text-orange-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span className="text-xs text-gray-500">Finding products...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t px-4 py-3">
          <form onSubmit={handleSend} className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              placeholder="Type what you need..."
              className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-400"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !inputValue.trim()}
              className="bg-orange-400 hover:bg-orange-500 text-white rounded-full w-10 h-10 flex items-center justify-center disabled:opacity-50"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
        </div>
      </div>
    </>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// Bundle Detail Popup Component
// ──────────────────────────────────────────────────────────────────────────────

const BundleDetail = ({ bundle, onClose, onAddToCart, onAddProduct }) => {
  const [quantities, setQuantities] = useState(
    Object.fromEntries(bundle.items.map(item => [item.product_id, 1]))
  );

  const updateQty = (productId, delta) => {
    setQuantities(prev => ({
      ...prev,
      [productId]: Math.max(1, (prev[productId] || 1) + delta)
    }));
  };

  const totalWithQuantities = bundle.items.reduce(
    (sum, item) => sum + (item.discount_price || item.price) * (quantities[item.product_id] || 1),
    0
  );

  return (
    <div className="border-2 border-blue-300 rounded-xl bg-white shadow-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-bold text-gray-900">
          {bundle.tier === 'budget' && '💰 Budget Bundle'}
          {bundle.tier === 'classic' && '⭐ Recommended Bundle'}
          {bundle.tier === 'premium' && '👑 Premium Bundle'}
        </h4>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg">×</button>
      </div>

      {/* Products list with quantity controls */}
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {bundle.items.map((item) => (
          <div key={item.product_id} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
            {/* Image */}
            {item.image_url ? (
              <img src={item.image_url} alt={item.name} className="w-10 h-10 rounded object-cover flex-shrink-0"
                onError={(e) => { e.target.src = 'https://via.placeholder.com/40x40?text=' + item.brand?.charAt(0); }} />
            ) : (
              <div className="w-10 h-10 rounded bg-orange-100 flex items-center justify-center text-orange-600 font-bold text-sm flex-shrink-0">
                {item.brand?.charAt(0) || 'P'}
              </div>
            )}

            {/* Details */}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-900 truncate">{item.name}</p>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-gray-900">Rs.{item.discount_price || item.price}</span>
                {item.discount_price && item.discount_price < item.price && (
                  <span className="text-xs text-gray-400 line-through">Rs.{item.price}</span>
                )}
                {item.product_url && (
                  <a href={item.product_url} target="_blank" rel="noopener noreferrer"
                    className="text-blue-500 hover:text-blue-700 text-xs underline">
                    View
                  </a>
                )}
              </div>
            </div>

            {/* Quantity controls */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <button
                onClick={() => updateQty(item.product_id, -1)}
                className="w-6 h-6 rounded bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-xs font-bold"
              >-</button>
              <span className="w-6 text-center text-xs font-medium">{quantities[item.product_id]}</span>
              <button
                onClick={() => updateQty(item.product_id, 1)}
                className="w-6 h-6 rounded bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-xs font-bold"
              >+</button>
            </div>
          </div>
        ))}
      </div>

      {/* Total + Add to Cart */}
      <div className="border-t pt-3 flex items-center justify-between">
        <div>
          <span className="text-xs text-gray-500">Total:</span>
          <span className="text-lg font-bold text-gray-900 ml-1">Rs.{totalWithQuantities.toFixed(0)}</span>
        </div>
        <button
          onClick={() => onAddToCart(bundle)}
          className="bg-orange-400 hover:bg-orange-500 text-sm font-medium py-2 px-4 rounded-lg text-gray-900"
        >
          Add All to Cart
        </button>
      </div>
    </div>
  );
};

export default IntentSearch;
