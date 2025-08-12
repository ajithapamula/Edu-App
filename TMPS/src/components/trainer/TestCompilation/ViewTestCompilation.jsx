import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardHeader,
  CardContent,
  Typography,
  Button,
  Grid,
  Paper,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  IconButton,
  Tooltip,
  Alert,
  Skeleton,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
  Visibility as VisibilityIcon,
  Person as PersonIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { formatDate } from '../../../utils/dateUtils';

// Dummy data for demonstration - replace with actual API call
const DUMMY_COMPILATION_DETAIL = {
  id: 1,
  title: "Mathematics Weekly Assessment",
  description: "Comprehensive math test covering algebra and geometry topics for grade 10 students. This assessment includes multiple choice questions, short answer problems, and detailed mathematical proofs.",
  studentName: "Alice Johnson",
  studentId: "STU001",
  studentEmail: "alice.johnson@email.com",
  type: "weekly",
  status: "completed",
  completionPercentage: 95,
  completedTests: 8,
  totalTests: 8,
  testTypes: ["Multiple Choice", "Short Answer", "Mathematical Proofs"],
  overallScore: 85,
  totalMarks: 100,
  overallPercentage: 85,
  dueDate: "2025-06-10T10:00:00Z",
  createdAt: "2025-05-28T08:00:00Z",
  submittedAt: "2025-06-09T14:30:00Z",
  isOverdue: false,
  timeSpent: "2 hours 45 minutes",
  attempts: 1,
  maxAttempts: 3,
  instructor: "Dr. Smith",
  course: "Mathematics - Grade 10",
  tests: [
    {
      id: 1,
      name: "Algebra Fundamentals",
      type: "Multiple Choice",
      status: "completed",
      score: 18,
      maxScore: 20,
      percentage: 90,
      timeSpent: "25 minutes",
      completedAt: "2025-06-09T10:15:00Z"
    },
    {
      id: 2,
      name: "Geometry Basics",
      type: "Short Answer",
      status: "completed",
      score: 15,
      maxScore: 18,
      percentage: 83.3,
      timeSpent: "30 minutes",
      completedAt: "2025-06-09T10:45:00Z"
    },
    {
      id: 3,
      name: "Problem Solving",
      type: "Mathematical Proofs",
      status: "completed",
      score: 22,
      maxScore: 25,
      percentage: 88,
      timeSpent: "45 minutes",
      completedAt: "2025-06-09T11:30:00Z"
    },
    {
      id: 4,
      name: "Advanced Algebra",
      type: "Multiple Choice",
      status: "completed",
      score: 16,
      maxScore: 20,
      percentage: 80,
      timeSpent: "20 minutes",
      completedAt: "2025-06-09T12:00:00Z"
    },
    {
      id: 5,
      name: "Coordinate Geometry",
      type: "Short Answer",
      status: "completed",
      score: 14,
      maxScore: 17,
      percentage: 82.4,
      timeSpent: "35 minutes",
      completedAt: "2025-06-09T12:35:00Z"
    }
  ],
  feedback: "Excellent performance overall. Strong understanding of algebraic concepts. Could improve on coordinate geometry visualization.",
  strengths: ["Algebra", "Problem Solving", "Mathematical Reasoning"],
  improvements: ["Coordinate Geometry", "Time Management", "Show More Work"]
};

