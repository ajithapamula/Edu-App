import { useState, useCallback } from 'react';
import { useAuth } from './useAuth';

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { logout } = useAuth();

  const makeRequest = useCallback(async (apiCall) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiCall();
      setLoading(false);
      return response;
    } catch (err) {
      setLoading(false);
      
      // Handle unauthorized access
      if (err.response?.status === 401) {
        logout();
        return;
      }
      
      setError(err.response?.data?.message || err.message || 'An error occurred');
      throw err;
    }
  }, [logout]);

  return { loading, error, makeRequest, setError };
};