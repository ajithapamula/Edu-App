// src/components/student/MockTest/MockTestStart.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Button,
  Container,
  Grid,
  Paper,
  RadioGroup,
  FormControlLabel,
  Radio,
  useTheme,
  alpha,
  Fade,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Code as CodeIcon,
  Psychology as PsychologyIcon,
  ArrowForward as ArrowForwardIcon,
  Quiz as QuizIcon,
  Create as CreateIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { mockTestAPI } from '../../../services/API/studentmocktest';

const MockTestStart = () => {
  const [selectedUserType, setSelectedUserType] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const theme = useTheme();

  const handleUserTypeChange = (event) => {
    setSelectedUserType(event.target.value);
    setError(''); // Clear any previous errors
  };

  const handleStartTest = async () => {
    if (!selectedUserType) {
      setError('Please select a user type before starting the test.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Prepare test configuration with proper format
      const testConfig = {
        user_type: selectedUserType === 'developer' ? 'dev' : 'non_dev',
        userType: selectedUserType, // Keep original for reference
        student_id: localStorage.getItem('studentId') || 'student123',
        timestamp: Date.now()
      };

      console.log('Starting test with config:', testConfig);

      // Validate configuration before sending
      const validation = mockTestAPI.validateTestConfig(testConfig);
      if (!validation.isValid) {
        setError(`Configuration error: ${validation.errors.join(', ')}`);
        setLoading(false);
        return;
      }

      // Start the test via API
      const testData = await mockTestAPI.startTestWithConfig(testConfig);
      
      console.log('Test started successfully:', testData);

      // Prepare navigation state with complete data structure
      const navigationState = {
        testData: {
          testId: testData.testId,
          sessionId: testData.sessionId,
          userType: testData.userType,
          totalQuestions: testData.totalQuestions,
          timeLimit: testData.timeLimit,
          duration: testData.duration,
          raw: testData.raw,
          currentQuestion: testData.currentQuestion
        },
        // Additional fields for backward compatibility
        testId: testData.testId,
        sessionId: testData.sessionId,
        userType: testData.userType,
        totalQuestions: testData.totalQuestions,
        timeLimit: testData.timeLimit,
        questions: [testData.currentQuestion], // First question
        duration: testData.duration
      };

      console.log('Navigation state prepared:', navigationState);

      // Navigate to appropriate test component based on user type
      if (selectedUserType === 'developer') {
        navigate('/student/mock-tests/developer-test', { 
          state: navigationState
        });
      } else {
        navigate('/student/mock-tests/non-developer-test', { 
          state: navigationState
        });
      }

    } catch (error) {
      console.error('Failed to start test:', error);
      const errorMessage = mockTestAPI.getErrorMessage(error);
      setError(`Failed to start test: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const userTypes = [
    {
      value: 'developer',
      title: 'Developer',
      subtitle: 'Code writing, debugging, scenarios',
      icon: <CodeIcon sx={{ fontSize: 60, color: theme.palette.primary.main }} />,
      description: 'Perfect for software developers, programmers, and technical professionals',
      features: [
        'Text-based coding questions',
        'Algorithm challenges',
        'Debugging scenarios',
        'System design problems',
        'Best practices assessment'
      ],
      color: theme.palette.primary.main,
      bgColor: alpha(theme.palette.primary.main, 0.05),
      duration: '45 minutes',
      questionCount: '5 questions'
    },
    {
      value: 'non-developer',
      title: 'Non-Developer',
      subtitle: 'Multiple choice questions',
      icon: <PsychologyIcon sx={{ fontSize: 60, color: theme.palette.secondary.main }} />,
      description: 'Ideal for managers, analysts, designers, and non-technical roles',
      features: [
        'Multiple choice format',
        'Quick assessment',
        'Theory-based questions',
        'Conceptual understanding',
        'Industry knowledge test'
      ],
      color: theme.palette.secondary.main,
      bgColor: alpha(theme.palette.secondary.main, 0.05),
      duration: '30 minutes',
      questionCount: '8 questions'
    }
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Paper 
        elevation={0}
        sx={{ 
          textAlign: 'center', 
          mb: 6, 
          p: 4,
          background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
          borderRadius: 3
        }}
      >
        <QuizIcon sx={{ fontSize: 80, color: theme.palette.primary.main, mb: 2 }} />
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
          Select Your User Type
        </Typography>
        <Typography 
          variant="h6" 
          color="text.secondary" 
          sx={{ maxWidth: 600, mx: 'auto', lineHeight: 1.6 }}
        >
          Choose the test format that best matches your role and expertise level
        </Typography>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* User Type Selection */}
      <RadioGroup
        value={selectedUserType}
        onChange={handleUserTypeChange}
        sx={{ mb: 4 }}
      >
        <Grid container spacing={4}>
          {userTypes.map((userType) => (
            <Grid item xs={12} md={6} key={userType.value}>
              <Fade in timeout={600}>
                <Card 
                  elevation={selectedUserType === userType.value ? 8 : 2}
                  sx={{ 
                    height: '100%',
                    border: selectedUserType === userType.value 
                      ? `3px solid ${userType.color}` 
                      : `2px solid transparent`,
                    backgroundColor: selectedUserType === userType.value 
                      ? userType.bgColor 
                      : 'background.paper',
                    transition: 'all 0.3s ease-in-out',
                    position: 'relative',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: theme.shadows[12]
                    }
                  }}
                >
                  <CardActionArea sx={{ height: '100%' }} onClick={() => setSelectedUserType(userType.value)}>
                    <CardContent sx={{ p: 4, height: '100%', display: 'flex', flexDirection: 'column' }}>
                      {/* Selection Indicator */}
                      {selectedUserType === userType.value && (
                        <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
                          <CheckCircleIcon sx={{ color: userType.color, fontSize: 32 }} />
                        </Box>
                      )}

                      {/* Icon and Title */}
                      <Box sx={{ textAlign: 'center', mb: 3 }}>
                        {userType.icon}
                        <Typography 
                          variant="h4" 
                          component="h3" 
                          sx={{ 
                            mt: 2, 
                            mb: 1, 
                            fontWeight: 'bold',
                            color: userType.color
                          }}
                        >
                          {userType.title}
                        </Typography>
                        <Typography variant="subtitle1" color="text.secondary" sx={{ fontWeight: 'medium' }}>
                          {userType.subtitle}
                        </Typography>
                        
                        {/* Test Info */}
                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', mt: 2 }}>
                          <Chip 
                            label={userType.duration} 
                            size="small" 
                            color="primary" 
                            variant="outlined" 
                          />
                          <Chip 
                            label={userType.questionCount} 
                            size="small" 
                            color="secondary" 
                            variant="outlined" 
                          />
                        </Box>
                      </Box>

                      {/* Description */}
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          mb: 3, 
                          textAlign: 'center',
                          color: 'text.secondary',
                          lineHeight: 1.6
                        }}
                      >
                        {userType.description}
                      </Typography>

                      {/* Features */}
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'text.primary' }}>
                          What you'll get:
                        </Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          {userType.features.map((feature, index) => (
                            <Chip
                              key={index}
                              label={feature}
                              size="small"
                              icon={<CreateIcon sx={{ fontSize: 16 }} />}
                              sx={{
                                justifyContent: 'flex-start',
                                backgroundColor: alpha(userType.color, 0.1),
                                color: userType.color,
                                fontWeight: 'medium',
                                '& .MuiChip-icon': {
                                  color: userType.color
                                }
                              }}
                            />
                          ))}
                        </Box>
                      </Box>

                      {/* Radio Button */}
                      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
                        <FormControlLabel
                          value={userType.value}
                          control={
                            <Radio 
                              sx={{ 
                                color: userType.color,
                                '&.Mui-checked': {
                                  color: userType.color,
                                }
                              }} 
                            />
                          }
                          label={
                            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                              Select {userType.title}
                            </Typography>
                          }
                        />
                      </Box>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Fade>
            </Grid>
          ))}
        </Grid>
      </RadioGroup>

      {/* Start Test Button */}
      <Fade in={!!selectedUserType} timeout={400}>
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleStartTest}
            disabled={!selectedUserType || loading}
            endIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ArrowForwardIcon />}
            sx={{
              py: 2,
              px: 6,
              fontSize: '1.2rem',
              fontWeight: 'bold',
              borderRadius: 3,
              background: selectedUserType 
                ? `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
                : 'grey.400',
              '&:hover': {
                background: selectedUserType 
                  ? `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.secondary.dark})`
                  : 'grey.400',
                transform: selectedUserType && !loading ? 'translateY(-2px)' : 'none',
                boxShadow: selectedUserType && !loading ? theme.shadows[8] : 'none'
              },
              '&:disabled': {
                color: 'white'
              },
              transition: 'all 0.2s ease-in-out'
            }}
          >
            {loading 
              ? 'Starting Test...' 
              : `Start ${selectedUserType === 'developer' ? 'Developer' : selectedUserType === 'non-developer' ? 'Non-Developer' : ''} Test`
            }
          </Button>
          
          {/* Debug Info */}
          {process.env.NODE_ENV === 'development' && selectedUserType && (
            <Typography variant="caption" display="block" sx={{ mt: 2, color: 'text.secondary' }}>
              Debug: Will send user_type="{selectedUserType === 'developer' ? 'dev' : 'non_dev'}" to API
            </Typography>
          )}
        </Box>
      </Fade>
    </Container>
  );
};

export default MockTestStart;