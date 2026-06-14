/**
 * Intent Service - Handles intent classification and bundle retrieval
 */

import { API_ENDPOINTS, apiCall } from '../config/api';

/**
 * Classify user's search query into an intent
 * @param {string} text - User's search query
 * @param {string} sessionId - Session ID for tracking
 * @returns {Promise<Object>} Intent classification result
 */
export const classifyIntent = async (text, sessionId = 'session-' + Date.now()) => {
  try {
    const response = await apiCall(API_ENDPOINTS.classifyIntent, {
      method: 'POST',
      body: JSON.stringify({
        text,
        session_id: sessionId,
      }),
    });
    
    return response;
  } catch (error) {
    console.error('Intent classification failed:', error);
    throw error;
  }
};

/**
 * Get product bundles for a classified intent
 * @param {string} intentId - UUID of the classified intent
 * @returns {Promise<Object>} Bundle recommendations
 */
export const getBundles = async (intentId) => {
  try {
    const response = await apiCall(API_ENDPOINTS.getBundles(intentId));
    return response;
  } catch (error) {
    console.error('Failed to fetch bundles:', error);
    throw error;
  }
};

/**
 * Combined function: Classify intent and get bundles
 * @param {string} searchQuery - User's search query
 * @returns {Promise<Object>} Bundles for the search query
 */
export const searchAndGetBundles = async (searchQuery) => {
  try {
    // Step 1: Classify intent
    const intentResult = await classifyIntent(searchQuery);
    
    // If cached bundle is available, return it immediately
    if (intentResult.cached_bundle) {
      return {
        intentId: intentResult.intent_id,
        intentType: intentResult.intent_type,
        confidence: intentResult.confidence,
        bundles: intentResult.cached_bundle,
        fromCache: true,
      };
    }
    
    // Step 2: Get bundles for the intent
    const bundlesResult = await getBundles(intentResult.intent_id);
    
    return {
      intentId: intentResult.intent_id,
      intentType: intentResult.intent_type,
      confidence: intentResult.confidence,
      bundles: bundlesResult,
      fromCache: false,
      clarificationQuestion: intentResult.clarification_question,
    };
  } catch (error) {
    console.error('Search and bundle retrieval failed:', error);
    throw error;
  }
};
