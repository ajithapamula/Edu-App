import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Link
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const LoginForm = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await login(formData.email, formData.password);
      
      // Redirect based on user role from backend response
      const userRole = response.data.user.role;
      switch (userRole) {
        case 'trainer':
          navigate('/trainer');
          break;
        case 'mentor':
          navigate('/mentor');
          break;
        case 'student':
          navigate('/student');
          break;
        default:
          navigate('/');
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="#f5f5f5"
    >
      <Card sx={{ maxWidth: 400, width: '100%', mx: 2 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Login to TMS
          </Typography>
          
          {/* Demo Credentials Info - Remove this when using real API */}
          <Box sx={{ mb: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              Demo Credentials:
            </Typography>
            <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
              Trainer: trainer@tms.com / trainer123<br/>
              Mentor: mentor@tms.com / mentor123<br/>
              Student: student@tms.com / student123
            </Typography>
          </Box>
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              margin="normal"
              required
              autoComplete="email"
              autoFocus
              disabled={loading}
            />

            <TextField
              fullWidth
              label="Password"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              margin="normal"
              required
              autoComplete="current-password"
              disabled={loading}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading || !formData.email || !formData.password}
            >
              {loading ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                  Signing In...
                </>
              ) : (
                'Login'
              )}
            </Button>

            <Box textAlign="center">
              <Link
                component="button"
                variant="body2"
                onClick={() => navigate('/register')}
                sx={{ textDecoration: 'none', cursor: 'pointer' }}
                disabled={loading}
              >
                Don't have an account? Register
              </Link>
              <br />
              <Link
                component="button"
                variant="body2"
                onClick={() => navigate('/forgot-password')}
                sx={{ mt: 1, textDecoration: 'none', cursor: 'pointer' }}
                disabled={loading}
              >
                Forgot Password?
              </Link>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default LoginForm;