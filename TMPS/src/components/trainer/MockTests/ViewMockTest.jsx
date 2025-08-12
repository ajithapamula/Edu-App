import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardHeader,
  CardContent,
  Typography,
  Chip,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Tooltip,
  Alert,
  Avatar,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  Person as PersonIcon,
  ArrowBack as ArrowBackIcon,
  AccessTime as AccessTimeIcon,
  QuestionAnswer as QuestionAnswerIcon,
  Grade as GradeIcon,
  Assignment as AssignmentIcon,
  School as SchoolIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
  Download as DownloadIcon,
  Print as PrintIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import LoadingSpinner from '../../common/LoadingSpinner';

// Import the API service
import { mockTestsAPI } from '../../../services/API/mocktest.js';

const ViewMockTest = () => {
  const { id: studentId } = useParams();
  const navigate = useNavigate();
  const [student, setStudent] = useState(null);
  const [studentTests, setStudentTests] = useState([]);
  const [studentStats, setStudentStats] = useState({
    totalTests: 0,
    completedTests: 0,
    avgScore: 0,
    totalQuestions: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (studentId) {
      fetchStudentDetails();
    }
  }, [studentId]);

  const fetchStudentDetails = async () => {
    try {
      setLoading(true);
      setError('');
      
      console.log('Fetching student details for ID:', studentId);
      
      // Fetch student details
      const studentData = await mockTestsAPI.getStudentById(studentId);
      console.log('Student data received:', studentData);
      
      setStudent(studentData);
      
      // Fetch student tests
      try {
        const testsResponse = await mockTestsAPI.getStudentTests(studentId);
        console.log('Student tests response:', testsResponse);
        
        // Extract tests array from response
        const testsData = testsResponse.tests || testsResponse || [];
        console.log('Student tests data:', testsData);
        
        setStudentTests(testsData);
        
        // Calculate student statistics from actual API data
        const stats = calculateStudentStats(testsData);
        setStudentStats(stats);
        
      } catch (testsError) {
        console.warn('Failed to fetch student tests:', testsError);
        setStudentTests([]);
        setStudentStats({
          totalTests: 0,
          completedTests: 0,
          avgScore: 0,
          totalQuestions: 0
        });
      }
      
    } catch (error) {
      console.error('Error fetching student details:', error);
      setError(`Failed to fetch student details: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const calculateStudentStats = (tests) => {
    if (!tests || tests.length === 0) {
      return {
        totalTests: 0,
        completedTests: 0,
        avgScore: 0,
        totalQuestions: 0
      };
    }

    const completedTests = tests.filter(test => test.test_completed === true);
    const totalQuestions = tests.reduce((sum, test) => sum + (test.total_questions || 0), 0);
    const avgScore = completedTests.length > 0 
      ? (completedTests.reduce((sum, test) => sum + (test.score_percentage || 0), 0) / completedTests.length).toFixed(1)
      : 0;
    
    return {
      totalTests: tests.length,
      completedTests: completedTests.length,
      avgScore: avgScore,
      totalQuestions: totalQuestions
    };
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTestStatusColor = (completed) => {
    return completed ? 'success' : 'warning';
  };

  const getTestStatusLabel = (completed) => {
    return completed ? 'Completed' : 'In Progress';
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp * 1000).toLocaleString();
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const getUserTypeLabel = (userType) => {
    switch (userType) {
      case 'dev':
        return 'Developer';
      case 'non_dev':
        return 'Non-Developer';
      default:
        return userType || 'Unknown';
    }
  };

  const getUserTypeColor = (userType) => {
    switch (userType) {
      case 'dev':
        return 'primary';
      case 'non_dev':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getInitials = (name) => {
    if (!name || name === 'Unknown Student' || name === 'No Name') return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getScoreColor = (percentage) => {
    if (percentage >= 80) return 'success.main';
    if (percentage >= 60) return 'warning.main';
    return 'error.main';
  };

  if (loading) return <LoadingSpinner />;

  if (error || !student) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || 'Student not found.'}
        </Alert>
        <Button 
          onClick={() => navigate(-1)} 
          startIcon={<ArrowBackIcon />}
          variant="outlined"
        >
          Go Back
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate(-1)} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h4" fontWeight="bold" color="primary.main">
            Student Profile
          </Typography>
        </Box>
        <Box>
          <Tooltip title="Download Report">
            <IconButton color="primary">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Print Details">
            <IconButton color="primary">
              <PrintIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Student Information Card */}
      <Card sx={{ mb: 3, boxShadow: 3 }}>
        <CardContent sx={{ p: 4 }}>
          <Box display="flex" alignItems="center" mb={3}>
            <Avatar 
              sx={{ 
                bgcolor: 'primary.main', 
                width: 80, 
                height: 80, 
                mr: 3,
                fontSize: '1.5rem',
                fontWeight: 'bold'
              }}
            >
              {getInitials(student.name)}
            </Avatar>
            <Box>
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                {student.name || 'Unknown Student'}
              </Typography>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Student ID: {student.Student_ID}
              </Typography>
              <Chip
                label={student.name ? 'Active' : 'Inactive'}
                color={getStatusColor(student.name ? 'active' : 'inactive')}
                size="medium"
                sx={{ fontWeight: 'bold' }}
              />
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Statistics Cards */}
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  borderRadius: 2
                }}
              >
                <AssignmentIcon sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h3" fontWeight="bold">
                  {studentStats.totalTests}
                </Typography>
                <Typography variant="body1">
                  Total Tests
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                  color: 'white',
                  borderRadius: 2
                }}
              >
                <CheckCircleIcon sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h3" fontWeight="bold">
                  {studentStats.completedTests}
                </Typography>
                <Typography variant="body1">
                  Completed
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                  color: 'white',
                  borderRadius: 2
                }}
              >
                <TrendingUpIcon sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h3" fontWeight="bold">
                  {studentStats.avgScore}%
                </Typography>
                <Typography variant="body1">
                  Avg Score
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
                  color: 'white',
                  borderRadius: 2
                }}
              >
                <QuestionAnswerIcon sx={{ fontSize: 40, mb: 1 }} />
                <Typography variant="h3" fontWeight="bold">
                  {studentStats.totalQuestions}
                </Typography>
                <Typography variant="body1">
                  Total Questions
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Test History */}
      <Card sx={{ boxShadow: 3 }}>
        <CardHeader 
          title={
            <Box display="flex" alignItems="center">
              <SchoolIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h5" fontWeight="bold">
                Test History
              </Typography>
            </Box>
          }
          subheader={`${studentTests.length} tests assigned to this student`}
          sx={{ 
            bgcolor: 'primary.main', 
            color: 'white',
            '& .MuiCardHeader-subheader': {
              color: 'rgba(255, 255, 255, 0.7)'
            }
          }}
        />
        <CardContent sx={{ p: 0 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: 'grey.50' }}>
                  <TableCell sx={{ fontWeight: 'bold' }}>Test ID</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Session ID</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>User Type</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Questions</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Final Score</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Score %</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Test Date</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Progress</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {studentTests.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                      <Box textAlign="center">
                        <AssignmentIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                          No tests found for this student
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : (
                  studentTests.map((test, index) => (
                    <TableRow 
                      key={test.test_id || index}
                      sx={{ 
                        '&:hover': { bgcolor: 'grey.50' },
                        '&:nth-of-type(even)': { bgcolor: 'rgba(0, 0, 0, 0.02)' }
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold" color="primary.main">
                          {test.test_id ? test.test_id.split('-')[0] : 'N/A'}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={test.session_id || 'N/A'} 
                          size="small" 
                          color="info"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getUserTypeLabel(test.user_type)}
                          size="small"
                          color={getUserTypeColor(test.user_type)}
                        />
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <QuestionAnswerIcon sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
                          <Typography variant="body2" fontWeight="bold">
                            {test.total_questions || 0}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography 
                          variant="body2" 
                          fontWeight="bold"
                          color={getScoreColor(test.score_percentage || 0)}
                        >
                          {test.final_score || 0}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center">
                          <Typography 
                            variant="body2" 
                            fontWeight="bold"
                            color={getScoreColor(test.score_percentage || 0)}
                            sx={{ mr: 1 }}
                          >
                            {test.score_percentage || 0}%
                          </Typography>
                          <GradeIcon sx={{ fontSize: 16, color: getScoreColor(test.score_percentage || 0) }} />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={getTestStatusLabel(test.test_completed)}
                          size="small"
                          color={getTestStatusColor(test.test_completed)}
                          icon={test.test_completed ? <CheckCircleIcon /> : <AccessTimeIcon />}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatTimestamp(test.timestamp)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" width="120px">
                          <LinearProgress
                            variant="determinate"
                            value={test.test_completed ? 100 : 50}
                            sx={{ 
                              width: '80px', 
                              mr: 1,
                              height: 8,
                              borderRadius: 4,
                              '& .MuiLinearProgress-bar': {
                                backgroundColor: test.test_completed ? 'success.main' : 'warning.main',
                                borderRadius: 4
                              }
                            }}
                          />
                          <Typography variant="caption" fontWeight="bold">
                            {test.test_completed ? '100%' : '50%'}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ViewMockTest;