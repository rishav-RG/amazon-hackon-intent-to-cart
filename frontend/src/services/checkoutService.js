/**
 * Checkout Service - Handles checkout operations
 */

import { API_ENDPOINTS, apiCall } from '../config/api';

/**
 * Process checkout
 * @param {string} cartId - Cart UUID
 * @param {Object} options - Checkout options (substitutions, preferences)
 * @returns {Promise<Object>} Order confirmation
 */
export const processCheckout = async (cartId, options = {}) => {
  try {
    const payload = {
      cart_id: cartId,
      accept_substitutions: options.acceptSubstitutions ?? true,
      ...options,
    };
    
    const response = await apiCall(API_ENDPOINTS.checkout, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    
    return response;
  } catch (error) {
    console.error('Checkout failed:', error);
    throw error;
  }
};

/**
 * Get buy-again recommendations
 * @returns {Promise<Object>} Buy again items
 */
export const getBuyAgain = async () => {
  try {
    const response = await apiCall(API_ENDPOINTS.buyAgain);
    return response;
  } catch (error) {
    console.error('Failed to fetch buy-again items:', error);
    throw error;
  }
};
