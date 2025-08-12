import { mockUsers, mockDelay } from './mockData';
// import api from './api'; // Uncomment when backend is ready

// MOCK VERSION - Using mock data instead of real API calls
const authService = {
  // Login function - Mock version
  
  // In your authService.js, replace the login function with this debug version:

login: async (email, password) => {
  console.log('🔄 Mock Login attempt for:', email);
  console.log('🔒 Password:', password);
  
  // Debug: Check if mockUsers is imported correctly
  console.log('📊 Available mockUsers:', mockUsers);
  console.log('📊 Number of users:', mockUsers.length);
  
  // Simulate API delay
  await mockDelay();
  
  // Debug: Check each user
  mockUsers.forEach((user, index) => {
    console.log(`👤 User ${index + 1}:`, {
      email: user.email,
      password: user.password,
      emailMatch: user.email === email,
      passwordMatch: user.password === password,
      role: user.role
    });
  });
  
  // Find user in mock data
  const user = mockUsers.find(u => u.email === email && u.password === password);
  
  console.log('🔍 Found user:', user);
  
  if (!user) {
    console.log('❌ No user found with matching credentials');
    throw new Error('Invalid email or password');
  }
  
  // Remove password from response (like real API would)
  const { password: _, ...userResponse } = user;
  
  // Store token and user data
  localStorage.setItem('token', user.token);
  localStorage.setItem('user', JSON.stringify(userResponse));
  
  console.log('✅ Mock Login successful for:', userResponse.name, '- Role:', userResponse.role);
  
  return {
    success: true,
    data: {
      user: userResponse,
      token: user.token
    }
  };
},

  // Register function - Mock version
  register: async (userData) => {
    console.log('🔄 Mock Register attempt for:', userData.email);
    await mockDelay();
    
    // For now, just simulate success
    return {
      success: true,
      message: 'Registration successful! (Mock response)'
    };
  },

  // Logout function
  logout: async () => {
    console.log('🔄 Mock Logout...');
    await mockDelay(300);
    
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    console.log('✅ Mock Logout successful');
    return { success: true };
  },

  // Forgot password function - Mock version
  forgotPassword: async (email) => {
    console.log('🔄 Mock Forgot Password for:', email);
    await mockDelay();
    
    return {
      success: true,
      message: 'Password reset email sent! (Mock response)'
    };
  },

  // Reset password function - Mock version
  resetPassword: async (token, newPassword) => {
    console.log('🔄 Mock Reset Password');
    await mockDelay();
    
    return {
      success: true,
      message: 'Password reset successful! (Mock response)'
    };
  },

  // Get current user
  getCurrentUser: () => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
      const userData = JSON.parse(user);
      console.log('👤 Current user:', userData.name, '- Role:', userData.role);
      return userData;
    }
    return null;
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    const isAuth = !!localStorage.getItem('token');
    console.log('🔐 Is authenticated:', isAuth);
    return isAuth;
  },

  // Get token
  getToken: () => {
    return localStorage.getItem('token');
  }
};

export default authService;

/* 
🚀 REAL API VERSION - Uncomment this when backend is ready:

import api from './api';

const authService = {
  login: async (email, password) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { token, user } = response.data;
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { token, user };
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  },

  register: async (userData) => {
    try {
      const response = await api.post('/auth/register', userData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  forgotPassword: async (email) => {
    try {
      const response = await api.post('/auth/forgot-password', { email });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to send reset email');
    }
  },

  resetPassword: async (token, newPassword) => {
    try {
      const response = await api.post('/auth/reset-password', { token, newPassword });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to reset password');
    }
  },

  getCurrentUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },

  getToken: () => {
    return localStorage.getItem('token');
  }
};

export default authService;
*/