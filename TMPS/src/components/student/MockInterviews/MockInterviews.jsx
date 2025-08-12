// FIXED: MockInterviews.jsx with proper session handling and parameter consistency
// src/components/student/MockInterviews/MockInterviews.jsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, Typography, Button, Box, Card, CardContent, 
  Alert, CircularProgress, Grid, Chip 
} from '@mui/material';
import { PlayArrow, Mic, Assessment } from '@mui/icons-material';

const StudentMockInterviews = () => {
  const navigate = useNavigate();
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState(null);
  const [systemReady, setSystemReady] = useState(false);

  useEffect(() => {
    checkSystemReady();
  }, []);

  const checkSystemReady = async () => {
    try {
      console.log('?? Checking if interview system is ready...');
      
      const response = await fetch('https://192.168.48.201:8070/weekly_interview/health', {
        method: 'GET',
        headers: { 'Accept': 'application/json' }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          setSystemReady(true);
          console.log('? Interview system ready!');
        } else {
          throw new Error(`System status: ${data.status}`);
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
      
    } catch (error) {
      console.error('? System check failed:', error);
      setError(`System not ready: ${error.message}`);
      setSystemReady(false);
    }
  };

  const startInterview = async () => {
    try {
      setIsStarting(true);
      setError(null);
      
      console.log('?? FIXED: Starting FRESH AI interview with proper session handling...');
      
      // FIXED: Clear any old session data properly
      localStorage.removeItem('currentSessionId');
      sessionStorage.clear();
      
      // Get fresh session data from corrected endpoint
      const response = await fetch('https://192.168.48.201:8070/weekly_interview/start_interview', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const sessionData = await response.json();
      
      console.log('?? FRESH SESSION DATA:');
      console.log('Full response:', sessionData);
      console.log('NEW session_id:', sessionData.session_id);
      console.log('NEW test_id:', sessionData.test_id);
      
      // FIXED: Validate required session data
      const freshSessionId = sessionData.session_id;
      const freshTestId = sessionData.test_id;
      const studentName = sessionData.student_name || 'Student';
      
      if (!freshSessionId) {
        throw new Error('Backend did not return session_id');
      }
      
      if (!freshTestId) {
        throw new Error('Backend did not return test_id');
      }
      
      console.log('?? FIXED NAVIGATION with proper parameters');
      
      // FIXED: Navigate with consistent parameter naming and proper state
      navigate(`/student/mock-interviews/session/${freshSessionId}`, {
        state: {
          testId: freshTestId,
          studentName: studentName,
          sessionData: sessionData
        }
      });
      
    } catch (error) {
      console.error('? FIXED: Failed to start interview:', error);
      setError(`Failed to start interview: ${error.message}`);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box textAlign="center" mb={4}>
        <Mic sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
        <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
          AI Mock Interview
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Practice your interview skills with AI-powered conversations
        </Typography>
      </Box>

      {/* System Status */}
      <Box mb={4}>
        {systemReady ? (
          <Alert severity="success" sx={{ borderRadius: 2 }}>
            <strong>System Ready!</strong> Interview AI is online and ready for fully automated speech-to-speech conversation.
          </Alert>
        ) : error ? (
          <Alert severity="error" sx={{ borderRadius: 2 }}>
            <strong>System Issue:</strong> {error}
            <Button 
              size="small" 
              onClick={checkSystemReady} 
              sx={{ ml: 2 }}
            >
              Retry
            </Button>
          </Alert>
        ) : (
          <Alert severity="info" sx={{ borderRadius: 2 }}>
            <CircularProgress size={20} sx={{ mr: 1 }} />
            Checking interview system...
          </Alert>
        )}
      </Box>

      {/* Main Interview Card */}
      <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <Assessment sx={{ fontSize: 50, color: 'primary.main', mb: 2 }} />
          
          <Typography variant="h4" gutterBottom>
            Ready for Your Automated Interview?
          </Typography>
          
          <Typography variant="body1" color="text.secondary" paragraph>
            This fully automated AI interviewer will conduct a realistic mock interview with continuous 
            speech-to-speech interaction. No recording buttons needed - just speak naturally!
          </Typography>

          <Box sx={{ my: 3 }}>
            <Grid container spacing={2} justifyContent="center">
              <Grid item>
                <Chip 
                  label="??? Continuous Speech Detection" 
                  variant="outlined" 
                  color="primary" 
                />
              </Grid>
              <Grid item>
                <Chip 
                  label="?? AI-Powered Questions" 
                  variant="outlined" 
                  color="primary" 
                />
              </Grid>
              <Grid item>
                <Chip 
                  label="?? Instant Feedback" 
                  variant="outlined" 
                  color="primary" 
                />
              </Grid>
              <Grid item>
                <Chip 
                  label="?? Automated Turn-Taking" 
                  variant="outlined" 
                  color="success" 
                />
              </Grid>
            </Grid>
          </Box>

          <Button
            variant="contained"
            size="large"
            startIcon={isStarting ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
            onClick={startInterview}
            disabled={!systemReady || isStarting}
            sx={{
              borderRadius: 3,
              py: 1.5,
              px: 4,
              fontSize: '1.1rem',
              fontWeight: 'bold'
            }}
          >
            {isStarting ? 'Starting Interview...' : 'Start Automated AI Interview'}
          </Button>

          {systemReady && (
            <Typography variant="caption" display="block" sx={{ mt: 2, color: 'text.secondary' }}>
              The interview will take approximately 30-45 minutes with automatic speech detection
            </Typography>
          )}
        </CardContent>
      </Card>

      {/* Enhanced Instructions */}
      <Card sx={{ mt: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom color="primary">
            ?? Fully Automated Interview Features:
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                <strong>?? Continuous Operation:</strong>
              </Typography>
              <Typography variant="body2" gutterBottom>
                • No manual recording buttons<br/>
                • Automatic turn-taking detection<br/>
                • Seamless speech-to-speech flow
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                <strong>??? Smart Audio Processing:</strong>
              </Typography>
              <Typography variant="body2" gutterBottom>
                • 2.5 second silence detection<br/>
                • Real-time audio streaming<br/>
                • Natural conversation pacing
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                <strong>?? Personalized Content:</strong>
              </Typography>
              <Typography variant="body2" gutterBottom>
                • Questions based on your recent work<br/>
                • 7-day activity summaries<br/>
                • Relevant technical discussions
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                <strong>?? Comprehensive Assessment:</strong>
              </Typography>
              <Typography variant="body2" gutterBottom>
                • Technical skills evaluation<br/>
                • Communication assessment<br/>
                • Behavioral analysis
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Container>
  );
};

export default StudentMockInterviews;