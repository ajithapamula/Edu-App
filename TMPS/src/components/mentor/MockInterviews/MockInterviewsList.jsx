import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  TextField,
  Alert,
  Tooltip,
  Avatar,
  Card,
  CardContent,
  Grid,
  Skeleton,
  Stack,
  keyframes,
  Container,
  CircularProgress,
  alpha,
  styled,
  useTheme
} from '@mui/material';
import {
  Visibility,
  Search,
  Star,
  TrendingUp,
  TrendingDown,
  Remove,
  Schedule,
  Analytics,
  People,
  Assessment,
  Refresh
} from '@mui/icons-material';
import { weeklyInterviewsAPI } from '../../../services/API/mockinterviews';

// Enhanced shimmer animation
const shimmerAnimation = keyframes`
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
`;

// Styled shimmer components that don't rely on theme in their definition
const ShimmerBox = styled(Box)(({ theme, width = '100%', height = '20px' }) => ({
  width,
  height,
  borderRadius: 4,
  background: 'linear-gradient(90deg, #f8f9fa 25%, #e9ecef 50%, #f8f9fa 75%)',
  backgroundSize: '200px 100%',
  animation: `${shimmerAnimation} 1.2s infinite`
}));

const ShimmerCard = () => (
  <Card elevation={0} sx={{ border: 1, borderColor: 'divider', height: '100%' }}>
    <CardContent sx={{ textAlign: 'center', py: 3 }}>
      <ShimmerBox width={56} height={56} sx={{ borderRadius: '50%', mx: 'auto', mb: 2 }} />
      <ShimmerBox width="60%" height={32} sx={{ mx: 'auto', mb: 1 }} />
      <ShimmerBox width="40%" height={16} sx={{ mx: 'auto' }} />
    </CardContent>
  </Card>
);

const ShimmerTableRow = () => (
  <TableRow>
    <TableCell>
      <Box display="flex" alignItems="center" gap={2}>
        <ShimmerBox width={48} height={48} sx={{ borderRadius: '50%' }} />
        <Box flex={1}>
          <ShimmerBox width="80%" height={20} sx={{ mb: 0.5 }} />
          <ShimmerBox width="60%" height={16} />
        </Box>
      </Box>
    </TableCell>
    {Array.from({ length: 6 }).map((_, i) => (
      <TableCell key={i}>
        <ShimmerBox width={`${60 + Math.random() * 40}%`} height={18} />
      </TableCell>
    ))}
    <TableCell align="center">
      <ShimmerBox width={40} height={40} sx={{ borderRadius: '50%', mx: 'auto' }} />
    </TableCell>
  </TableRow>
);

const ShimmerControls = () => (
  <Paper elevation={0} sx={{ p: 3, mb: 3, border: 1, borderColor: 'divider' }}>
    <ShimmerBox width={400} height={40} />
  </Paper>
);

