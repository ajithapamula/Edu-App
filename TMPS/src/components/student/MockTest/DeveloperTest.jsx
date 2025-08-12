// src/components/student/MockTest/DeveloperTest.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Container,
  LinearProgress,
  Paper,
  Chip,
  useTheme,
  alpha,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Code as CodeIcon,
  Timer as TimerIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  NavigateNext as NavigateNextIcon,
  Send as SendIcon
} from '@mui/icons-material';
import { mockTestAPI } from '../../../services/API/studentmocktest';

const DeveloperTest = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  
  // Extract test data from navigation state with proper fallback
  const navigationState = location.state || {};
  const testData = navigationState.testData || navigationState;
  
  // Extract test configuration with multiple fallback sources
  const testId = testData?.testId || testData?.raw?.test_id || navigationState.testId;
  const sessionId = testData?.sessionId || testData?.raw?.session_id || navigationState.sessionId;
  const userType = testData?.userType || testData?.raw?.user_type || navigationState.userType || 'dev';
  const totalQuestions = testData?.totalQuestions || testData?.raw?.total_questions || navigationState.totalQuestions || 5;
  const timeLimit = testData?.timeLimit || testData?.raw?.time_limit || navigationState.timeLimit || 300;

  // Initialize current question state
  const initializeCurrentQuestion = () => {
    if (testData?.currentQuestion) {
      return {
        question: testData.currentQuestion.questionHtml || '',
        questionNumber: testData.currentQuestion.questionNumber || 1,
        options: testData.currentQuestion.options || null,
        rawQuestion: testData.currentQuestion.questionHtml || ''
      };
    } else if (testData?.raw) {
      return {
        question: testData.raw.question_html || '',
        questionNumber: testData.raw.question_number || 1,
        options: testData.raw.options || null,
        rawQuestion: testData.raw.question_html || ''
      };
    }
    return {
      question: '',
      questionNumber: 1,
      options: null,
      rawQuestion: ''
    };
  };

  const [currentQuestion, setCurrentQuestion] = useState(initializeCurrentQuestion);
  const [answer, setAnswer] = useState('');
  const [timeLeft, setTimeLeft] = useState(timeLimit);
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [testCompleted, setTestCompleted] = useState(false);
  const [results, setResults] = useState(null);

  const progress = (currentQuestion.questionNumber / totalQuestions) * 100;

  // Redirect if no test data
  useEffect(() => {
    console.log('DeveloperTest loaded with data:', {
      navigationState,
      testData,
      testId,
      currentQuestion
    });
    
    if (!testId || !currentQuestion.question) {
      console.warn('No test data found, redirecting to test start');
      setError('Test data not found. Please start a new test.');
      setTimeout(() => {
        navigate('/student/mock-tests/start');
      }, 3000);
    }
  }, [testId, currentQuestion.question, navigate]);

  // Timer effect
  useEffect(() => {
    if (testCompleted || loading || !testId) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          handleSubmitAnswer(true); // Auto-submit when time runs out
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [testCompleted, loading, currentQuestion.questionNumber, testId]);

  // Reset timer when question changes
  useEffect(() => {
    setTimeLeft(timeLimit);
  }, [currentQuestion.questionNumber, timeLimit]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleAnswerChange = (event) => {
    setAnswer(event.target.value);
  };

  const handleSubmitAnswer = async (isAutoSubmit = false) => {
    if (!testId) {
      setError('Test ID is missing. Cannot submit answer.');
      return;
    }

    if (!isAutoSubmit && !answer.trim()) {
      setError('Please provide an answer before submitting.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      console.log('Submitting answer:', {
        testId,
        questionNumber: currentQuestion.questionNumber,
        answer: answer.trim() || 'No answer provided'
      });

      // Validate answer data before submitting
      const validation = mockTestAPI.validateAnswerData(
        testId, 
        currentQuestion.questionNumber, 
        answer.trim() || 'No answer provided'
      );

      if (!validation.isValid) {
        setError(`Validation error: ${validation.errors.join(', ')}`);
        setSubmitting(false);
        return;
      }

      const response = await mockTestAPI.submitAnswerWithData(
        testId,
        currentQuestion.questionNumber,
        answer.trim() || 'No answer provided'
      );

      console.log('Submit response:', response);

      if (response.testCompleted) {
        // Test is finished
        setTestCompleted(true);
        setResults(response);
        
        // Navigate to results page with complete data
        navigate('/student/mock-tests/results', { 
          state: { 
            results: {
              ...response,
              testId: testId,
              userType: userType,
              totalQuestions: totalQuestions
            }, 
            testType: 'developer',
            testData: testData
          } 
        });
      } else if (response.nextQuestion) {
        // Move to next question
        const nextQuestion = response.nextQuestion;
        setCurrentQuestion({
          question: nextQuestion.questionHtml,
          questionNumber: nextQuestion.questionNumber,
          options: nextQuestion.options,
          rawQuestion: nextQuestion.questionHtml
        });
        setAnswer(''); // Clear answer for next question
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
      const errorMessage = mockTestAPI.getErrorMessage(error);
      setError(`Failed to submit answer: ${errorMessage}`);
    } finally {
      setSubmitting(false);
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'Easy': return theme.palette.success.main;
      case 'Medium': return theme.palette.warning.main;
      case 'Hard': return theme.palette.error.main;
      default: return theme.palette.info.main;
    }
  };

  const getQuestionPlaceholder = () => {
    return `// Write your solution here
function solution() {
  // Your code here
  
}

// Explanation:
// Time Complexity: O(n)
// Space Complexity: O(1)
// Approach: Describe your approach here...`;
  };

  // Loading state
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Processing your answer...
        </Typography>
      </Container>
    );
  }

  // Error state if no question data
  if (!currentQuestion.question && !loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
        <Alert severity="error" sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>No Question Data Available</Typography>
          <Typography variant="body2" sx={{ mb: 2 }}>
            The test question couldn't be loaded. This might be due to:
          </Typography>
          <ul style={{ textAlign: 'left', marginBottom: '16px' }}>
            <li>Test wasn't started properly</li>
            <li>Session data is missing or corrupted</li>
            <li>Network connection issues</li>
            <li>Server is temporarily unavailable</li>
          </ul>
          {process.env.NODE_ENV === 'development' && (
            <Typography variant="body2" component="pre" sx={{ 
              fontSize: '0.8rem', 
              backgroundColor: 'rgba(0,0,0,0.1)', 
              p: 1, 
              borderRadius: 1,
              textAlign: 'left'
            }}>
              {JSON.stringify({ 
                testId, 
                hasTestData: !!testData, 
                navigationState,
                currentQuestion
              }, null, 2)}
            </Typography>
          )}
        </Alert>
        
        <Button 
          variant="contained" 
          onClick={() => navigate('/student/mock-tests/start')}
        >
          Start New Test
        </Button>
      </Container>
    );
  }

  // Test completed state
  if (testCompleted && results) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
        <Typography variant="h4" sx={{ mb: 4, color: theme.palette.success.main }}>
          🎉 Test Completed!
        </Typography>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Your Score: {results.score} / {results.totalQuestions}
        </Typography>
        <Typography variant="body1" sx={{ mb: 4 }}>
          Redirecting to detailed results...
        </Typography>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Header with Progress */}
      <Paper elevation={2} sx={{ p: 3, mb: 4, borderRadius: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CodeIcon sx={{ fontSize: 32, color: theme.palette.primary.main }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
              Developer Assessment
            </Typography>
            {testId && (
              <Chip 
                label={`Test ID: ${testId.slice(0, 8)}...`} 
                size="small" 
                variant="outlined" 
                color="primary"
              />
            )}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <Chip
              icon={<TimerIcon />}
              label={formatTime(timeLeft)}
              color={timeLeft < 60 ? 'error' : 'primary'}
              sx={{ fontSize: '1rem', fontWeight: 'bold' }}
            />
            <Typography variant="body1" color="text.secondary">
              Question {currentQuestion.questionNumber} of {totalQuestions}
            </Typography>
          </Box>
        </Box>
        
        <LinearProgress 
          variant="determinate" 
          value={progress} 
          sx={{ 
            height: 8, 
            borderRadius: 4,
            backgroundColor: alpha(theme.palette.primary.main, 0.1),
            '& .MuiLinearProgress-bar': {
              borderRadius: 4,
              background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
            }
          }} 
        />
      </Paper>

      {/* Question Card */}
      <Card elevation={3} sx={{ mb: 4, borderRadius: 3 }}>
        <CardContent sx={{ p: 4 }}>
          {/* Question Header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
            <Box>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip 
                  label="Programming" 
                  variant="outlined"
                  sx={{ fontWeight: 'bold' }}
                />
                <Chip 
                  label="Medium"
                  sx={{ 
                    backgroundColor: getDifficultyColor('Medium'),
                    color: 'white',
                    fontWeight: 'bold'
                  }}
                />
                <Chip 
                  label="10 points"
                  color="primary"
                  variant="outlined"
                />
              </Box>
            </Box>
            {answer.trim() && (
              <CheckCircleIcon sx={{ color: theme.palette.success.main, fontSize: 32 }} />
            )}
          </Box>

          {/* Question */}
          <Box 
            sx={{ 
              mb: 3, 
              lineHeight: 1.6,
              color: theme.palette.text.primary,
              fontWeight: 'medium',
              '& h1, & h2, & h3, & h4, & h5, & h6': { 
                fontSize: '1.25rem', 
                fontWeight: 'bold', 
                mb: 2,
                color: theme.palette.text.primary
              },
              '& p': { mb: 2 },
              '& pre': { 
                backgroundColor: alpha(theme.palette.primary.main, 0.05),
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontFamily: 'Monaco, Consolas, "Courier New", monospace'
              },
              '& code': {
                backgroundColor: alpha(theme.palette.primary.main, 0.1),
                padding: '2px 6px',
                borderRadius: 1,
                fontFamily: 'Monaco, Consolas, "Courier New", monospace'
              },
              '& ul, & ol': { 
                pl: 3, 
                mb: 2 
              },
              '& li': { 
                mb: 1 
              }
            }}
            dangerouslySetInnerHTML={{ __html: currentQuestion.question }}
          />

          {/* Answer Field */}
          <TextField
            multiline
            rows={12}
            fullWidth
            placeholder={getQuestionPlaceholder()}
            value={answer}
            onChange={handleAnswerChange}
            sx={{
              '& .MuiOutlinedInput-root': {
                fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                fontSize: '0.9rem',
                lineHeight: 1.5,
                backgroundColor: alpha(theme.palette.primary.main, 0.02),
                '&:hover': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.04),
                },
                '&.Mui-focused': {
                  backgroundColor: alpha(theme.palette.primary.main, 0.06),
                }
              }
            }}
          />
        </CardContent>
      </Card>

      {/* Submit Button */}
      <Box sx={{ display: 'flex', justifyContent: 'center' }}>
        {currentQuestion.questionNumber === totalQuestions ? (
          <Button
            variant="contained"
            size="large"
            startIcon={submitting ? <CircularProgress size={16} color="inherit" /> : <SendIcon />}
            onClick={() => setShowSubmitDialog(true)}
            disabled={submitting || (!answer.trim())}
            sx={{ 
              py: 1.5, 
              px: 4,
              background: `linear-gradient(45deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`,
              '&:hover': {
                background: `linear-gradient(45deg, ${theme.palette.success.dark}, ${theme.palette.success.main})`,
              }
            }}
          >
            {submitting ? 'Submitting...' : 'Finish Test'}
          </Button>
        ) : (
          <Button
            variant="contained"
            size="large"
            endIcon={submitting ? <CircularProgress size={16} color="inherit" /> : <NavigateNextIcon />}
            onClick={() => handleSubmitAnswer()}
            disabled={submitting || (!answer.trim())}
            sx={{ py: 1.5, px: 4 }}
          >
            {submitting ? 'Submitting...' : 'Next Question'}
          </Button>
        )}
      </Box>

      {/* Submit Confirmation Dialog */}
      <Dialog open={showSubmitDialog} onClose={() => setShowSubmitDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="warning" />
          Finish Test
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Are you sure you want to finish the test? This is the last question.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Time remaining: {formatTime(timeLeft)}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Answer length: {answer.trim().length} characters
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSubmitDialog(false)} disabled={submitting}>
            Continue
          </Button>
          <Button 
            onClick={() => {
              setShowSubmitDialog(false);
              handleSubmitAnswer();
            }} 
            variant="contained" 
            color="success"
            startIcon={submitting ? <CircularProgress size={16} color="inherit" /> : <SendIcon />}
            disabled={submitting}
          >
            {submitting ? 'Submitting...' : 'Finish Test'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default DeveloperTest;