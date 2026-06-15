/**
 * API service layer for Intent-to-Cart backend.
 * All requests go to the FastAPI backend at localhost:8000.
 */

const API_BASE = 'http://localhost:8000';
const DEFAULT_USER_ID = 'test-user-001';

/**
 * POST /v1/intent — Classify user's natural language query
 */
export async function postIntent(text, sessionId) {
  console.log('[API] POST /v1/intent →', { text, session_id: sessionId });
  const res = await fetch(`${API_BASE}/v1/intent`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': DEFAULT_USER_ID,
    },
    body: JSON.stringify({ text, session_id: sessionId }),
  });
  const data = await res.json().catch(() => ({}));
  console.log('[API] POST /v1/intent ←', res.status, data);
  if (!res.ok) {
    throw new Error(data?.error?.message || data?.detail || `Intent failed (${res.status})`);
  }
  return data;
}

/**
 * POST /v1/clarification — Answer a clarification question
 */
export async function postClarification(intentId, sessionId, answer) {
  console.log('[API] POST /v1/clarification →', { intent_id: intentId, session_id: sessionId, answer });
  const res = await fetch(`${API_BASE}/v1/clarification`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': DEFAULT_USER_ID,
    },
    body: JSON.stringify({
      intent_id: intentId,
      session_id: sessionId,
      answer,
    }),
  });
  const data = await res.json().catch(() => ({}));
  console.log('[API] POST /v1/clarification ←', res.status, data);
  if (!res.ok) {
    throw new Error(data?.error?.message || data?.detail || `Clarification failed (${res.status})`);
  }
  return data;
}

/**
 * GET /v1/bundles/{intentId} — Fetch generated bundles
 */
export async function getBundles(intentId) {
  console.log('[API] GET /v1/bundles/' + intentId + ' →');
  const res = await fetch(`${API_BASE}/v1/bundles/${intentId}`, {
    method: 'GET',
    headers: {
      'X-User-ID': DEFAULT_USER_ID,
    },
  });
  const data = await res.json().catch(() => ({}));
  console.log('[API] GET /v1/bundles ←', res.status, data);
  if (!res.ok) {
    throw new Error(data?.error?.message || data?.detail || `Bundles failed (${res.status})`);
  }
  return data;
}

/**
 * PATCH /v1/cart — Add items to cart
 */
export async function patchCart(operations, version = null) {
  console.log('[API] PATCH /v1/cart →', { operations, version });
  const res = await fetch(`${API_BASE}/v1/cart`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': DEFAULT_USER_ID,
    },
    body: JSON.stringify({ operations, version }),
  });
  const data = await res.json().catch(() => ({}));
  console.log('[API] PATCH /v1/cart ←', res.status, data);
  if (!res.ok) {
    throw new Error(data?.detail?.message || data?.detail || `Cart update failed (${res.status})`);
  }
  return data;
}

/**
 * GET /v1/cart/{cartId} — Retrieve a specific cart
 */
export async function getCart(cartId) {
  console.log('[API] GET /v1/cart/' + cartId + ' →');
  const res = await fetch(`${API_BASE}/v1/cart/${cartId}`, {
    method: 'GET',
    headers: {
      'X-User-ID': DEFAULT_USER_ID,
    },
  });
  const data = await res.json().catch(() => ({}));
  console.log('[API] GET /v1/cart ←', res.status, data);
  if (!res.ok) {
    throw new Error(data?.detail || `Get cart failed (${res.status})`);
  }
  return data;
}

/**
 * POST /v1/checkout — Checkout the cart
 */
export async function postCheckout(cartId) {
  console.log('[API] POST /v1/checkout →', { cartId });
  const res = await fetch(`${API_BASE}/v1/checkout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': DEFAULT_USER_ID,
    },
    body: JSON.stringify({ cartId }),
  });
  const data = await res.json().catch(() => ({}));
  console.log('[API] POST /v1/checkout ←', res.status, data);
  if (!res.ok) {
    throw new Error(data?.detail?.message || data?.detail || `Checkout failed (${res.status})`);
  }
  return data;
}

/**
 * GET /health — Check backend connectivity
 */
export async function checkHealth() {
  try {
    console.log('[API] GET /health →');
    const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
    console.log('[API] GET /health ←', res.status);
    return res.ok;
  } catch (err) {
    console.log('[API] GET /health ← FAILED:', err.message);
    return false;
  }
}
