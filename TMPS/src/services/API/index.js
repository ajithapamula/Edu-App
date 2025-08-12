// src/services/API/index.js
// Base API configuration

// ✅ Fixed: Use import.meta.env instead of process.env for Vite
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.48.4:8000';

// Get authentication token from localStorage
const getAuthToken = () => {
  return localStorage.getItem('token') || sessionStorage.getItem('token');
};

// Common headers for all requests
const getHeaders = (isFormData = false) => {
  const headers = {};
  
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

// Generic API request function
export const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const isFormData = options.body instanceof FormData;
  
  const config = {
    headers: getHeaders(isFormData),
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    // Handle different response types
    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorData || response.statusText}`);
    }
    
    // Check if response has content
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    } else {
      return await response.text();
    }
    
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

// Utility function for handling file uploads
export const createFormData = (data) => {
  const formData = new FormData();
  
  Object.keys(data).forEach(key => {
    if (data[key] instanceof File) {
      formData.append(key, data[key]);
    } else if (data[key] !== null && data[key] !== undefined) {
      formData.append(key, data[key]);
    }
  });
  
  return formData;
};

export { API_BASE_URL };