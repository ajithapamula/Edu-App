import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Alert,
  Button,
  Skeleton,
  keyframes,
  Container,
  Stack,
  Divider,
  LinearProgress,
  IconButton,
  Tooltip,
  useTheme,
  alpha,
  styled,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  Person,
  Schedule,
  Star,
  ArrowBack,
  Assessment,
  Badge as BadgeIcon,
  TrendingUp,
  Analytics,
  Timer,
  CalendarToday,
  Download,
  Share,
  Print,
  MoreVert,
  Refresh,
  School as SchoolIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  QuestionAnswer as QuestionAnswerIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { weeklyInterviewsAPI } from '../../../services/API/mockinterviews';

// Professional shimmer animation
const shimmerAnimation = keyframes`
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
`;

// Styled shimmer components
const ShimmerBox = styled(Box)(({ theme, width = '100%', height = '20px' }) => ({
  width,
  height,
  borderRadius: 4,
  background: 'linear-gradient(90deg, #f8f9fa 25%, #e9ecef 50%, #f8f9fa 75%)',
  backgroundSize: '200px 100%',
  animation: `${shimmerAnimation} 1.2s infinite`
}));

// Professional Loading Components
const HeaderShimmer = () => (
  <Box mb={4}>
    <ShimmerBox width="50%" height={40} sx={{ mb: 2 }} />
    <Box display="flex" gap={2} alignItems="center">
      <ShimmerBox width={120} height={32} sx={{ borderRadius: 2 }} />
      <ShimmerBox width={100} height={32} sx={{ borderRadius: 2 }} />
    </Box>
  </Box>
);

const MetricCardShimmer = () => (
  <Card elevation={0} sx={{ border: 1, borderColor: 'divider', height: '100%' }}>
    <CardContent sx={{ textAlign: 'center', py: 4 }}>
      <ShimmerBox width={64} height={64} sx={{ borderRadius: '50%', mx: 'auto', mb: 2 }} />
      <ShimmerBox width="60%" height={32} sx={{ mx: 'auto', mb: 1 }} />
      <ShimmerBox width="80%" height={20} sx={{ mx: 'auto' }} />
    </CardContent>
  </Card>
);

const ProfileCardShimmer = () => (
  <Card elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
    <CardContent sx={{ p: 3 }}>
      <Box display="flex" alignItems="center" gap={3} mb={3}>
        <ShimmerBox width={80} height={80} sx={{ borderRadius: '50%' }} />
        <Box flex={1}>
          <ShimmerBox width="70%" height={28} sx={{ mb: 1 }} />
          <ShimmerBox width="50%" height={20} />
        </Box>
      </Box>
      {Array.from({ length: 4 }).map((_, i) => (
        <Box key={i} mb={2}>
          <ShimmerBox width="100%" height={16} />
        </Box>
      ))}
    </CardContent>
  </Card>
);

