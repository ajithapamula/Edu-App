// src/components/student/MockTest/MockTestResults.jsx
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Container,
  Grid,
  Paper,
  Chip,
  useTheme,
  alpha,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert
} from '@mui/material';
import {
  EmojiEvents as TrophyIcon,
  Timer as TimerIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  Home as HomeIcon,
  Code as CodeIcon,
  Psychology as PsychologyIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { mockTestAPI } from '../../../services/API/studentmocktest';

const MockTestResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  
  // Extract results data from navigation state
  const navigationState = location.state || {};
  const passedResults = navigationState.results;
  const testType = navigationState.testType || 'developer';
  const testData = navigationState.testData;

  const [results, setResults] = useState(passedResults);
  const [loading, setLoading] = useState(!passedResults);
  const [error, setError] = useState('');
  const [downloadingPDF, setDownloadingPDF] = useState(false);

  // Extract test ID from various possible sources
  const testId = results?.testId || 
                 results?.test_id ||
                 testData?.testId || 
                 testData?.raw?.test_id ||
                 navigationState.testId;

  // Fetch results from API if not passed through navigation
  useEffect(() => {
    const fetchResults = async () => {
      if (passedResults || !testId) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        console.log('Fetching results for test ID:', testId);
        
        const apiResults = await mockTestAPI.getTestResults(testId);
        console.log('API Results received:', apiResults);
        
        if (apiResults) {
          setResults(apiResults);
        } else {
          throw new Error('No results data received from API');
        }
      } catch (error) {
        console.error('Failed to fetch results:', error);
        const errorMessage = mockTestAPI.getErrorMessage(error);
        setError(`Failed to load test results: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [testId, passedResults]);

  const handleDownloadPDF = async () => {
    if (!testId) {
      setError('Test ID not found. Cannot download PDF.');
      return;
    }

    try {
      setDownloadingPDF(true);
      console.log('Downloading PDF for test:', testId);
      
      const pdfBlob = await mockTestAPI.downloadResultsPDF(testId);
      
      // Create download link
      const url = window.URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `mock_test_results_${testId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Failed to download PDF:', error);
      const errorMessage = mockTestAPI.getErrorMessage(error);
      setError(`Failed to download PDF: ${errorMessage}`);
    } finally {
      setDownloadingPDF(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading test results...
        </Typography>
      </Container>
    );
  }

  // Error state
  if (error) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
        <Box sx={{ textAlign: 'center' }}>
          <Button 
            variant="contained" 
            onClick={() => navigate('/student/mock-tests')}
          >
            Go to Mock Tests
          </Button>
        </Box>
      </Container>
    );
  }

  // No results state
  if (!results) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: 'center' }}>
        <Typography variant="h5" color="error" sx={{ mb: 2 }}>
          No test results found. Please take a test first.
        </Typography>
        {process.env.NODE_ENV === 'development' && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Debug info: Test ID = {testId || 'Not found'}
          </Typography>
        )}
        <Button 
          variant="contained" 
          onClick={() => navigate('/student/mock-tests')}
          sx={{ mt: 2 }}
        >
          Go to Mock Tests
        </Button>
      </Container>
    );
  }

  const formatTime = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins} min ${secs} sec`;
  };

  const getScoreColor = (percentage) => {
    if (percentage >= 80) return theme.palette.success.main;
    if (percentage >= 60) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getPerformanceLevel = (percentage) => {
    if (percentage >= 90) return 'Excellent';
    if (percentage >= 80) return 'Very Good';
    if (percentage >= 70) return 'Good';
    if (percentage >= 60) return 'Average';
    return 'Needs Improvement';
  };

  // Extract data from results with proper fallbacks
  const score = results.score || 0;
  const totalQuestions = results.totalQuestions || results.total_questions || (testType === 'developer' ? 5 : 8);
  const percentage = results.scorePercentage || Math.round((score / totalQuestions) * 100) || 0;
  const analytics = results.analytics || 'Evaluation completed successfully.';
  const pdfAvailable = results.pdfAvailable !== false;
  const timestamp = results.timestamp || Date.now();

  const renderDeveloperResults = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card elevation={2} sx={{ height: '100%' }}>
          <CardContent sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <AssignmentIcon sx={{ color: theme.palette.primary.main, mr: 1 }} />
              <Typography variant="h6" fontWeight="bold">
                Test Summary
              </Typography>
            </Box>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <CheckCircleIcon color="success" />
                </ListItemIcon>
                <ListItemText 
                  primary="Questions Completed" 
                  secondary={`${totalQuestions} questions`}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <TrophyIcon color="warning" />
                </ListItemIcon>
                <ListItemText 
                  primary="Score" 
                  secondary={`${score} out of ${totalQuestions}`}
                />
              </ListItem>
              {testId && (
                <ListItem>
                  <ListItemIcon>
                    <AssignmentIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Test ID" 
                    secondary={testId.slice(0, 8) + '...' || 'N/A'}
                  />
                </ListItem>
              )}
            </List>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card elevation={2} sx={{ height: '100%' }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
              Performance Overview
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              Your code solutions have been evaluated and scored.
            </Typography>
            <Chip 
              label={`${percentage}% Score`}
              color={percentage >= 70 ? 'success' : percentage >= 50 ? 'warning' : 'error'}
              sx={{ fontWeight: 'bold', fontSize: '1rem' }}
            />
          </CardContent>
        </Card>
      </Grid>

      {/* Analytics Section for Developer */}
      {analytics && (
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Detailed Feedback
              </Typography>
              <Paper 
                sx={{ 
                  p: 3, 
                  backgroundColor: alpha(theme.palette.primary.main, 0.02),
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
                }}
              >
                <Typography 
                  variant="body2" 
                  sx={{ 
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'inherit',
                    lineHeight: 1.6
                  }}
                >
                  {analytics}
                </Typography>
              </Paper>
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );

  const renderNonDeveloperResults = () => {
    const scoreColor = getScoreColor(percentage);
    
    return (
      <Grid container spacing={3}>
        {/* Score Overview */}
        <Grid item xs={12} md={4}>
          <Card elevation={3} sx={{ textAlign: 'center', p: 3 }}>
            <Box sx={{ position: 'relative', display: 'inline-flex', mb: 2 }}>
              <CircularProgress
                variant="determinate"
                value={percentage}
                size={120}
                thickness={6}
                sx={{
                  color: scoreColor,
                  '& .MuiCircularProgress-circle': {
                    strokeLinecap: 'round',
                  },
                }}
              />
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  bottom: 0,
                  right: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column'
                }}
              >
                <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', color: scoreColor }}>
                  {percentage}%
                </Typography>
              </Box>
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: scoreColor }}>
              {getPerformanceLevel(percentage)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Overall Performance
            </Typography>
          </Card>
        </Grid>

        {/* Detailed Stats */}
        <Grid item xs={12} md={8}>
          <Card elevation={2} sx={{ height: '100%' }}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 3 }}>
                Detailed Results
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <CheckCircleIcon sx={{ fontSize: 40, color: theme.palette.success.main, mb: 1 }} />
                    <Typography variant="h5" fontWeight="bold" color="success.main">
                      {score}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Correct Answers
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <CancelIcon sx={{ fontSize: 40, color: theme.palette.error.main, mb: 1 }} />
                    <Typography variant="h5" fontWeight="bold" color="error.main">
                      {totalQuestions - score}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Incorrect Answers
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <TrophyIcon sx={{ fontSize: 40, color: theme.palette.warning.main, mb: 1 }} />
                    <Typography variant="h5" fontWeight="bold" color="warning.main">
                      {score}/{totalQuestions}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Final Score
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Box sx={{ textAlign: 'center' }}>
                    <AssignmentIcon sx={{ fontSize: 40, color: theme.palette.info.main, mb: 1 }} />
                    <Typography variant="h5" fontWeight="bold" color="info.main">
                      {totalQuestions}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Questions
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Breakdown */}
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                Performance Breakdown
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Chip 
                  label={`${score}/${totalQuestions} Questions Correct`}
                  color="success"
                  variant="outlined"
                />
                <Chip 
                  label={`${percentage}% Accuracy`}
                  sx={{ 
                    backgroundColor: alpha(scoreColor, 0.1),
                    color: scoreColor,
                    borderColor: scoreColor
                  }}
                  variant="outlined"
                />
                <Chip 
                  label={getPerformanceLevel(percentage)}
                  color="primary"
                  variant="outlined"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Analytics Section for Non-Developer */}
        {analytics && (
          <Grid item xs={12}>
            <Card elevation={2}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                  Detailed Feedback
                </Typography>
                <Paper 
                  sx={{ 
                    p: 3, 
                    backgroundColor: alpha(theme.palette.secondary.main, 0.02),
                    border: `1px solid ${alpha(theme.palette.secondary.main, 0.1)}`
                  }}
                >
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'inherit',
                      lineHeight: 1.6
                    }}
                  >
                    {analytics}
                  </Typography>
                </Paper>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Paper 
        elevation={3}
        sx={{ 
          textAlign: 'center', 
          mb: 4, 
          p: 4,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
          borderRadius: 3
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', mb: 2 }}>
          {testType === 'developer' ? (
            <CodeIcon sx={{ fontSize: 60, color: theme.palette.primary.main, mr: 2 }} />
          ) : (
            <PsychologyIcon sx={{ fontSize: 60, color: theme.palette.secondary.main, mr: 2 }} />
          )}
          <TrophyIcon sx={{ fontSize: 80, color: theme.palette.warning.main }} />
        </Box>
        
        <Typography 
          variant="h3" 
          component="h1" 
          gutterBottom
          sx={{ 
            fontWeight: 'bold',
            color: theme.palette.text.primary,
            mb: 2
          }}
        >
          Test Completed!
        </Typography>
        
        <Typography 
          variant="h5" 
          color="text.secondary" 
          sx={{ mb: 2 }}
        >
          {testType === 'developer' ? 'Developer' : 'Non-Developer'} Assessment Results
        </Typography>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Chip 
            label={new Date(timestamp).toLocaleDateString()}
            variant="outlined"
            sx={{ fontSize: '1rem' }}
          />
          {testId && (
            <Chip 
              label={`Test ID: ${testId.slice(0, 8)}...`}
              variant="outlined"
              sx={{ fontSize: '1rem' }}
            />
          )}
        </Box>
      </Paper>

      {/* Results Content */}
      <Box sx={{ mb: 4 }}>
        {testType === 'developer' ? renderDeveloperResults() : renderNonDeveloperResults()}
      </Box>

      {/* Recommendations */}
      {testType === 'non-developer' && (
        <Card elevation={2} sx={{ mb: 4 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
              Recommendations
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {percentage >= 80 ? (
              <Box>
                <Typography variant="body1" sx={{ mb: 2, color: theme.palette.success.main, fontWeight: 'medium' }}>
                  🎉 Excellent performance! You have a strong understanding of the concepts.
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <TrendingUpIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary="Consider taking advanced level assessments" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary="You're ready for leadership or specialized roles" />
                  </ListItem>
                </List>
              </Box>
            ) : percentage >= 60 ? (
              <Box>
                <Typography variant="body1" sx={{ mb: 2, color: theme.palette.warning.main, fontWeight: 'medium' }}>
                  👍 Good performance! With some focused study, you can excel further.
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <TrendingUpIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText primary="Review areas where you scored lower" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <AssignmentIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText primary="Practice with additional mock tests" />
                  </ListItem>
                </List>
              </Box>
            ) : (
              <Box>
                <Typography variant="body1" sx={{ mb: 2, color: theme.palette.error.main, fontWeight: 'medium' }}>
                  📚 Keep learning! Focus on strengthening your foundational knowledge.
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      <AssignmentIcon color="error" />
                    </ListItemIcon>
                    <ListItemText primary="Review fundamental concepts in each category" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <RefreshIcon color="error" />
                    </ListItemIcon>
                    <ListItemText primary="Retake the assessment after studying" />
                  </ListItem>
                </List>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, flexWrap: 'wrap' }}>
        {pdfAvailable && testId && (
          <Button
            variant="outlined"
            size="large"
            startIcon={downloadingPDF ? <CircularProgress size={16} /> : <DownloadIcon />}
            onClick={handleDownloadPDF}
            disabled={downloadingPDF}
            sx={{ 
              py: 1.5, 
              px: 4,
              borderRadius: 3,
              fontWeight: 'bold'
            }}
          >
            {downloadingPDF ? 'Downloading...' : 'Download PDF'}
          </Button>
        )}
        
        <Button
          variant="outlined"
          size="large"
          startIcon={<RefreshIcon />}
          onClick={() => navigate('/student/mock-tests/start')}
          sx={{ 
            py: 1.5, 
            px: 4,
            borderRadius: 3,
            fontWeight: 'bold'
          }}
        >
          Take Another Test
        </Button>
        
        <Button
          variant="contained"
          size="large"
          startIcon={<HomeIcon />}
          onClick={() => navigate('/student/mock-tests')}
          sx={{ 
            py: 1.5, 
            px: 4,
            borderRadius: 3,
            fontWeight: 'bold',
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            '&:hover': {
              background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.secondary.dark})`,
            }
          }}
        >
          Back to Mock Tests
        </Button>
        
        <Button
          variant="outlined"
          size="large"
          startIcon={<AssignmentIcon />}
          onClick={() => navigate('/student/dashboard')}
          sx={{ 
            py: 1.5, 
            px: 4,
            borderRadius: 3,
            fontWeight: 'bold'
          }}
        >
          Go to Dashboard
        </Button>
      </Box>

      {/* Additional Info */}
      <Paper 
        elevation={1} 
        sx={{ 
          mt: 4, 
          p: 3, 
          textAlign: 'center',
          backgroundColor: alpha(theme.palette.info.main, 0.05),
          border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`
        }}
      >
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          💡 <strong>Tip:</strong> Regular practice with mock tests helps improve your performance and confidence.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Your test history and progress are saved in your profile for future reference.
        </Typography>
      </Paper>
    </Container>
  );
};

export default MockTestResults;