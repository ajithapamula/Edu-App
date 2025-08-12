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
  IconButton,
  Tooltip,
  LinearProgress,
  Avatar,
  Alert,
  Button,
  Skeleton,
  Divider,
  Stack,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  ArrowBack as ArrowBackIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  Person as PersonIcon,
  Assessment as AssessmentIcon,
  School as SchoolIcon,
  EmojiEvents as TrophyIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import studentResultsService from '../../../services/API/studentresults';

const MentorViewStudentResults = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const [studentData, setStudentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      fetchStudentData();
    }
  }, [id]);

  const fetchStudentData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await studentResultsService.getAllStudentResults();
      
      if (response.success && response.data) {
        const student = response.data.find(s => s.Student_ID === parseInt(id));
        
        if (student) {
          setStudentData(student);
        } else {
          setError('Student not found');
        }
      } else {
        setError(response.error || 'Failed to fetch student data');
      }
    } catch (error) {
      console.error('Error fetching student data:', error);
      setError('Failed to fetch student data');
    } finally {
      setLoading(false);
    }
  };

  const getPerformanceColor = (percentage) => {
    const numPercentage = parseFloat(percentage);
    if (numPercentage >= 90) return 'success';
    if (numPercentage >= 80) return 'info';
    if (numPercentage >= 70) return 'warning';
    if (numPercentage >= 60) return 'secondary';
    return 'error';
  };

  const getPerformanceGradient = (percentage) => {
    const numPercentage = parseFloat(percentage);
    if (numPercentage >= 90) return 'linear-gradient(135deg, #4caf50, #81c784)';
    if (numPercentage >= 80) return 'linear-gradient(135deg, #2196f3, #64b5f6)';
    if (numPercentage >= 70) return 'linear-gradient(135deg, #ff9800, #ffb74d)';
    if (numPercentage >= 60) return 'linear-gradient(135deg, #9c27b0, #ba68c8)';
    return 'linear-gradient(135deg, #f44336, #e57373)';
  };

  const getPerformanceLabel = (percentage) => {
    const numPercentage = parseFloat(percentage);
    if (numPercentage >= 90) return 'Outstanding';
    if (numPercentage >= 80) return 'Excellent';
    if (numPercentage >= 70) return 'Good';
    if (numPercentage >= 60) return 'Satisfactory';
    if (numPercentage > 0) return 'Needs Improvement';
    return 'No Data';
  };

  const getOverallStatus = (student) => {
    const attendance = parseFloat(student.Avg_Attendance_Percentage);
    const mockTest = parseFloat(student.Overall_Mock_Test_Percentage);
    const mockInterview = parseFloat(student.Overall_Mock_Interview_Percentage);
    const standupCall = parseFloat(student.Overall_Standup_Call_Percentage);
    
    const averagePerformance = (attendance + mockTest + mockInterview + standupCall) / 4;
    
    if (averagePerformance >= 85) return { status: 'Outstanding Performance', color: 'success', icon: <TrophyIcon /> };
    if (averagePerformance >= 75) return { status: 'Excellent Progress', color: 'info', icon: <AssessmentIcon /> };
    if (averagePerformance >= 65) return { status: 'Good Development', color: 'warning', icon: <SchoolIcon /> };
    if (averagePerformance >= 50) return { status: 'Satisfactory', color: 'secondary', icon: <TimelineIcon /> };
    return { status: 'Needs Improvement', color: 'error', icon: <PersonIcon /> };
  };

  const MetricCard = ({ title, percentage, icon, gradient, index }) => (
    <Grid item xs={12} sm={6} md={3}>
      <Paper 
        sx={{ 
          p: 3, 
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
          background: gradient,
          color: 'white',
          transition: 'all 0.3s ease-in-out',
          transform: 'translateY(0)',
          '&:hover': {
            transform: 'translateY(-8px)',
            boxShadow: theme.shadows[12],
          },
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: alpha('#fff', 0.1),
            backdropFilter: 'blur(10px)',
          }
        }}
        elevation={6}
      >
        <Box position="relative" zIndex={1}>
          <Box display="flex" justifyContent="center" mb={2}>
            {icon}
          </Box>
          <Typography 
            variant="h2" 
            fontWeight="bold"
            sx={{ 
              mb: 1,
              textShadow: '0 2px 4px rgba(0,0,0,0.3)',
              fontSize: { xs: '2.5rem', sm: '3rem' }
            }}
          >
            {percentage}%
          </Typography>
          <Typography 
            variant="body1" 
            sx={{ 
              mb: 2,
              fontWeight: 500,
              textShadow: '0 1px 2px rgba(0,0,0,0.3)'
            }}
          >
            {title}
          </Typography>
          <Chip
            label={getPerformanceLabel(percentage)}
            sx={{
              bgcolor: alpha('#fff', 0.2),
              color: 'white',
              fontWeight: 'bold',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.3)'
            }}
            size="small"
          />
        </Box>
      </Paper>
    </Grid>
  );

  if (loading) {
    return (
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        {/* Enhanced Header Skeleton */}
        <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }} elevation={4}>
          <Box display="flex" alignItems="center">
            <Skeleton variant="circular" width={48} height={48} sx={{ mr: 2, bgcolor: alpha('#fff', 0.3) }} />
            <Box>
              <Skeleton variant="text" width={350} height={36} sx={{ bgcolor: alpha('#fff', 0.3) }} />
              <Skeleton variant="text" width={200} height={20} sx={{ bgcolor: alpha('#fff', 0.2) }} />
            </Box>
          </Box>
        </Paper>

        <Grid container spacing={3}>
          {/* Student Info Skeleton */}
          <Grid item xs={12} lg={4}>
            <Card elevation={6} sx={{ height: '100%' }}>
              <CardHeader 
                title={<Skeleton variant="text" width={180} height={28} />}
                sx={{ pb: 2 }}
              />
              <Divider />
              <CardContent sx={{ pt: 3 }}>
                <Box display="flex" alignItems="center" mb={4}>
                  <Skeleton variant="circular" width={80} height={80} sx={{ mr: 3 }} />
                  <Box flex={1}>
                    <Skeleton variant="text" width={160} height={28} />
                    <Skeleton variant="text" width={120} height={20} />
                  </Box>
                </Box>
                
                <Box textAlign="center">
                  <Skeleton variant="text" width={140} height={20} sx={{ mx: 'auto', mb: 2 }} />
                  <Skeleton variant="rounded" width={150} height={40} sx={{ mx: 'auto' }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Performance Cards Skeleton */}
          <Grid item xs={12} lg={8}>
            <Grid container spacing={3}>
              {Array.from({ length: 4 }).map((_, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <Paper sx={{ p: 3, textAlign: 'center', height: 200 }} elevation={6}>
                    <Skeleton variant="circular" width={40} height={40} sx={{ mx: 'auto', mb: 2 }} />
                    <Skeleton variant="text" width={80} height={48} sx={{ mx: 'auto', mb: 1 }} />
                    <Skeleton variant="text" width={100} height={20} sx={{ mx: 'auto', mb: 2 }} />
                    <Skeleton variant="rounded" width={90} height={24} sx={{ mx: 'auto' }} />
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Grid>

        {/* Progress Analysis Skeleton */}
        <Card sx={{ mt: 4 }} elevation={6}>
          <CardHeader title={<Skeleton variant="text" width={200} height={28} />} />
          <Divider />
          <CardContent>
            <Grid container spacing={4}>
              {Array.from({ length: 4 }).map((_, index) => (
                <Grid item xs={12} md={6} key={index}>
                  <Box sx={{ p: 2 }}>
                    <Box display="flex" justifyContent="space-between" mb={2}>
                      <Skeleton variant="text" width={180} height={24} />
                      <Skeleton variant="text" width={50} height={24} />
                    </Box>
                    <Skeleton variant="rounded" width="100%" height={12} sx={{ borderRadius: 6 }} />
                  </Box>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (error || !studentData) {
    return (
      <Box sx={{ p: { xs: 2, md: 3 } }}>
        <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }} elevation={4}>
          <Box display="flex" alignItems="center">
            <IconButton onClick={() => navigate(-1)} sx={{ mr: 2, color: 'white' }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" fontWeight="bold">Student Performance</Typography>
          </Box>
        </Paper>
        
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={() => fetchStudentData()}>
              Retry
            </Button>
          }
        >
          {error || 'Student not found'}
        </Alert>
        
        <Button 
          onClick={() => navigate(-1)} 
          startIcon={<ArrowBackIcon />}
          variant="contained"
          size="large"
        >
          Go Back
        </Button>
      </Box>
    );
  }

  const overallStatus = getOverallStatus(studentData);
  const averageScore = (
    (parseFloat(studentData.Avg_Attendance_Percentage) +
     parseFloat(studentData.Overall_Mock_Test_Percentage) +
     parseFloat(studentData.Overall_Mock_Interview_Percentage) +
     parseFloat(studentData.Overall_Standup_Call_Percentage)) / 4
  ).toFixed(1);

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, minHeight: '100vh', bgcolor: 'grey.50' }}>
      {/* Enhanced Header */}
      <Paper 
        sx={{ 
          p: 4, 
          mb: 4, 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          position: 'relative',
          overflow: 'hidden'
        }} 
        elevation={8}
      >
        <Box 
          sx={{
            position: 'absolute',
            top: 0,
            right: 0,
            width: 200,
            height: 200,
            background: alpha('#fff', 0.1),
            borderRadius: '50%',
            transform: 'translate(25%, -25%)'
          }}
        />
        <Box position="relative" zIndex={1}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center">
              <IconButton 
                onClick={() => navigate(-1)} 
                sx={{ 
                  mr: 2, 
                  color: 'white',
                  bgcolor: alpha('#fff', 0.2),
                  '&:hover': { bgcolor: alpha('#fff', 0.3) }
                }}
              >
                <ArrowBackIcon />
              </IconButton>
              <Box>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                  Student Performance Dashboard
                </Typography>
                <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
                  Comprehensive performance analysis and insights
                </Typography>
              </Box>
            </Box>
            
            <Stack direction="row" spacing={1}>
              <Tooltip title="Download Report">
                <IconButton 
                  sx={{ 
                    color: 'white',
                    bgcolor: alpha('#fff', 0.2),
                    '&:hover': { bgcolor: alpha('#fff', 0.3) }
                  }}
                >
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Print Report">
                <IconButton 
                  sx={{ 
                    color: 'white',
                    bgcolor: alpha('#fff', 0.2),
                    '&:hover': { bgcolor: alpha('#fff', 0.3) }
                  }}
                >
                  <PrintIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Box>
        </Box>
      </Paper>

      <Grid container spacing={4}>
        {/* Enhanced Student Information */}
        <Grid item xs={12} lg={4}>
          <Card elevation={8} sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
            <Box 
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 120,
                background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              }}
            />
            
            <CardContent sx={{ pt: 6, position: 'relative', zIndex: 1 }}>
              <Box display="flex" flexDirection="column" alignItems="center" mb={4}>
                <Avatar 
                  sx={{ 
                    width: 100, 
                    height: 100, 
                    bgcolor: 'white',
                    color: 'primary.main',
                    fontSize: '2.5rem',
                    fontWeight: 'bold',
                    border: '4px solid white',
                    boxShadow: theme.shadows[8],
                    mb: 2
                  }}
                >
                  {studentData.Student_Name?.charAt(0) || 'S'}
                </Avatar>
                
                <Typography variant="h5" fontWeight="bold" textAlign="center" gutterBottom>
                  {studentData.Student_Name}
                </Typography>
                
                <Chip
                  label={`ID: ${studentData.Student_ID}`}
                  variant="outlined"
                  size="medium"
                  sx={{ mb: 3 }}
                />
              </Box>
              
              <Divider sx={{ my: 3 }} />
              
              <Box textAlign="center">
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Overall Performance Rating
                </Typography>
                
                <Box display="flex" justifyContent="center" alignItems="center" mb={2}>
                  {overallStatus.icon}
                  <Typography variant="h4" fontWeight="bold" sx={{ ml: 1 }}>
                    {averageScore}%
                  </Typography>
                </Box>
                
                <Chip
                  label={overallStatus.status}
                  color={overallStatus.color}
                  size="large"
                  sx={{ 
                    fontWeight: 'bold',
                    px: 2,
                    py: 1,
                    fontSize: '0.875rem'
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Enhanced Performance Metrics */}
        <Grid item xs={12} lg={8}>
          <Grid container spacing={3}>
            <MetricCard
              title="Attendance"
              percentage={studentData.Avg_Attendance_Percentage}
              icon={<PersonIcon sx={{ fontSize: 40, mb: 1 }} />}
              gradient={getPerformanceGradient(studentData.Avg_Attendance_Percentage)}
              index={0}
            />
            <MetricCard
              title="Mock Tests"
              percentage={studentData.Overall_Mock_Test_Percentage}
              icon={<AssessmentIcon sx={{ fontSize: 40, mb: 1 }} />}
              gradient={getPerformanceGradient(studentData.Overall_Mock_Test_Percentage)}
              index={1}
            />
            <MetricCard
              title="Mock Interviews"
              percentage={studentData.Overall_Mock_Interview_Percentage}
              icon={<SchoolIcon sx={{ fontSize: 40, mb: 1 }} />}
              gradient={getPerformanceGradient(studentData.Overall_Mock_Interview_Percentage)}
              index={2}
            />
            <MetricCard
              title="Standup Calls"
              percentage={studentData.Overall_Standup_Call_Percentage}
              icon={<TimelineIcon sx={{ fontSize: 40, mb: 1 }} />}
              gradient={getPerformanceGradient(studentData.Overall_Standup_Call_Percentage)}
              index={3}
            />
          </Grid>
        </Grid>
      </Grid>

      {/* Enhanced Performance Analysis */}
      <Card sx={{ mt: 4 }} elevation={8}>
        <CardHeader 
          title={
            <Box display="flex" alignItems="center">
              <TrendingUpIcon sx={{ mr: 2, color: 'primary.main' }} />
              <Typography variant="h5" fontWeight="bold">
                Detailed Performance Analysis
              </Typography>
            </Box>
          }
        />
        <Divider />
        <CardContent sx={{ p: 4 }}>
          <Grid container spacing={4}>
            {[
              { label: 'Attendance Performance', value: studentData.Avg_Attendance_Percentage },
              { label: 'Mock Test Performance', value: studentData.Overall_Mock_Test_Percentage },
              { label: 'Mock Interview Performance', value: studentData.Overall_Mock_Interview_Percentage },
              { label: 'Standup Call Performance', value: studentData.Overall_Standup_Call_Percentage },
            ].map((item, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Paper 
                  sx={{ 
                    p: 3, 
                    background: alpha(theme.palette.primary.main, 0.02),
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      background: alpha(theme.palette.primary.main, 0.04),
                      transform: 'translateY(-2px)',
                      boxShadow: theme.shadows[8]
                    }
                  }}
                  elevation={2}
                >
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" fontWeight="600">
                      {item.label}
                    </Typography>
                    <Chip
                      label={`${item.value}%`}
                      color={getPerformanceColor(item.value)}
                      variant="filled"
                      size="medium"
                      sx={{ fontWeight: 'bold', minWidth: 70 }}
                    />
                  </Box>
                  
                  <LinearProgress
                    variant="determinate"
                    value={parseFloat(item.value)}
                    color={getPerformanceColor(item.value)}
                    sx={{ 
                      height: 12, 
                      borderRadius: 6,
                      backgroundColor: alpha(theme.palette.grey[300], 0.3),
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 6,
                        backgroundImage: getPerformanceGradient(item.value)
                      }
                    }}
                  />
                  
                  <Box display="flex" justifyContent="space-between" mt={1}>
                    <Typography variant="caption" color="text.secondary">
                      {getPerformanceLabel(item.value)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Target: 80%
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Enhanced Performance Summary */}
      <Card sx={{ mt: 4, mb: 4 }} elevation={8}>
        <CardHeader 
          title={
            <Box display="flex" alignItems="center">
              <TrophyIcon sx={{ mr: 2, color: 'warning.main' }} />
              <Typography variant="h5" fontWeight="bold">
                Performance Summary & Insights
              </Typography>
            </Box>
          }
        />
        <Divider />
        <CardContent>
          <Grid container spacing={3}>
            {[
              { 
                label: 'Student ID', 
                value: studentData.Student_ID, 
                color: 'primary.main',
                icon: <PersonIcon />
              },
              { 
                label: 'Best Performance', 
                value: `${Math.max(
                  parseFloat(studentData.Avg_Attendance_Percentage),
                  parseFloat(studentData.Overall_Mock_Test_Percentage),
                  parseFloat(studentData.Overall_Mock_Interview_Percentage),
                  parseFloat(studentData.Overall_Standup_Call_Percentage)
                ).toFixed(1)}%`, 
                color: 'success.main',
                icon: <TrophyIcon />
              },
              { 
                label: 'Average Score', 
                value: `${averageScore}%`, 
                color: 'info.main',
                icon: <AssessmentIcon />
              },
              { 
                label: 'Overall Status', 
                value: overallStatus.status, 
                color: `${overallStatus.color}.main`,
                icon: overallStatus.icon,
                isChip: true
              },
            ].map((item, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Paper 
                  sx={{ 
                    p: 3, 
                    textAlign: 'center',
                    background: alpha(item.color.includes('.') ? theme.palette[item.color.split('.')[0]][item.color.split('.')[1]] : item.color, 0.1),
                    border: `2px solid ${alpha(item.color.includes('.') ? theme.palette[item.color.split('.')[0]][item.color.split('.')[1]] : item.color, 0.2)}`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: theme.shadows[12]
                    }
                  }}
                  elevation={4}
                >
                  <Box display="flex" justifyContent="center" mb={2}>
                    {React.cloneElement(item.icon, { 
                      sx: { 
                        fontSize: 40, 
                        color: item.color.includes('.') ? 
                          theme.palette[item.color.split('.')[0]][item.color.split('.')[1]] : 
                          item.color 
                      } 
                    })}
                  </Box>
                  
                  {item.isChip ? (
                    <Chip
                      label={item.value}
                      color={overallStatus.color}
                      size="large"
                      sx={{ 
                        fontWeight: 'bold',
                        mb: 1,
                        fontSize: '0.875rem'
                      }}
                    />
                  ) : (
                    <Typography 
                      variant="h5" 
                      fontWeight="bold"
                      sx={{ 
                        color: item.color.includes('.') ? 
                          theme.palette[item.color.split('.')[0]][item.color.split('.')[1]] : 
                          item.color,
                        mb: 1
                      }}
                    >
                      {item.value}
                    </Typography>
                  )}
                  
                  <Typography variant="body2" color="text.secondary" fontWeight="500">
                    {item.label}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default MentorViewStudentResults;