const ViewMockInterview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const [interview, setInterview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchInterview = async () => {
      setLoading(true);
      setError(null);
      try {
        console.log('Fetching interview with ID:', id);
        
        // Get all interviews and find the one that matches the ID
        const allInterviews = await weeklyInterviewsAPI.getAllInterviews();
        console.log('All interviews:', allInterviews);
        
        // Find interview by test_id, id, or other identifiers
        const foundInterview = allInterviews.find(
          interview => 
            interview.test_id === id || 
            interview.id === id ||
            interview.Student_ID === id ||
            interview.student_id === id
        );
        
        if (foundInterview) {
          const transformedData = weeklyInterviewsAPI.transformInterviewData(foundInterview);
          console.log('Transformed interview data:', transformedData);
          setInterview(transformedData);
        } else {
          setError('Interview not found');
        }
      } catch (error) {
        console.error('Failed to load interview:', error);
        setError('Failed to load interview data: ' + error.message);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchInterview();
    }
  }, [id]);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const allInterviews = await weeklyInterviewsAPI.getAllInterviews();
      const foundInterview = allInterviews.find(
        interview => 
          interview.test_id === id || 
          interview.id === id ||
          interview.Student_ID === id ||
          interview.student_id === id
      );
      
      if (foundInterview) {
        const transformedData = weeklyInterviewsAPI.transformInterviewData(foundInterview);
        setInterview(transformedData);
        setError(null);
      }
    } catch (error) {
      console.error('Failed to refresh interview:', error);
      setError('Failed to refresh interview data');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'success';
    if (score >= 6) return 'warning';
    if (score >= 4) return 'info';
    return 'error';
  };

  const getScorePercentage = (score) => {
    return `${score}%`;
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return { date: 'N/A', time: 'N/A' };
    
    let date;
    if (typeof timestamp === 'number') {
      // Unix timestamp
      date = new Date(timestamp * 1000);
    } else {
      // ISO string or other format
      date = new Date(timestamp);
    }
    
    if (isNaN(date.getTime())) {
      return { date: 'N/A', time: 'N/A' };
    }
    
    return {
      date: date.toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      }),
      time: date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      })
    };
  };

  const getInitials = (name) => {
    if (!name || name === 'Unknown Student' || name === 'No Name') return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <HeaderShimmer />
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <ProfileCardShimmer />
          </Grid>
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              {Array.from({ length: 4 }).map((_, i) => (
                <Grid item xs={6} sm={3} key={i}>
                  <MetricCardShimmer />
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>
      </Container>
    );
  }

  if (error || !interview) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
          {error || 'Interview not found or you don\'t have permission to view it.'}
        </Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/trainer/mock-interviews')}
        >
          Back to List
        </Button>
      </Box>
    );
  }

  const dateTime = formatTimestamp(interview.timestamp);
  const hasScores = interview.overallScore !== null || 
                   interview.technicalScore !== null || 
                   interview.communicationScore !== null || 
                   interview.hrScore !== null ||
                   interview.scores?.overall_score !== null ||
                   interview.scores?.technical_score !== null ||
                   interview.scores?.communication_score !== null ||
                   interview.scores?.hr_score !== null;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate('/trainer/mock-interviews')} sx={{ mr: 1 }}>
            <ArrowBack />
          </IconButton>
          <Assessment sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h4" fontWeight="bold" color="primary.main">
            Interview Assessment
          </Typography>
        </Box>
        <Box>
          <Tooltip title="Refresh Data">
            <IconButton 
              color="primary" 
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
          </Tooltip>
          <Tooltip title="Download Report">
            <IconButton color="primary">
              <Download />
            </IconButton>
          </Tooltip>
          <Tooltip title="Print Details">
            <IconButton color="primary">
              <Print />
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
              {getInitials(interview.studentName || interview.student_name || interview.name)}
            </Avatar>
            <Box>
              <Typography variant="h4" fontWeight="bold" gutterBottom>
                {interview.studentName || interview.student_name || interview.name || 'Unknown Student'}
              </Typography>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Student ID: {interview.studentId || interview.Student_ID || 'N/A'}
              </Typography>
              <Box display="flex" gap={1} alignItems="center">
                <Chip 
                  label="Weekly Interview" 
                  color="primary" 
                  variant="outlined"
                  size="medium"
                />
                <Chip 
                  label={`Session ${interview.sessionId || interview.session_id || 'N/A'}`} 
                  variant="outlined"
                  size="medium"
                />
                {hasScores && (
                  <Chip 
                    label="Assessed" 
                    color="success" 
                    size="medium"
                  />
                )}
              </Box>
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* Interview Details Table */}
          <Card sx={{ border: 1, borderColor: 'divider' }}>
            <CardHeader 
              title={
                <Box display="flex" alignItems="center">
                  <Assessment sx={{ mr: 1, color: 'white' }} />
                  <Typography variant="h5" fontWeight="bold" color="white">
                    Interview Details
                  </Typography>
                </Box>
              }
              subheader="Basic interview information"
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
                      <TableCell sx={{ fontWeight: 'bold' }}>Test Date</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Test Time</TableCell>
                      <TableCell sx={{ fontWeight: 'bold' }}>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow sx={{ '&:hover': { bgcolor: 'grey.50' } }}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold" color="primary.main" fontFamily="monospace">
                          {interview.testId || interview.test_id ? 
                            `${(interview.testId || interview.test_id).substring(0, 8)}...` : 
                            'N/A'
                          }
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={interview.sessionId || interview.session_id || 'N/A'} 
                          size="small" 
                          color="info"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="bold">
                          {dateTime.date}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {dateTime.time}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={hasScores ? "Completed" : "Pending"}
                          size="small"
                          color={hasScores ? "success" : "warning"}
                          icon={hasScores ? <CheckCircleIcon /> : <Timer />}
                        />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Card sx={{ boxShadow: 3 }}>
        <CardHeader 
          title={
            <Box display="flex" alignItems="center">
              <TrendingUp sx={{ mr: 1, color: 'white' }} />
              <Typography variant="h5" fontWeight="bold" color="white">
                Performance Overview
              </Typography>
            </Box>
          }
          subheader={hasScores ? "Assessment scores and performance metrics" : "Assessment pending"}
          sx={{ 
            bgcolor: 'primary.main', 
            color: 'white',
            '& .MuiCardHeader-subheader': {
              color: 'rgba(255, 255, 255, 0.7)'
            }
          }}
        />
        <CardContent sx={{ p: 4 }}>
          {hasScores ? (
            <Grid container spacing={3}>
              {/* Overall Score */}
              {(interview.overallScore !== null || interview.scores?.overall_score !== null) && (
                <Grid item xs={12} sm={6} md={3}>
                  <Card 
                    elevation={2} 
                    sx={{ 
                      textAlign: 'center',
                      height: '100%',
                      bgcolor: 'background.paper',
                      border: 1,
                      borderColor: 'divider'
                    }}
                  >
                    <CardContent sx={{ py: 3 }}>
                      <Box 
                        sx={{ 
                          width: 64, 
                          height: 64, 
                          borderRadius: '50%', 
                          bgcolor: alpha(theme.palette[getScoreColor(interview.scores?.overall_score || interview.overallScore)].main, 0.2),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mx: 'auto',
                          mb: 2
                        }}
                      >
                        <Typography variant="h5" fontWeight={700} sx={{ color: theme.palette[getScoreColor(interview.scores?.overall_score || interview.overallScore)].main }}>
                          {interview.scores?.overall_score || interview.overallScore}
                        </Typography>
                      </Box>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Overall
                      </Typography>
                      <Chip 
                        label={getScorePercentage(interview.scores?.overall_score || interview.overallScore)} 
                        color={getScoreColor(interview.scores?.overall_score || interview.overallScore)}
                        size="small"
                      />
                      <Box sx={{ mt: 2 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={interview.scores?.overall_score || interview.overallScore} 
                          color={getScoreColor(interview.scores?.overall_score || interview.overallScore)}
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Technical Score */}
              {(interview.technicalScore !== null || interview.scores?.technical_score !== null) && (
                <Grid item xs={12} sm={6} md={3}>
                  <Card 
                    elevation={2} 
                    sx={{ 
                      textAlign: 'center',
                      height: '100%',
                      border: 1,
                      borderColor: 'divider'
                    }}
                  >
                    <CardContent sx={{ py: 3 }}>
                      <Box 
                        sx={{ 
                          width: 64, 
                          height: 64, 
                          borderRadius: '50%', 
                          bgcolor: alpha(theme.palette[getScoreColor(interview.scores?.technical_score || interview.technicalScore)].main, 0.2),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mx: 'auto',
                          mb: 2
                        }}
                      >
                        <Typography variant="h5" fontWeight={700} sx={{ color: theme.palette[getScoreColor(interview.scores?.technical_score || interview.technicalScore)].main }}>
                          {interview.scores?.technical_score || interview.technicalScore}
                        </Typography>
                      </Box>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Technical
                      </Typography>
                      <Chip 
                        label={getScorePercentage(interview.scores?.technical_score || interview.technicalScore)} 
                        color={getScoreColor(interview.scores?.technical_score || interview.technicalScore)}
                        size="small"
                      />
                      <Box sx={{ mt: 2 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={interview.scores?.technical_score || interview.technicalScore} 
                          color={getScoreColor(interview.scores?.technical_score || interview.technicalScore)}
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Communication Score */}
              {(interview.communicationScore !== null || interview.scores?.communication_score !== null) && (
                <Grid item xs={12} sm={6} md={3}>
                  <Card 
                    elevation={2} 
                    sx={{ 
                      textAlign: 'center',
                      height: '100%',
                      border: 1,
                      borderColor: 'divider'
                    }}
                  >
                    <CardContent sx={{ py: 3 }}>
                      <Box 
                        sx={{ 
                          width: 64, 
                          height: 64, 
                          borderRadius: '50%', 
                          bgcolor: alpha(theme.palette[getScoreColor(interview.scores?.communication_score || interview.communicationScore)].main, 0.2),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mx: 'auto',
                          mb: 2
                        }}
                      >
                        <Typography variant="h5" fontWeight={700} sx={{ color: theme.palette[getScoreColor(interview.scores?.communication_score || interview.communicationScore)].main }}>
                          {interview.scores?.communication_score || interview.communicationScore}
                        </Typography>
                      </Box>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Communication
                      </Typography>
                      <Chip 
                        label={getScorePercentage(interview.scores?.communication_score || interview.communicationScore)} 
                        color={getScoreColor(interview.scores?.communication_score || interview.communicationScore)}
                        size="small"
                      />
                      <Box sx={{ mt: 2 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={interview.scores?.communication_score || interview.communicationScore} 
                          color={getScoreColor(interview.scores?.communication_score || interview.communicationScore)}
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* HR Score */}
              {(interview.hrScore !== null || interview.scores?.hr_score !== null) && (
                <Grid item xs={12} sm={6} md={3}>
                  <Card 
                    elevation={2} 
                    sx={{ 
                      textAlign: 'center',
                      height: '100%',
                      border: 1,
                      borderColor: 'divider'
                    }}
                  >
                    <CardContent sx={{ py: 3 }}>
                      <Box 
                        sx={{ 
                          width: 64, 
                          height: 64, 
                          borderRadius: '50%', 
                          bgcolor: alpha(theme.palette[getScoreColor(interview.scores?.hr_score || interview.hrScore)].main, 0.2),
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mx: 'auto',
                          mb: 2
                        }}
                      >
                        <Typography variant="h5" fontWeight={700} sx={{ color: theme.palette[getScoreColor(interview.scores?.hr_score || interview.hrScore)].main }}>
                          {interview.scores?.hr_score || interview.hrScore}
                        </Typography>
                      </Box>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        HR Skills
                      </Typography>
                      <Chip 
                        label={getScorePercentage(interview.scores?.hr_score || interview.hrScore)} 
                        color={getScoreColor(interview.scores?.hr_score || interview.hrScore)}
                        size="small"
                      />
                      <Box sx={{ mt: 2 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={interview.scores?.hr_score || interview.hrScore} 
                          color={getScoreColor(interview.scores?.hr_score || interview.hrScore)}
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* Assessment Summary */}
              <Grid item xs={12}>
                <Card elevation={2} sx={{ mt: 3, border: 1, borderColor: 'divider' }}>
                  <CardContent sx={{ p: 3 }}>
                    <Typography variant="h6" fontWeight={600} gutterBottom>
                      Assessment Summary
                    </Typography>
                    <Grid container spacing={3}>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Overall Performance
                        </Typography>
                        <Typography variant="body2">
                          {(interview.scores?.overall_score || interview.overallScore) >= 8 ? 'Excellent performance with strong capabilities across all areas.' :
                           (interview.scores?.overall_score || interview.overallScore) >= 6 ? 'Good performance with room for improvement in some areas.' :
                           (interview.scores?.overall_score || interview.overallScore) >= 4 ? 'Satisfactory performance but needs significant improvement.' :
                           'Needs considerable improvement across multiple areas.'}
                        </Typography>
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                          Recommendations
                        </Typography>
                        <Typography variant="body2">
                          Focus on areas with lower scores. Consider additional practice sessions and targeted skill development.
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : (
            <Box textAlign="center" py={4}>
              <AssignmentIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Interview Assessment Pending
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This interview has not been scored yet. Scores will be available once the assessment is complete.
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default ViewMockInterview;