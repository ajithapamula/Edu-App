import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';

const ForgotPasswordForm = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous messages
    setError('');
    setMessage('');

    // Validation
    if (!email.trim()) {
      setError('Email is required');
      return;
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);

    try {
      // TODO: Replace with actual API call to your backend
      console.log('Forgot password request for:', email);
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate successful response
      setMessage('Password reset link has been sent to your email address. Please check your inbox.');
      setEmail(''); // Clear the form
      
    } catch (err) {
      console.error('Forgot password error:', err);
      setError('Failed to send reset email. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailChange = (e) => {
    setEmail(e.target.value);
    // Clear error when user starts typing
    if (error) {
      setError('');
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
      {message && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TextField
        margin="normal"
        required
        fullWidth
        id="email"
        label="Email Address"
        name="email"
        type="email"
        autoComplete="email"
        autoFocus
        value={email}
        onChange={handleEmailChange}
        disabled={loading}
        placeholder="Enter your email address"
      />

      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 3, mb: 2 }}
        disabled={loading || !email.trim()}
      >
        {loading ? (
          <>
            <CircularProgress size={20} sx={{ mr: 1, color: 'inherit' }} />
            Sending Reset Link...
          </>
        ) : (
          'Send Reset Link'
        )}
      </Button>
    </Box>
  );
};

export default ForgotPasswordForm;