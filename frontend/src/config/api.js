/**
 * API Configuration for Intent-to-Cart Backend Integration
 */

// Backend API base URL
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
  // Intent endpoints
  classifyIntent: `${API_BASE_URL}/v1/intent`,
  clarification: `${API_BASE_URL}/v1/clarification`,
  
  // Bundle endpoints
  getBundles: (intentId) => `${API_BASE_URL}/v1/bundles/${intentId}`,
  
  // Cart endpoints
  getCart: (cartId) => `${API_BASE_URL}/v1/cart/${cartId}`,
  updateCart: `${API_BASE_URL}/v1/cart`,
  
  // Checkout endpoints
  checkout: `${API_BASE_URL}/v1/checkout`,
  
  // Other endpoints
  health: `${API_BASE_URL}/health`,
  buyAgain: `${API_BASE_URL}/v1/buy-again`,
};

// Default headers for all requests
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
  // Add user ID header (for demo purposes, use a fixed user)
  'X-User-ID': 'demo-user-123',
};

// Helper function to make API calls
export const apiCall = async (url, options = {}) => {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...DEFAULT_HEADERS,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { code: 'UNKNOWN_ERROR', message: 'Request failed' }
    }));
    throw new Error(error.error?.message || 'API request failed');
  }

  return response.json();
};
