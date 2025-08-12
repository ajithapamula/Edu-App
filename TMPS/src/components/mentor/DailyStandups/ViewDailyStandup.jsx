import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  IconButton,
  Tooltip,
  Skeleton,
  keyframes,
  Alert,
  Button
} from '@mui/material';
import {
  Person,
  Task,
  TrendingUp,
  ArrowBack,
  Refresh,
  ErrorOutline,
  Quiz
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import dailyStandupApiService from '../../../services/API/dailystandup';

// Enhanced Shimmer Animation
const shimmerAnimation = keyframes`
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
`;

const shimmerGradient = {
  background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
  backgroundSize: '200px 100%',
  animation: `${shimmerAnimation} 1.5s infinite`
};

// Shimmer Components
const HeaderShimmer = () => (
  <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
    <Skeleton 
      variant="circular" 
      width={40} 
      height={40} 
      sx={{ mr: 2, ...shimmerGradient }} 
    />
    <Skeleton 
      variant="text" 
      width="50%" 
      height={40} 
      sx={{ mr: 2, ...shimmerGradient }} 
    />
  </Box>
);

const SummaryCardShimmer = () => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Skeleton 
          variant="circular" 
          width={24} 
          height={24} 
          sx={{ mr: 1, ...shimmerGradient }} 
        />
        <Box flex={1}>
          <Skeleton 
            variant="text" 
            width="60%" 
            height={28} 
            sx={{ mb: 0.5, ...shimmerGradient }} 
          />
          <Skeleton 
            variant="text" 
            width="40%" 
            height={16} 
            sx={shimmerGradient} 
          />
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const MentorViewDailyStandup = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [testData, setTestData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTestData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Fetching test data for student ID:', id);
      
      // Directly fetch student test data using the API
      const studentTests = await dailyStandupApiService.getStudentStandupTests(id);
      
      if (!studentTests || studentTests.length === 0) {
        throw new Error('No test data found for this student');
      }
      
      console.log('API Response - Test Data:', studentTests);
      setTestData(studentTests);
      
    } catch (err) {
      console.error('Error fetching test data:', err);
      setError(err.message || 'Failed to load test data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchTestData();
    }
  }, [id]);

  const handleBack = () => {
    navigate('/mentor/daily-standups');
  };

  const handleRetry = () => {
    fetchTestData();
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'success';
    if (score >= 6) return 'info';
    if (score >= 4) return 'warning';
    return 'error';
  };

  // Loading state
  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <HeaderShimmer />
        
        {/* Summary Cards Shimmer */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <SummaryCardShimmer />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  // Error state
  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Tooltip title="Back to Daily Standups List">
            <IconButton onClick={handleBack} sx={{ mr: 2 }}>
              <ArrowBack />
            </IconButton>
          </Tooltip>
          <Typography variant="h4" component="h1">
            Test Data Details
          </Typography>
        </Box>
        
        <Alert 
          severity="error" 
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={handleRetry}
              startIcon={<Refresh />}
            >
              Retry
            </Button>
          }
          sx={{ mb: 2 }}
        >
          <Typography variant="h6" gutterBottom>
            <ErrorOutline sx={{ mr: 1, verticalAlign: 'middle' }} />
            Failed to Load Test Data
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
        </Alert>
      </Box>
    );
  }

  // Not found state
  if (!testData || testData.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton onClick={handleBack} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" color="error">
            No test data found
          </Typography>
        </Box>
        <Alert severity="warning">
          No test data found for Student ID: {id}
        </Alert>
      </Box>
    );
  }

  // Calculate summary from actual API data
  const testCount = testData.length;
  const studentName = testData[0]?.name || `Student ${id}`;
  const studentId = testData[0]?.Student_ID || id;
  const sessionId = testData[0]?.session_id;
  const averageScore = testData.reduce((sum, test) => sum + (test.score || 0), 0) / testCount;
  const maxScore = Math.max(...testData.map(t => t.score || 0));
  const minScore = Math.min(...testData.map(t => t.score || 0));

  return (
    <Box sx={{ p: 3 }}>
      {/* Header - Using only API data */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Tooltip title="Back to Daily Standups List">
          <IconButton onClick={handleBack} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
        </Tooltip>
        <Typography variant="h4" component="h1">
          Test Data - {studentName}
        </Typography>
        <Chip 
          label={`Session ${sessionId}`}
          variant="outlined"
          sx={{ ml: 2 }}
        />
      </Box>

      {/* Summary Cards - Only API data */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Person color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{studentName}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Student ID: {studentId}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Quiz color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{testCount}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Tests
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TrendingUp color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{averageScore.toFixed(1)}/10</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average Score
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Task color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{sessionId}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Session ID
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Test Data Table - Only API fields */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Test Details ({testCount} test{testCount > 1 ? 's' : ''})
          </Typography>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Test ID</TableCell>
                  <TableCell>Student ID</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Session ID</TableCell>
                  <TableCell>Score</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {testData.map((test, index) => (
                  <TableRow key={test.test_id || index} hover>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {test.test_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {test.Student_ID}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar 
                          sx={{ width: 32, height: 32, mr: 2 }}
                        >
                          {test.name ? test.name.charAt(0) : 'S'}
                        </Avatar>
                        <Typography variant="body2" fontWeight="medium">
                          {test.name}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={test.session_id}
                        variant="outlined"
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={`${test.score}/10`}
                        color={getScoreColor(test.score)}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Summary Section - Only calculated from API data */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom color="primary" display="flex" alignItems="center">
                <TrendingUp sx={{ mr: 1 }} />
                Score Analysis
              </Typography>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2">
                    <strong>Highest Score:</strong>
                  </Typography>
                  <Chip 
                    label={`${maxScore}/10`}
                    color={getScoreColor(maxScore)}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2">
                    <strong>Lowest Score:</strong>
                  </Typography>
                  <Chip 
                    label={`${minScore}/10`}
                    color={getScoreColor(minScore)}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2">
                    <strong>Average Score:</strong>
                  </Typography>
                  <Chip 
                    label={`${averageScore.toFixed(1)}/10`}
                    color={getScoreColor(averageScore)}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">
                    <strong>Score Range:</strong>
                  </Typography>
                  <Typography variant="body2">
                    {minScore === maxScore ? `${minScore}/10` : `${minScore}-${maxScore}/10`}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom display="flex" alignItems="center">
                <Task sx={{ mr: 1 }} />
                Test Information
              </Typography>
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2">
                    <strong>Student Name:</strong>
                  </Typography>
                  <Typography variant="body2">
                    {studentName}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2">
                    <strong>Student ID:</strong>
                  </Typography>
                  <Typography variant="body2">
                    {studentId}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2">
                    <strong>Session ID:</strong>
                  </Typography>
                  <Typography variant="body2">
                    {sessionId}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">
                    <strong>Total Tests:</strong>
                  </Typography>
                  <Typography variant="body2">
                    {testCount}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MentorViewDailyStandup;