const MentorMockInterviewSystem = () => {
  const navigate = useNavigate();
  const theme = useTheme(); // Add this hook to access the theme
  const [interviews, setInterviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    withScores: 0,
    averageOverallScore: 0,
    averageTechnicalScore: 0,
    averageCommunicationScore: 0,
    averageHrScore: 0
  });

  const fetchData = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      
      console.log('Fetching interview data...');
      
      // Use the new getAllInterviews method that aggregates all student interviews
      const data = await weeklyInterviewsAPI.getAllInterviews();
      console.log('Fetched interviews:', data);
      
      const transformed = data.map(weeklyInterviewsAPI.transformInterviewData);
      setInterviews(transformed);
      
      // Get statistics
      const statsData = await weeklyInterviewsAPI.getStats();
      setStats(statsData);
      
    } catch (error) {
      console.error('Failed to load interviews:', error);
      setError(error.message);
      setInterviews([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    fetchData(true);
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  
  const handleView = (interview) => {
  // Navigate to the mentor mock interview view route
  const interviewId = interview.testId || interview.id;
  // console.log('Navigating to mentor mock interview view:', interviewId);
  navigate(`/mentor/mock-interviews/view/${interviewId}`);
};

  const getScoreColor = (score) => {
    if (score >= 8) return 'success';
    if (score >= 6) return 'warning';
    if (score >= 4) return 'info';
    return 'error';
  };

  const getScoreIcon = (score) => {
    if (score >= 8) return <TrendingUp color="success" />;
    if (score >= 6) return <Remove color="warning" />;
    return <TrendingDown color="error" />;
  };

  const filteredInterviews = interviews.filter(interview => {
    const matchesSearch = interview.studentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         interview.testId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         interview.studentId.toString().toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

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
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      }),
      time: date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      })
    };
  };

  // Show error state
  if (error && !loading && !refreshing) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box mb={4}>
          <Typography variant="h4" component="h1" fontWeight={600} color="text.primary" gutterBottom>
            Weekly Interviews Management
          </Typography>
        </Box>
        
        <Alert 
          severity="error" 
          action={
            <IconButton size="small" onClick={handleRefresh}>
              <Refresh />
            </IconButton>
          }
          sx={{ mb: 3 }}
        >
          Failed to load interview data: {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Professional Header */}
      <Box mb={4}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography 
              variant="h4" 
              component="h1" 
              fontWeight={600}
              color="text.primary"
              gutterBottom
            >
              Weekly Interviews Management
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Monitor and review student interview assessments and performance metrics
            </Typography>
          </Box>
          
          <Tooltip title="Refresh Data">
            <IconButton 
              onClick={handleRefresh} 
              disabled={loading || refreshing}
              sx={{
                bgcolor: 'background.paper',
                border: 1,
                borderColor: theme.palette.primary.main,
                color: theme.palette.primary.main,
                '&:hover': {
                  bgcolor: theme.palette.primary.main,
                  color: 'white',
                  transform: 'rotate(180deg)',
                  transition: 'all 0.3s ease-in-out'
                },
                '&:disabled': {
                  bgcolor: alpha(theme.palette.primary.main, 0.1)
                }
              }}
            >
              {refreshing ? <CircularProgress size={20} /> : <Refresh />}
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          {loading ? <ShimmerCard /> : (
            <Card elevation={0} sx={{ border: 1, borderColor: 'divider', height: '100%' }}>
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box 
                  sx={{ 
                    width: 56, 
                    height: 56, 
                    borderRadius: '50%', 
                    bgcolor: alpha(theme.palette.primary.main, 0.2),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2
                  }}
                >
                  <People sx={{ color: theme.palette.primary.main }} />
                </Box>
                <Typography variant="h4" fontWeight={700} sx={{ color: theme.palette.primary.main }}>
                  {stats.total}
                </Typography>
                <Typography variant="body2" color="text.secondary" fontWeight={500}>
                  Total Interviews
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          {loading ? <ShimmerCard /> : (
            <Card elevation={0} sx={{ border: 1, borderColor: 'divider', height: '100%' }}>
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box 
                  sx={{ 
                    width: 56, 
                    height: 56, 
                    borderRadius: '50%', 
                    bgcolor: alpha(theme.palette.success.main, 0.2),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2
                  }}
                >
                  <Assessment sx={{ color: theme.palette.success.main }} />
                </Box>
                <Typography variant="h4" fontWeight={700} sx={{ color: theme.palette.success.main }}>
                  {stats.withScores}
                </Typography>
                <Typography variant="body2" color="text.secondary" fontWeight={500}>
                  Assessed
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          {loading ? <ShimmerCard /> : (
            <Card elevation={0} sx={{ border: 1, borderColor: 'divider', height: '100%' }}>
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box 
                  sx={{ 
                    width: 56, 
                    height: 56, 
                    borderRadius: '50%', 
                    bgcolor: alpha(theme.palette.info.main, 0.2),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2
                  }}
                >
                  <Star sx={{ color: theme.palette.info.main }} />
                </Box>
                <Typography variant="h4" fontWeight={700} sx={{ color: theme.palette.info.main }}>
                  {stats.averageOverallScore}
                </Typography>
                <Typography variant="body2" color="text.secondary" fontWeight={500}>
                  Avg Overall Score
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          {loading ? <ShimmerCard /> : (
            <Card elevation={0} sx={{ border: 1, borderColor: 'divider', height: '100%' }}>
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box 
                  sx={{ 
                    width: 56, 
                    height: 56, 
                    borderRadius: '50%', 
                    bgcolor: alpha(theme.palette.warning.main, 0.2),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    mx: 'auto',
                    mb: 2
                  }}
                >
                  <Analytics sx={{ color: theme.palette.warning.main }} />
                </Box>
                <Typography variant="h4" fontWeight={700} sx={{ color: theme.palette.warning.main }}>
                  {stats.averageTechnicalScore}
                </Typography>
                <Typography variant="body2" color="text.secondary" fontWeight={500}>
                  Avg Technical Score
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Search Controls */}
      {loading ? <ShimmerControls /> : (
        <Paper elevation={0} sx={{ p: 3, mb: 3, border: 1, borderColor: 'divider' }}>
          <TextField
            placeholder="Search by student name, student ID, or test ID..."
            variant="outlined"
            size="medium"
            value={searchTerm}
            onChange={handleSearch}
            InputProps={{
              startAdornment: <Search sx={{ mr: 2, color: 'text.secondary' }} />
            }}
            sx={{ 
              maxWidth: 500,
              '& .MuiOutlinedInput-root': {
                bgcolor: 'background.paper'
              }
            }}
          />
        </Paper>
      )}

      {/* Interviews Table */}
      <Paper elevation={0} sx={{ border: 1, borderColor: 'divider', borderRadius: 2 }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: 'grey.50' }}>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Student</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Test ID</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Session</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Date & Time</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Overall Score</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Technical</TableCell>
                <TableCell sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Communication</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600, fontSize: '0.875rem' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                Array.from({ length: 6 }).map((_, index) => (
                  <ShimmerTableRow key={index} />
                ))
              ) : filteredInterviews.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 6 }}>
                    <Alert 
                      severity="info" 
                      sx={{ 
                        border: 'none',
                        bgcolor: 'transparent'
                      }}
                    >
                      <Typography variant="h6" gutterBottom>
                        No interviews found
                      </Typography>
                      <Typography variant="body2">
                        {searchTerm 
                          ? "Try adjusting your search criteria to find interviews." 
                          : "No interview data is available at the moment."
                        }
                      </Typography>
                    </Alert>
                  </TableCell>
                </TableRow>
              ) : (
                filteredInterviews.map((interview, index) => {
                  const dateTime = formatTimestamp(interview.timestamp);
                  return (
                    <TableRow 
                      key={interview.id} 
                      hover
                      sx={{ 
                        '&:hover': { 
                          bgcolor: 'action.hover',
                          cursor: 'pointer'
                        },
                        animation: `fadeInUp 0.3s ease-out ${index * 0.05}s both`
                      }}
                      onClick={() => handleView(interview)}
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar 
                            sx={{ 
                              width: 48, 
                              height: 48, 
                              bgcolor: theme.palette.primary.main,
                              fontWeight: 600,
                              fontSize: '1.1rem'
                            }}
                          >
                            {interview.studentName.charAt(0).toUpperCase()}
                          </Avatar>
                          <Box>
                            <Typography variant="subtitle2" fontWeight={600}>
                              {interview.studentName}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Student ID: {interview.studentId}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Typography 
                          variant="body2" 
                          fontFamily="monospace"
                          sx={{ 
                            bgcolor: 'grey.100',
                            px: 1,
                            py: 0.5,
                            borderRadius: 1,
                            fontSize: '0.75rem'
                          }}
                        >
                          {interview.testId}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={`Session ${interview.sessionId}`}
                          size="small"
                          variant="outlined"
                          color="primary"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            {dateTime.date}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {dateTime.time}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        {interview.overallScore !== null ? (
                          <Box display="flex" alignItems="center" gap={1}>
                            {getScoreIcon(interview.overallScore)}
                            <Chip
                              label={interview.overallScore}
                              color={getScoreColor(interview.overallScore)}
                              size="small"
                              sx={{ fontWeight: 600 }}
                            />
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Not scored
                          </Typography>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        {interview.technicalScore !== null ? (
                          <Chip
                            label={interview.technicalScore}
                            color={getScoreColor(interview.technicalScore)}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Not scored
                          </Typography>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        {interview.communicationScore !== null ? (
                          <Chip
                            label={interview.communicationScore}
                            color={getScoreColor(interview.communicationScore)}
                            size="small"
                            sx={{ fontWeight: 600 }}
                          />
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Not scored
                          </Typography>
                        )}
                      </TableCell>
                      
                      <TableCell align="center">
                        <Tooltip title="View Interview Details">
                          <IconButton 
                            size="medium" 
                            color="primary"
                            onClick={(e) => {
                              e.stopPropagation(); // Prevent row click
                              handleView(interview);
                            }}
                            sx={{
                              border: 1,
                              borderColor: theme.palette.primary.main,
                              '&:hover': {
                                bgcolor: theme.palette.primary.main,
                                color: 'white',
                                transform: 'scale(1.1)',
                                transition: 'all 0.2s ease-in-out'
                              }
                            }}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Loading overlay for refresh */}
      {refreshing && (
        <Box
          position="fixed"
          top={0}
          left={0}
          right={0}
          bottom={0}
          bgcolor="rgba(0, 0, 0, 0.1)"
          display="flex"
          alignItems="center"
          justifyContent="center"
          zIndex={9999}
        >
          <Paper 
            elevation={8} 
            sx={{ 
              p: 3, 
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              gap: 2
            }}
          >
            <CircularProgress size={24} />
            <Typography variant="body2">Refreshing data...</Typography>
          </Paper>
        </Box>
      )}

      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </Container>
  );
};

export default MentorMockInterviewSystem;