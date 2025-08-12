// src/components/student/MockTest/NonDeveloperTest.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Container,
  LinearProgress,
  Paper,
  Chip,
  RadioGroup,
  FormControlLabel,
  Radio,
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
  Psychology as PsychologyIcon,
  Timer as TimerIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  NavigateNext as NavigateNextIcon,
  Send as SendIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
  RadioButtonChecked as RadioButtonCheckedIcon
} from '@mui/icons-material';
import { mockTestAPI } from '../../../services/API/studentmocktest';

const NonDeveloperTest = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  
  // Extract test data from navigation state with proper fallback
  const navigationState = location.state || {};
  const testData = navigationState.testData || navigationState;
  
  // Extract test configuration with multiple fallback sources
  const testId = testData?.testId || testData?.raw?.test_id || navigationState.testId;
  const sessionId = testData?.sessionId || testData?.raw?.session_id || navigationState.sessionId;
  const userType = testData?.userType || testData?.raw?.user_type || navigationState.userType || 'non_dev';
  const totalQuestions = testData?.totalQuestions || testData?.raw?.total_questions || navigationState.totalQuestions || 8;
  const timeLimit = testData?.timeLimit || testData?.raw?.time_limit || navigationState.timeLimit || 120;

  // Initialize current question state
  const initializeCurrentQuestion = () => {
    if (testData?.currentQuestion) {
      return {
        question: testData.currentQuestion.questionHtml || '',
        questionNumber: testData.currentQuestion.questionNumber || 1,
        options: testData.currentQuestion.options || [],
        rawQuestion: testData.currentQuestion.questionHtml || ''
      };
    } else if (testData?.raw) {
      return {
        question: testData.raw.question_html || '',
        questionNumber: testData.raw.question_number || 1,
        options: testData.raw.options || [],
        rawQuestion: testData.raw.question_html || ''
      };
    }
    return {
      question: '',
      questionNumber: 1,
      options: [],
      rawQuestion: ''
    };
  };

  const [currentQuestion, setCurrentQuestion] = useState(initializeCurrentQuestion);
  const [selectedAnswer, setSelectedAnswer] = useState('');
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
    console.log('NonDeveloperTest loaded with data:', {
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
    setSelectedAnswer(event.target.value);
  };

  const handleSubmitAnswer = async (isAutoSubmit = false) => {
    if (!testId) {
      setError('Test ID is missing. Cannot submit answer.');
      return;
    }

    if (!isAutoSubmit && selectedAnswer === '') {
      setError('Please select an answer before submitting.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      // Convert answer to option text if it's an index
      let answerToSubmit = selectedAnswer;
      if (selectedAnswer !== '' && currentQuestion.options && currentQuestion.options.length > 0) {
        const answerIndex = parseInt(selectedAnswer);
        if (!isNaN(answerIndex) && answerIndex >= 0 && answerIndex < currentQuestion.options.length) {
          answerToSubmit = currentQuestion.options[answerIndex];
        }
      }

      // Default to first option if auto-submit with no selection
      if (isAutoSubmit && selectedAnswer === '' && currentQuestion.options && currentQuestion.options.length > 0) {
        answerToSubmit = currentQuestion.options[0];
      }

      console.log('Submitting answer:', {
        testId,
        questionNumber: currentQuestion.questionNumber,
        selectedIndex: selectedAnswer,
        answerText: answerToSubmit
      });

      // Validate answer data before submitting
      const validation = mockTestAPI.validateAnswerData(
        testId, 
        currentQuestion.questionNumber, 
        answerToSubmit
      );

      if (!validation.isValid) {
        setError(`Validation error: ${validation.errors.join(', ')}`);
        setSubmitting(false);
        return;
      }

      const response = await mockTestAPI.submitAnswerWithData(
        testId,
        currentQuestion.questionNumber,
        answerToSubmit
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
            testType: 'non-developer',
            testData: testData
          } 
        });
      } else if (response.nextQuestion) {
        // Move to next question
        const nextQuestion = response.nextQuestion;
        setCurrentQuestion({
          question: nextQuestion.questionHtml,
          questionNumber: nextQuestion.questionNumber,
          options: nextQuestion.options || [],
          rawQuestion: nextQuestion.questionHtml
        });
        setSelectedAnswer(''); // Clear selection for next question
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

  const getTimerColor = (timeLeft, totalTime) => {
    const percentage = (timeLeft / totalTime) * 100;
    if (percentage <= 10) return 'error';
    if (percentage <= 25) return 'warning';
    return 'secondary';
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'Easy': return theme.palette.success.main;
      case 'Medium': return theme.palette.warning.main;
      case 'Hard': return theme.palette.error.main;
      default: return theme.palette.info.main;
    }
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
            <PsychologyIcon sx={{ fontSize: 32, color: theme.palette.secondary.main }} />
            <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
              Non-Developer Assessment
            </Typography>
            {testId && (
              <Chip 
                label={`Test ID: ${testId.slice(0, 8)}...`} 
                size="small" 
                variant="outlined" 
                color="secondary"
              />
            )}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <Chip
              icon={<TimerIcon />}
              label={formatTime(timeLeft)}
              color={getTimerColor(timeLeft, timeLimit)}
              sx={{ 
                fontSize: '1rem', 
                fontWeight: 'bold',
                animation: timeLeft <= 30 ? 'pulse 1s infinite' : 'none',
                '@keyframes pulse': {
                  '0%': { transform: 'scale(1)' },
                  '50%': { transform: 'scale(1.05)' },
                  '100%': { transform: 'scale(1)' }
                }
              }}
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
            backgroundColor: alpha(theme.palette.secondary.main, 0.1),
            '& .MuiLinearProgress-bar': {
              borderRadius: 4,
              background: `linear-gradient(90deg, ${theme.palette.secondary.main}, ${theme.palette.primary.main})`
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
                  label="Multiple Choice" 
                  variant="outlined"
                  color="secondary"
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
                  color="secondary"
                  variant="outlined"
                />
              </Box>
            </Box>
            {selectedAnswer !== '' && (
              <CheckCircleIcon sx={{ color: theme.palette.success.main, fontSize: 32 }} />
            )}
          </Box>

          {/* Question */}
          <Box 
            sx={{ 
              mb: 4, 
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
                backgroundColor: alpha(theme.palette.secondary.main, 0.05),
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontFamily: 'Monaco, Consolas, "Courier New", monospace'
              },
              '& code': {
                backgroundColor: alpha(theme.palette.secondary.main, 0.1),
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

          {/* Answer Options */}
          <RadioGroup
            value={selectedAnswer}
            onChange={handleAnswerChange}
          >
            {(currentQuestion.options || []).map((option, index) => (
              <Paper
                key={index}
                elevation={selectedAnswer === index.toString() ? 3 : 1}
                sx={{
                  mb: 2,
                  borderRadius: 2,
                  border: selectedAnswer === index.toString() 
                    ? `2px solid ${theme.palette.secondary.main}` 
                    : '2px solid transparent',
                  backgroundColor: selectedAnswer === index.toString() 
                    ? alpha(theme.palette.secondary.main, 0.05) 
                    : 'background.paper',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    backgroundColor: alpha(theme.palette.secondary.main, 0.02),
                    transform: 'translateY(-1px)',
                    boxShadow: theme.shadows[4]
                  }
                }}
              >
                <FormControlLabel
                  value={index.toString()}
                  control={
                    <Radio 
                      sx={{ 
                        color: theme.palette.secondary.main,
                        '&.Mui-checked': {
                          color: theme.palette.secondary.main,
                        }
                      }}
                      icon={<RadioButtonUncheckedIcon />}
                      checkedIcon={<RadioButtonCheckedIcon />}
                    />
                  }
                  label={
                    <Typography 
                      variant="body1" 
                      sx={{ 
                        py: 1,
                        fontWeight: selectedAnswer === index.toString() ? 'bold' : 'normal',
                        color: selectedAnswer === index.toString() 
                          ? theme.palette.secondary.main 
                          : 'text.primary'
                      }}
                    >
                      {String.fromCharCode(65 + index)}. {option}
                    </Typography>
                  }
                  sx={{ 
                    width: '100%', 
                    m: 0, 
                    p: 2,
                    borderRadius: 2
                  }}
                />
              </Paper>
            ))}
          </RadioGroup>
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
            disabled={submitting || selectedAnswer === ''}
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
            disabled={submitting || selectedAnswer === ''}
            color="secondary"
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
            Selected answer: {selectedAnswer !== '' ? `Option ${String.fromCharCode(65 + parseInt(selectedAnswer))}` : 'None'}
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

export default NonDeveloperTest;