const ViewTestCompilation = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [compilation, setCompilation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCompilationDetails();
  }, [id]);

  const fetchCompilationDetails = async () => {
    try {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // In real implementation, you would make an API call here
      // const response = await trainerService.getTestCompilationById(id);
      // setCompilation(response.data);
      
      setCompilation(DUMMY_COMPILATION_DETAIL);
    } catch (error) {
      console.error('Error fetching compilation details:', error);
      setError('Failed to load test compilation details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'info';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      case 'submitted':
        return 'primary';
      default:
        return 'default';
    }
  };

  const getTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'weekly':
        return 'primary';
      case 'monthly':
        return 'secondary';
      case 'final':
        return 'success';
      case 'mid_term':
        return 'info';
      default:
        return 'default';
    }
  };

  const getProgressColor = (progress) => {
    if (progress >= 80) return 'success';
    if (progress >= 60) return 'info';
    if (progress >= 40) return 'warning';
    return 'error';
  };

  const handleDownloadReport = () => {
    // Implement download functionality
    console.log('Downloading report for compilation:', id);
  };

  const handleEditCompilation = () => {
    // Navigate to edit page or open edit modal
    console.log('Edit compilation:', id);
  };

  if (loading) {
    return (
      <Box>
        <Box display="flex" alignItems="center" gap={2} mb={3}>
          <Skeleton variant="circular" width={40} height={40} />
          <Skeleton variant="text" width={200} height={32} />
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardHeader title={<Skeleton variant="text" width={300} height={28} />} />
              <CardContent>
                <Skeleton variant="text" width="100%" height={20} sx={{ mb: 2 }} />
                <Skeleton variant="text" width="80%" height={20} sx={{ mb: 2 }} />
                <Skeleton variant="rectangular" width="100%" height={200} />
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              <CardHeader title={<Skeleton variant="text" width={150} height={24} />} />
              <CardContent>
                {Array.from({ length: 5 }).map((_, index) => (
                  <Box key={index} mb={2}>
                    <Skeleton variant="text" width="100%" height={20} />
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  }

  if (error || !compilation) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/trainer/test-compilation')}
          sx={{ mb: 3 }}
        >
          Go Back
        </Button>
        
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || 'Test compilation not found.'}
        </Alert>
        
        <Typography variant="h5" color="text.secondary">
          Test compilation not found.
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/trainer/test-compilation')}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h5" fontWeight="bold">
              {compilation.title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Test Compilation Details
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" gap={1}>
          <Tooltip title="Edit Compilation">
            <IconButton onClick={handleEditCompilation}>
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Download Report">
            <IconButton onClick={handleDownloadReport}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={8}>
          {/* Overview Card */}
          <Card sx={{ mb: 3 }}>
            <CardHeader
              title={
                <Box display="flex" alignItems="center" gap={1}>
                  <AssessmentIcon />
                  <Typography variant="h6">Compilation Overview</Typography>
                </Box>
              }
            />
            <CardContent>
              <Typography variant="body1" paragraph>
                {compilation.description}
              </Typography>
              
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <PersonIcon color="primary" />
                    <Typography variant="subtitle2">Student Information</Typography>
                  </Box>
                  <Typography variant="body2">
                    <strong>{compilation.studentName}</strong> ({compilation.studentId})
                  </Typography>
                  {compilation.studentEmail && (
                    <Typography variant="body2" color="text.secondary">
                      {compilation.studentEmail}
                    </Typography>
                  )}
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <ScheduleIcon color="primary" />
                    <Typography variant="subtitle2">Timeline</Typography>
                  </Box>
                  <Typography variant="body2">
                    <strong>Created:</strong> {formatDate(compilation.createdAt)}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Due:</strong> {formatDate(compilation.dueDate)}
                  </Typography>
                  {compilation.submittedAt && (
                    <Typography variant="body2">
                      <strong>Submitted:</strong> {formatDate(compilation.submittedAt)}
                    </Typography>
                  )}
                </Grid>
              </Grid>

              {/* Progress Section */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Overall Progress
                </Typography>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">
                    {compilation.completedTests} / {compilation.totalTests} tests completed
                  </Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {compilation.completionPercentage}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={compilation.completionPercentage}
                  color={getProgressColor(compilation.completionPercentage)}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>

              {/* Score Section */}
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Overall Score
                </Typography>
                <Box display="flex" alignItems="center" gap={2}>
                  <Typography variant="h4" color={getProgressColor(compilation.overallPercentage)}>
                    {compilation.overallScore} / {compilation.totalMarks}
                  </Typography>
                  <Chip
                    label={`${compilation.overallPercentage}%`}
                    color={getProgressColor(compilation.overallPercentage)}
                    variant="outlined"
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Individual Tests */}
          <Card>
            <CardHeader
              title={
                <Typography variant="h6">Individual Test Results</Typography>
              }
            />
            <CardContent>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Test Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Score</TableCell>
                      <TableCell>Time Spent</TableCell>
                      <TableCell>Completed</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {compilation.tests?.map((test) => (
                      <TableRow key={test.id} hover>
                        <TableCell>
                          <Typography variant="subtitle2">
                            {test.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={test.type} 
                            size="small" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            {test.status === 'completed' ? (
                              <CheckCircleIcon color="success" fontSize="small" />
                            ) : (
                              <CancelIcon color="error" fontSize="small" />
                            )}
                            <Chip
                              label={test.status}
                              size="small"
                              color={getStatusColor(test.status)}
                            />
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" fontWeight="bold">
                              {test.score} / {test.maxScore}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {test.percentage.toFixed(1)}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {test.timeSpent}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {test.completedAt ? formatDate(test.completedAt) : '-'}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Status & Info Card */}
          <Card sx={{ mb: 3 }}>
            <CardHeader title="Compilation Status" />
            <CardContent>
              <Box display="flex" gap={1} mb={2}>
                <Chip
                  label={compilation.status}
                  color={getStatusColor(compilation.status)}
                />
                <Chip
                  label={compilation.type?.replace('_', ' ').toUpperCase()}
                  color={getTypeColor(compilation.type)}
                  variant="outlined"
                />
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Course & Instructor
                </Typography>
                <Typography variant="body2">
                  <strong>Course:</strong> {compilation.course}
                </Typography>
                <Typography variant="body2">
                  <strong>Instructor:</strong> {compilation.instructor}
                </Typography>
              </Box>

              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom>
                  Attempt Information
                </Typography>
                <Typography variant="body2">
                  <strong>Attempt:</strong> {compilation.attempts} / {compilation.maxAttempts}
                </Typography>
                <Typography variant="body2">
                  <strong>Time Spent:</strong> {compilation.timeSpent}
                </Typography>
              </Box>

              {compilation.isOverdue && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  This compilation is overdue
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Performance Insights */}
          <Card sx={{ mb: 3 }}>
            <CardHeader
              title={
                <Box display="flex" alignItems="center" gap={1}>
                  <TrendingUpIcon />
                  <Typography variant="h6">Performance Insights</Typography>
                </Box>
              }
            />
            <CardContent>
              <Box mb={2}>
                <Typography variant="subtitle2" gutterBottom color="success.main">
                  Strengths
                </Typography>
                {compilation.strengths?.map((strength, index) => (
                  <Chip
                    key={index}
                    label={strength}
                    size="small"
                    color="success"
                    variant="outlined"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>

              <Box>
                <Typography variant="subtitle2" gutterBottom color="warning.main">
                  Areas for Improvement
                </Typography>
                {compilation.improvements?.map((improvement, index) => (
                  <Chip
                    key={index}
                    label={improvement}
                    size="small"
                    color="warning"
                    variant="outlined"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Feedback */}
          {compilation.feedback && (
            <Card>
              <CardHeader title="Instructor Feedback" />
              <CardContent>
                <Typography variant="body2">
                  {compilation.feedback}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default ViewTestCompilation;