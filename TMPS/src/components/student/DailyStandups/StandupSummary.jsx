import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Avatar,
  Chip,
  Divider,
  Grid,
  Fade,
  useTheme,
  alpha,
  IconButton
} from '@mui/material';
import {
  Assignment, // Changed from Summary to Assignment
  CheckCircle,
  Schedule,
  Block,
  ArrowBack,
  Download,
  Share,
  Print
} from '@mui/icons-material';
import { useParams, useNavigate, useLocation } from 'react-router-dom';

// Import the standup API
import { standupCallAPI } from '../../../services/API/studentstandup';

const StandupSummary = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  
  const [summary, setSummary] = useState(location.state?.summary || null);
  const [loading, setLoading] = useState(!summary);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!summary && testId) {
      fetchSummary();
    }
  }, [testId, summary]);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const summaryData = await standupCallAPI.getStandupSummary(testId);
      setSummary(summaryData);
      
    } catch (err) {
      console.error('Error fetching summary:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoBack = () => {
    navigate('/student/daily-standups');
  };

  const handleStartNewStandup = () => {
    navigate('/student/daily-standups');
  };

  const handleDownload = () => {
    // Create a downloadable summary
    const summaryText = generateSummaryText();
    const blob = new Blob([summaryText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `standup-summary-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const generateSummaryText = () => {
    if (!summary) return '';
    
    const date = new Date().toLocaleDateString();
    return `
Daily Standup Summary - ${date}
=====================================

Yesterday's Accomplishments:
${summary.yesterday || summary.accomplishments || 'Not provided'}

Today's Plans:
${summary.today || summary.plans || 'Not provided'}

Blockers/Challenges:
${summary.blockers || summary.challenges || 'None mentioned'}

Additional Notes:
${summary.notes || summary.additional_info || 'None'}

Session ID: ${testId}
Generated: ${new Date().toLocaleString()}
    `.trim();
  };

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6">Loading summary...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" color="error" gutterBottom>
          Error loading summary
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {error}
        </Typography>
        <Button variant="contained" onClick={handleGoBack} sx={{ mt: 2 }}>
          Go Back
        </Button>
      </Box>
    );
  }

  return (
    <Fade in={true}>
      <Box sx={{ p: 3, minHeight: '100vh', backgroundColor: alpha(theme.palette.primary.main, 0.02) }}>
        {/* Header */}
        <Box 
          display="flex" 
          justifyContent="space-between" 
          alignItems="center" 
          mb={4}
          sx={{
            background: `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.1)}, ${alpha(theme.palette.primary.main, 0.1)})`,
            p: 3,
            borderRadius: 3,
            backdropFilter: 'blur(10px)',
            border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`
          }}
        >
          <Box display="flex" alignItems="center" gap={2}>
            <IconButton onClick={handleGoBack} sx={{ mr: 1 }}>
              <ArrowBack />
            </IconButton>
            <Avatar 
              sx={{ 
                bgcolor: theme.palette.success.main,
                width: 48,
                height: 48,
                boxShadow: theme.shadows[8]
              }}
            >
              <Assignment />
            </Avatar>
            <Box>
              <Typography 
                variant="h5" 
                component="h1"
                sx={{
                  background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.primary.main})`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  fontWeight: 'bold'
                }}
              >
                Standup Summary
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {new Date().toLocaleDateString()} • Session ID: {testId}
              </Typography>
            </Box>
          </Box>
          
          <Box display="flex" alignItems="center" gap={1}>
            <Chip 
              label="Completed"
              color="success"
              icon={<CheckCircle />}
            />
          </Box>
        </Box>

        {/* Action Buttons */}
        <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={handleDownload}
          >
            Download
          </Button>
          <Button
            variant="outlined"
            startIcon={<Print />}
            onClick={() => window.print()}
          >
            Print
          </Button>
          <Button
            variant="contained"
            onClick={handleStartNewStandup}
            sx={{ ml: 'auto' }}
          >
            Start New Standup
          </Button>
        </Box>

        <Grid container spacing={3}>
          {/* Yesterday's Accomplishments */}
          <Grid item xs={12} md={6}>
            <Card 
              sx={{
                borderRadius: 3,
                boxShadow: theme.shadows[4],
                background: `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.05)}, ${alpha(theme.palette.success.light, 0.05)})`,
                border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Avatar sx={{ bgcolor: theme.palette.success.main, width: 40, height: 40 }}>
                    <CheckCircle />
                  </Avatar>
                  <Typography variant="h6" color="success.main">
                    Yesterday's Accomplishments
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                  {summary?.yesterday || summary?.accomplishments || 'No accomplishments recorded'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Today's Plans */}
          <Grid item xs={12} md={6}>
            <Card 
              sx={{
                borderRadius: 3,
                boxShadow: theme.shadows[4],
                background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.05)}, ${alpha(theme.palette.primary.light, 0.05)})`,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Avatar sx={{ bgcolor: theme.palette.primary.main, width: 40, height: 40 }}>
                    <Schedule />
                  </Avatar>
                  <Typography variant="h6" color="primary.main">
                    Today's Plans
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                  {summary?.today || summary?.plans || 'No plans recorded'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Blockers/Challenges */}
          <Grid item xs={12} md={6}>
            <Card 
              sx={{
                borderRadius: 3,
                boxShadow: theme.shadows[4],
                background: `linear-gradient(135deg, ${alpha(theme.palette.warning.main, 0.05)}, ${alpha(theme.palette.warning.light, 0.05)})`,
                border: `1px solid ${alpha(theme.palette.warning.main, 0.2)}`
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Avatar sx={{ bgcolor: theme.palette.warning.main, width: 40, height: 40 }}>
                    <Block />
                  </Avatar>
                  <Typography variant="h6" color="warning.main">
                    Blockers & Challenges
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                  {summary?.blockers || summary?.challenges || 'No blockers mentioned'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Additional Notes */}
          <Grid item xs={12} md={6}>
            <Card 
              sx={{
                borderRadius: 3,
                boxShadow: theme.shadows[4],
                background: `linear-gradient(135deg, ${alpha(theme.palette.info.main, 0.05)}, ${alpha(theme.palette.info.light, 0.05)})`,
                border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Avatar sx={{ bgcolor: theme.palette.info.main, width: 40, height: 40 }}>
                    <Assignment />
                  </Avatar>
                  <Typography variant="h6" color="info.main">
                    Additional Notes
                  </Typography>
                </Box>
                <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                  {summary?.notes || summary?.additional_info || 'No additional notes'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Session Details */}
        <Paper 
          sx={{ 
            mt: 4, 
            p: 3, 
            borderRadius: 2,
            bgcolor: alpha(theme.palette.grey[100], 0.5)
          }}
        >
          <Typography variant="h6" gutterBottom>
            Session Details
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Session ID
              </Typography>
              <Typography variant="body1" fontFamily="monospace">
                {testId}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Date
              </Typography>
              <Typography variant="body1">
                {new Date().toLocaleDateString()}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Time
              </Typography>
              <Typography variant="body1">
                {new Date().toLocaleTimeString()}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Status
              </Typography>
              <Chip label="Completed" color="success" size="small" />
            </Grid>
          </Grid>
        </Paper>
      </Box>
    </Fade>
  );
};

export default StandupSummary;