import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Alert,
  Card,
  CardContent,
  IconButton,
  Button,
  Avatar,
  Tooltip,
  Fade,
  Zoom,
  Grid,
  useTheme,
  alpha,
  styled,
  keyframes
} from '@mui/material';
import { 
  Refresh, 
  PlayArrow,
  School,
  TrendingUp,
  Mic,
  Schedule
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Import the standup API
import { standupCallAPI } from '../../../services/API/studentstandup';

// Shimmer animation keyframes
const shimmer = keyframes`
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
`;

// Styled components for animations
const PulseButton = styled(Button)(({ theme }) => ({
  position: 'relative',
  overflow: 'hidden',
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: `linear-gradient(45deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
    borderRadius: 'inherit',
    animation: `${shimmer} 2s infinite ease-in-out`,
  },
  '&:hover::before': {
    animationDuration: '0.5s',
  }
}));

const StandupCall = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const theme = useTheme();
  const navigate = useNavigate();

  const handleStartStandup = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Starting standup session...');
      
      // Call API to start standup
      const response = await standupCallAPI.startStandup();
      console.log('Standup started:', response);
      
      // Navigate to standup call page with test ID
      if (response && (response.test_id || response.testId || response.id)) {
        const testId = response.test_id || response.testId || response.id;
        navigate(`/student/daily-standups/call/${testId}`);
      } else {
        throw new Error('No test ID received from server');
      }
      
    } catch (err) {
      console.error('Error starting standup:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setError(null);
  };

  // Show error state
  if (error && !loading) {
    return (
      <Fade in={true}>
        <Box sx={{ p: 3 }}>
          <Typography 
            variant="h4" 
            component="h1" 
            gutterBottom
            sx={{
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 'bold',
              mb: 3
            }}
          >
            Daily Standup
          </Typography>
          <Alert 
            severity="error" 
            sx={{
              borderRadius: 2,
              '& .MuiAlert-icon': {
                fontSize: '1.5rem'
              }
            }}
            action={
              <IconButton 
                size="small" 
                onClick={handleRefresh}
                sx={{
                  '&:hover': {
                    transform: 'rotate(180deg)',
                    transition: 'transform 0.3s ease-in-out'
                  }
                }}
              >
                <Refresh />
              </IconButton>
            }
          >
            Failed to start standup: {error}
          </Alert>
        </Box>
      </Fade>
    );
  }

  return (
    <Fade in={true}>
      <Box sx={{ p: 3, minHeight: '100vh', backgroundColor: alpha(theme.palette.primary.main, 0.02) }}>
        {/* Header Section */}
        <Box 
          display="flex" 
          justifyContent="space-between" 
          alignItems="center" 
          mb={4}
          sx={{
            background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
            p: 3,
            borderRadius: 3,
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
          }}
        >
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar 
              sx={{ 
                bgcolor: theme.palette.primary.main,
                width: 48,
                height: 48,
                boxShadow: theme.shadows[8]
              }}
            >
              <Mic />
            </Avatar>
            <Box>
              <Typography 
                variant="h4" 
                component="h1"
                sx={{
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 'bold',
                  mb: 0.5
                }}
              >
                Daily Standup
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Start your daily standup session
              </Typography>
            </Box>
          </Box>
          
          <Tooltip title="Refresh">
            <IconButton 
              onClick={handleRefresh} 
              disabled={loading}
              sx={{
                bgcolor: theme.palette.background.paper,
                boxShadow: theme.shadows[4],
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                  transform: 'rotate(180deg)',
                  transition: 'all 0.3s ease-in-out'
                },
                '&:disabled': {
                  bgcolor: alpha(theme.palette.action.disabled, 0.1)
                }
              }}
            >
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Stats Cards */}
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} sm={6} md={4}>
            <Zoom in={true} style={{ transitionDelay: '100ms' }}>
              <Card 
                sx={{
                  background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                  color: 'white',
                  borderRadius: 3,
                  boxShadow: theme.shadows[8],
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    transition: 'transform 0.3s ease-in-out',
                    boxShadow: theme.shadows[12]
                  }
                }}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography variant="h3" fontWeight="bold">
                        Ready
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        System Status
                      </Typography>
                    </Box>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 56, height: 56 }}>
                      <School sx={{ fontSize: 28 }} />
                    </Avatar>
                  </Box>
                </CardContent>
              </Card>
            </Zoom>
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <Zoom in={true} style={{ transitionDelay: '200ms' }}>
              <Card 
                sx={{
                  background: `linear-gradient(135deg, ${theme.palette.secondary.main}, ${theme.palette.secondary.dark})`,
                  color: 'white',
                  borderRadius: 3,
                  boxShadow: theme.shadows[8],
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    transition: 'transform 0.3s ease-in-out',
                    boxShadow: theme.shadows[12]
                  }
                }}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography variant="h3" fontWeight="bold">
                        5-10
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Minutes Duration
                      </Typography>
                    </Box>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 56, height: 56 }}>
                      <Schedule sx={{ fontSize: 28 }} />
                    </Avatar>
                  </Box>
                </CardContent>
              </Card>
            </Zoom>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <Zoom in={true} style={{ transitionDelay: '300ms' }}>
              <Card 
                sx={{
                  background: `linear-gradient(135deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`,
                  color: 'white',
                  borderRadius: 3,
                  boxShadow: theme.shadows[8],
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    transition: 'transform 0.3s ease-in-out',
                    boxShadow: theme.shadows[12]
                  }
                }}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography variant="h3" fontWeight="bold">
                        Interactive
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Voice Enabled
                      </Typography>
                    </Box>
                    <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 56, height: 56 }}>
                      <TrendingUp sx={{ fontSize: 28 }} />
                    </Avatar>
                  </Box>
                </CardContent>
              </Card>
            </Zoom>
          </Grid>
        </Grid>

        {/* Main Start Button Section */}
        <Paper 
          sx={{
            borderRadius: 3,
            overflow: 'hidden',
            boxShadow: theme.shadows[8],
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
            background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.9)}, ${alpha(theme.palette.primary.main, 0.05)})`
          }}
        >
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <Avatar 
              sx={{ 
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                width: 80,
                height: 80,
                mx: 'auto',
                mb: 3,
                border: `3px solid ${alpha(theme.palette.primary.main, 0.2)}`
              }}
            >
              <Mic sx={{ fontSize: 40, color: theme.palette.primary.main }} />
            </Avatar>
            
            <Typography 
              variant="h4" 
              component="h2" 
              gutterBottom
              sx={{
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontWeight: 'bold',
                mb: 2
              }}
            >
              Ready to Start Your Standup?
            </Typography>
            
            <Typography 
              variant="body1" 
              color="text.secondary" 
              sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}
            >
              Your daily standup session will guide you through key questions about your progress, 
              challenges, and plans. The session is interactive and voice-enabled for a natural conversation experience.
            </Typography>
            
            <Box display="flex" justifyContent="center" gap={2}>
              <PulseButton
                variant="contained"
                size="large"
                onClick={handleStartStandup}
                disabled={loading}
                startIcon={<PlayArrow />}
                sx={{
                  minWidth: 200,
                  height: 56,
                  borderRadius: 3,
                  fontSize: '1.1rem',
                  fontWeight: 'bold',
                  background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                  boxShadow: theme.shadows[8],
                  '&:hover': {
                    background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.secondary.dark})`,
                    transform: 'translateY(-2px)',
                    boxShadow: theme.shadows[12]
                  },
                  '&:disabled': {
                    background: alpha(theme.palette.action.disabled, 0.3)
                  }
                }}
              >
                {loading ? 'Starting...' : 'Start Standup'}
              </PulseButton>
            </Box>
            
            {/* Instructions */}
            <Box 
              sx={{ 
                mt: 4, 
                p: 3, 
                bgcolor: alpha(theme.palette.info.main, 0.05),
                borderRadius: 2,
                border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`
              }}
            >
              <Typography variant="h6" color="info.main" gutterBottom>
                What to Expect:
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>1. Yesterday's Work:</strong> Discuss what you accomplished
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>2. Today's Plans:</strong> Share what you plan to work on
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>3. Blockers:</strong> Mention any challenges or obstacles
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Box>
        </Paper>

        <style jsx>{`
          @keyframes fadeInUp {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}</style>
      </Box>
    </Fade>
  );
};

export default StandupCall;