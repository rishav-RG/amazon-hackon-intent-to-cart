/**
 * Cart Service - Handles cart operations with backend
 */

import { API_ENDPOINTS, apiCall } from '../config/api';

/**
 * Get cart by ID
 * @param {string} cartId - Cart UUID
 * @returns {Promise<Object>} Cart data
 */
export const getCart = async (cartId) => {
  try {
    const response = await apiCall(API_ENDPOINTS.getCart(cartId));
    return response;
  } catch (error) {
    console.error('Failed to fetch cart:', error);
    throw error;
  }
};

/**
 * Update cart (add/remove/update items)
 * @param {Object} cartData - Cart update payload
 * @returns {Promise<Object>} Updated cart
 */
export const updateCart = async (cartData) => {
  try {
    const response = await apiCall(API_ENDPOINTS.updateCart, {
      method: 'PATCH',
      body: JSON.stringify(cartData),
    });
    return response;
  } catch (error) {
    console.error('Failed to update cart:', error);
    throw error;
  }
};

/**
 * Add item to cart
 * @param {string} cartId - Cart UUID (optional, will be created if not provided)
 * @param {Object} item - Product item to add
 * @returns {Promise<Object>} Updated cart
 */
export const addToCart = async (cartId, item) => {
  const payload = {
    cart_id: cartId || undefined,
    items: [{
      product_id: item.id || item.product_id,
      name: item.title || item.name,
      quantity: 1,
      unit_price: item.price || item.unit_price,
    }],
  };
  
  return updateCart(payload);
};

/**
 * Remove item from cart
 * @param {string} cartId - Cart UUID
 * @param {string} productId - Product ID to remove
 * @returns {Promise<Object>} Updated cart
 */
export const removeFromCart = async (cartId, productId) => {
  const payload = {
    cart_id: cartId,
    items: [{
      product_id: productId,
      quantity: 0, // Setting quantity to 0 removes the item
    }],
  };
  
  return updateCart(payload);
};

/**
 * Update item quantity in cart
 * @param {string} cartId - Cart UUID
 * @param {string} productId - Product ID
 * @param {number} quantity - New quantity
 * @returns {Promise<Object>} Updated cart
 */
export const updateCartItemQuantity = async (cartId, productId, quantity) => {
  const payload = {
    cart_id: cartId,
    items: [{
      product_id: productId,
      quantity,
    }],
  };
  
  return updateCart(payload);
};

/**
 * Clear all items from cart
 * @param {string} cartId - Cart UUID
 * @returns {Promise<Object>} Empty cart
 */
export const clearCart = async (cartId) => {
  // To clear, we send empty items array
  const payload = {
    cart_id: cartId,
    items: [],
  };
  
  return updateCart(payload);
};
