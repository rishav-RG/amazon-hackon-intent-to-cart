import React, { useState, useRef, useEffect, useCallback } from 'react';
import ChatMessage from './ChatMessage';
import BundleCard from './BundleCard';
import { postIntent, postClarification, getBundles, patchCart } from '../../services/api';

/**
 * Floating chat-based Smart Shopping Assistant.
 * Flow: Intent → Clarification → Bundles → Cart
 */

// Generate a unique session ID per assistant session
const generateSessionId = () => `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const SmartAssistant = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'system', content: 'How can I help you today?' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [addingBundle, setAddingBundle] = useState(null);

  // Flow state
  const [flowState, setFlowState] = useState('idle'); // idle | clarifying | confirming | bundles | done
  const [intentId, setIntentId] = useState(null);
  const [sessionId] = useState(generateSessionId);
  const [clarificationSessionId, setClarificationSessionId] = useState(null);
  const [answeredQuestions, setAnsweredQuestions] = useState([]); // eslint-disable-line no-unused-vars
  const [bundles, setBundles] = useState(null); // eslint-disable-line no-unused-vars

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  // Listen for smart-search events from the banner
  useEffect(() => {
    const handler = (e) => {
      const query = e.detail;
      if (query) {
        setIsOpen(true);
        // Reset state for new search
        setMessages([{ role: 'system', content: 'How can I help you today?' }]);
        setFlowState('idle');
        setBundles(null);
        setAnsweredQuestions([]);
        // Trigger intent after a tick so panel is visible
        setTimeout(() => handleSendIntent(query), 100);
      }
    };
    window.addEventListener('smart-search', handler);
    return () => window.removeEventListener('smart-search', handler);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const addMessage = useCallback((role, content, extra = {}) => {
    setMessages((prev) => [...prev, { role, content, ...extra }]);
  }, []);

  // ─── STEP 1: Send Intent ───────────────────────────────────────────────
  const handleSendIntent = async (text) => {
    addMessage('user', text);
    setLoading(true);
    try {
      const res = await postIntent(text, sessionId);
      setIntentId(res.intent_id);

      // Check if clarification is needed
      if (res.needs_clarification && res.clarification_question) {
        // Use the SAME sessionId that was sent with the intent request
        // (backend stores the Redis session under that key)
        setClarificationSessionId(sessionId);
        setFlowState('clarifying');
        addMessage('system', res.clarification_question);
      } else {
        // Skip clarification, go straight to bundles
        addMessage('system', `Got it! Finding personalized bundles for "${text}"...`);
        setFlowState('bundles');
        await fetchBundles(res.intent_id);
      }
    } catch (err) {
      addMessage('system', `❌ ${err.message}`);
      setFlowState('idle');
    } finally {
      setLoading(false);
    }
  };

  // ─── STEP 2: Handle Clarification ─────────────────────────────────────
  const handleClarificationAnswer = async (answer) => {
    addMessage('user', answer);
    setLoading(true);
    try {
      const res = await postClarification(intentId, clarificationSessionId, answer);

      if (res.complete) {
        // Show Q&A summary for confirmation
        const qaList = res.answered_questions || [];
        setAnsweredQuestions(qaList);
        setFlowState('confirming');
        addMessage('system', null, { type: 'qa_summary', qaList });
      } else {
        // Next question
        addMessage('system', res.next_question);
      }
    } catch (err) {
      addMessage('system', `❌ ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ─── STEP 3: Confirm & Fetch Bundles ───────────────────────────────────
  const handleConfirm = async () => {
    addMessage('user', '✅ Confirmed! Find me bundles.');
    setFlowState('bundles');
    setLoading(true);
    await fetchBundles(intentId);
    setLoading(false);
  };

  const fetchBundles = async (id) => {
    try {
      addMessage('system', '🔍 Generating personalized bundles...');
      const res = await getBundles(id);
      setBundles(res);
      setFlowState('bundles');
      addMessage('system', null, { type: 'bundles', data: res });
    } catch (err) {
      addMessage('system', `❌ ${err.message}`);
      setFlowState('idle');
    }
  };

  // ─── STEP 4: Add Bundle to Cart ────────────────────────────────────────
  const handleSelectBundle = async (bundle) => {
    setAddingBundle(bundle.bundle_id);
    try {
      // First, clear any existing items by sending remove ops for current cart
      const existingCart = localStorage.getItem('backendCart');
      if (existingCart) {
        const parsed = JSON.parse(existingCart);
        if (parsed.items && parsed.items.length > 0) {
          const removeOps = parsed.items.map((item) => ({
            type: 'remove',
            productId: item.productId,
          }));
          await patchCart(removeOps, parsed.version);
        }
      }

      // Now add the selected bundle items to a fresh cart
      const operations = bundle.items.map((item) => ({
        type: 'add',
        productId: item.product_id,
        quantity: item.quantity,
      }));
      const cartRes = await patchCart(operations, null);
      // Store backend cart in localStorage for the Cart page to pick up
      localStorage.setItem('backendCart', JSON.stringify(cartRes));
      window.dispatchEvent(new Event('backend-cart-updated'));
      addMessage('system', null, { type: 'cart_success', data: cartRes, bundleName: bundle.bundle_name });
      setFlowState('done');
    } catch (err) {
      addMessage('system', `❌ Failed to add to cart: ${err.message}`);
    } finally {
      setAddingBundle(null);
    }
  };

  // ─── Form Submit ──────────────────────────────────────────────────────
  const handleSubmit = (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput('');

    if (flowState === 'idle' || flowState === 'done') {
      // New intent
      setFlowState('idle');
      setBundles(null);
      setAnsweredQuestions([]);
      handleSendIntent(text);
    } else if (flowState === 'clarifying') {
      handleClarificationAnswer(text);
    }
  };

  // ─── Reset assistant ──────────────────────────────────────────────────
  const handleReset = () => {
    setMessages([{ role: 'system', content: 'How can I help you today?' }]);
    setFlowState('idle');
    setIntentId(null);
    setBundles(null);
    setAnsweredQuestions([]);
    setAddingBundle(null);
  };

  // ─── Render Message Content ────────────────────────────────────────────
  const renderMessage = (msg, idx) => {
    // Q&A Summary
    if (msg.type === 'qa_summary') {
      return (
        <ChatMessage key={idx} role="system">
          <div>
            <p className="font-semibold mb-2">Here's what I gathered:</p>
            <ul className="space-y-1 mb-3">
              {msg.qaList.map((qa, i) => (
                <li key={i} className="text-xs">
                  <span className="font-medium text-gray-600">Q: {qa.question}</span>
                  <br />
                  <span className="text-gray-900">A: {qa.answer}</span>
                </li>
              ))}
            </ul>
            <p className="text-xs text-gray-500 mb-2">Does this look right?</p>
            <div className="flex gap-2">
              <button
                onClick={handleConfirm}
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg disabled:opacity-50"
              >
                ✅ Yes, find bundles
              </button>
              <button
                onClick={handleReset}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs font-medium px-3 py-1.5 rounded-lg"
              >
                Start over
              </button>
            </div>
          </div>
        </ChatMessage>
      );
    }

    // Bundle cards
    if (msg.type === 'bundles') {
      const data = msg.data;
      return (
        <ChatMessage key={idx} role="system">
          <div>
            <p className="font-semibold mb-2">
              Found {data.options.length} bundles for you:
            </p>
            <div className="space-y-3">
              {data.options.map((bundle) => (
                <BundleCard
                  key={bundle.bundle_id}
                  bundle={bundle}
                  isRecommended={bundle.bundle_id === data.recommended.bundle_id}
                  onSelect={handleSelectBundle}
                  isLoading={addingBundle === bundle.bundle_id}
                />
              ))}
            </div>
          </div>
        </ChatMessage>
      );
    }

    // Cart success
    if (msg.type === 'cart_success') {
      const { data, bundleName } = msg;
      return (
        <ChatMessage key={idx} role="system">
          <div>
            <p className="font-semibold text-green-700 mb-1">✅ Added to cart!</p>
            <p className="text-xs text-gray-600 mb-2">
              {bundleName} — {data.items.length} items, ₹{data.total.toFixed(2)}
            </p>
            <p className="text-xs text-gray-500">
              Cart version: {data.version} • Status: {data.status}
            </p>
            <button
              onClick={handleReset}
              className="mt-2 text-xs text-blue-600 hover:underline"
            >
              Start a new search
            </button>
          </div>
        </ChatMessage>
      );
    }

    // Default text message
    return <ChatMessage key={idx} role={msg.role} content={msg.content} />;
  };

  // ─── Input placeholder based on state ──────────────────────────────────
  const getPlaceholder = () => {
    if (loading) return 'Thinking...';
    if (flowState === 'clarifying') return 'Type your answer...';
    if (flowState === 'confirming') return 'Waiting for confirmation...';
    if (flowState === 'bundles') return 'Select a bundle above...';
    return 'Tell me what you need...';
  };

  const isInputDisabled = loading || flowState === 'confirming' || flowState === 'bundles';

  return (
    <>
      {/* Floating action button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-orange-500 hover:bg-orange-600 text-white w-14 h-14 rounded-full shadow-lg flex items-center justify-center transition-transform hover:scale-110"
          aria-label="Open Smart Shopping Assistant"
        >
          <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 w-[480px] max-w-[calc(100vw-2rem)] h-[600px] max-h-[calc(100vh-4rem)] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-gray-900 text-white px-4 py-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <span className="text-lg">🔍</span>
              <span className="font-semibold text-sm">Intent-to-Cart AI</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-300 hover:text-white text-xl leading-none"
              aria-label="Close assistant"
            >
              ×
            </button>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-4 py-3 bg-gray-50 space-y-1">
            {messages.map((msg, idx) => renderMessage(msg, idx))}
            {loading && (
              <div className="flex justify-start mb-3">
                <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-2.5 shadow-sm">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <form
            onSubmit={handleSubmit}
            className="flex-shrink-0 border-t border-gray-200 px-3 py-2.5 bg-white flex items-center gap-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={getPlaceholder()}
              disabled={isInputDisabled}
              className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 disabled:bg-gray-100 disabled:cursor-not-allowed"
            />
            <button
              type="submit"
              disabled={isInputDisabled || !input.trim()}
              className="bg-orange-500 hover:bg-orange-600 text-white w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
};

export default SmartAssistant;
