import React, { useState, useEffect } from 'react';
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
  Alert,
  Card,
  CardContent,
  IconButton,
  Skeleton,
  Chip,
  Avatar,
  Tooltip,
  Fade,
  Zoom,
  Grid,
  useTheme,
  alpha,
  styled,
  keyframes
} from '@mui/material';
import { 
  Refresh, 
  Visibility, 
  Person, 
  School,
  TrendingUp
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// FIXED: Use consistent import name
import dailyStandupApiService from '../../../services/API/dailystandup';

// Shimmer animation keyframes
const shimmer = keyframes`
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
`;

// Styled components for shimmer effects
const ShimmerBox = styled(Box)(({ theme, width = '100%', height = '20px', borderRadius = '4px' }) => ({
  width,
  height,
  borderRadius,
  background: `linear-gradient(90deg, ${alpha(theme.palette.grey[300], 0.2)} 25%, ${alpha(theme.palette.grey[300], 0.4)} 50%, ${alpha(theme.palette.grey[300], 0.2)} 75%)`,
  backgroundSize: '200px 100%',
  animation: `${shimmer} 1.5s infinite linear`,
}));

const ShimmerCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(90deg, ${alpha(theme.palette.grey[300], 0.1)} 25%, ${alpha(theme.palette.grey[300], 0.2)} 50%, ${alpha(theme.palette.grey[300], 0.1)} 75%)`,
  backgroundSize: '200px 100%',
  animation: `${shimmer} 1.5s infinite linear`,
  borderRadius: 12,
  boxShadow: theme.shadows[4],
}));

const ShimmerAvatar = styled(Avatar)(({ theme }) => ({
  background: `linear-gradient(90deg, ${alpha(theme.palette.grey[300], 0.2)} 25%, ${alpha(theme.palette.grey[300], 0.4)} 50%, ${alpha(theme.palette.grey[300], 0.2)} 75%)`,
  backgroundSize: '200px 100%',
  animation: `${shimmer} 1.5s infinite linear`,
}));

const ShimmerTableCell = styled(TableCell)(({ theme }) => ({
  '& .shimmer-content': {
    background: `linear-gradient(90deg, ${alpha(theme.palette.grey[300], 0.1)} 25%, ${alpha(theme.palette.grey[300], 0.2)} 50%, ${alpha(theme.palette.grey[300], 0.1)} 75%)`,
    backgroundSize: '200px 100%',
    animation: `${shimmer} 1.5s infinite linear`,
    borderRadius: 4,
  }
}));

const MentorDailyStandupsList = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [count, setCount] = useState(0);
  const theme = useTheme();
  const navigate = useNavigate();

  // Load data from API
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Loading standup students from API...');
      
      // FIXED: Use consistent API service name
      const response = await dailyStandupApiService.getAllStandupStudents();
      console.log('API Response:', response);
      
      // Set the actual data from API
      setStudents(response || []);
      setCount(response ? response.length : 0);
      
    } catch (err) {
      console.error('Error loading data:', err);
      setError(err.message);
      setStudents([]);
      setCount(0);
    } finally {
      setLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    loadData();
  };

  const handleViewStudent = (student) => {
    // FIXED: Navigate to the correct route that matches App.jsx
    console.log('Navigating to view student:', student.Student_ID);
    navigate(`/mentor/daily-standups/view/${student.Student_ID}`);
  };

  // Generate avatar color based on student ID
  const getAvatarColor = (studentId) => {
    const colors = [
      theme.palette.primary.main,
      theme.palette.secondary.main,
      theme.palette.error.main,
      theme.palette.warning.main,
      theme.palette.info.main,
      theme.palette.success.main,
    ];
    const index = studentId ? studentId.toString().charCodeAt(0) % colors.length : 0;
    return colors[index];
  };

  // Shimmer loading components
  const HeaderShimmer = () => (
    <Box 
      sx={{
        background: `linear-gradient(90deg, ${alpha(theme.palette.grey[300], 0.1)} 25%, ${alpha(theme.palette.grey[300], 0.2)} 50%, ${alpha(theme.palette.grey[300], 0.1)} 75%)`,
        backgroundSize: '200px 100%',
        animation: `${shimmer} 1.5s infinite linear`,
        p: 3,
        borderRadius: 3,
        mb: 4
      }}
    >
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Box display="flex" alignItems="center" gap={2}>
          <ShimmerAvatar sx={{ width: 48, height: 48 }} />
          <Box>
            <ShimmerBox width="200px" height="32px" borderRadius="8px" />
            <Box mt={1}>
              <ShimmerBox width="150px" height="16px" borderRadius="4px" />
            </Box>
          </Box>
        </Box>
        <ShimmerBox width="48px" height="48px" borderRadius="50%" />
      </Box>
    </Box>
  );

  const StatsCardShimmer = ({ delay = 0 }) => (
    <Grid item xs={12} sm={6} md={4}>
      <ShimmerCard 
        sx={{ 
          animationDelay: `${delay}ms`,
          minHeight: 120
        }}
      >
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <ShimmerBox width="60px" height="36px" borderRadius="8px" />
              <Box mt={1}>
                <ShimmerBox width="100px" height="16px" borderRadius="4px" />
              </Box>
            </Box>
            <ShimmerBox width="56px" height="56px" borderRadius="50%" />
          </Box>
        </CardContent>
      </ShimmerCard>
    </Grid>
  );

  const TableRowShimmer = ({ delay = 0 }) => (
    <TableRow sx={{ animationDelay: `${delay}ms` }}>
      <ShimmerTableCell>
        <Box display="flex" alignItems="center" gap={2}>
          <ShimmerBox width="40px" height="40px" borderRadius="50%" />
          <Box>
            <ShimmerBox width="120px" height="20px" borderRadius="4px" />
            <Box mt={0.5}>
              <ShimmerBox width="80px" height="16px" borderRadius="4px" />
            </Box>
          </Box>
        </Box>
      </ShimmerTableCell>
      <ShimmerTableCell>
        <ShimmerBox width="80px" height="24px" borderRadius="12px" />
      </ShimmerTableCell>
      <ShimmerTableCell align="center">
        <Box display="flex" justifyContent="center">
          <ShimmerBox width="40px" height="40px" borderRadius="50%" />
        </Box>
      </ShimmerTableCell>
    </TableRow>
  );

  // Show error state
  if (error && !loading) {
    return (
      <Fade in={true}>
        <Box sx={{ p: 3 }}>
          <Typography 
            variant="h4" 
            component="h1" 
            gutterBottom
            sx={{
              background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 'bold',
              mb: 3
            }}
          >
            Daily Standup Students
          </Typography>
          <Alert 
            severity="error" 
            sx={{
              borderRadius: 2,
              '& .MuiAlert-icon': {
                fontSize: '1.5rem'
              }
            }}
            action={
              <IconButton 
                size="small" 
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
            }
          >
            Failed to load data: {error}
          </Alert>
        </Box>
      </Fade>
    );
  }

  return (
    <Fade in={true}>
      <Box sx={{ p: 3, minHeight: '100vh', backgroundColor: alpha(theme.palette.primary.main, 0.02) }}>
        {/* Header Section */}
        {loading ? (
          <HeaderShimmer />
        ) : (
          <Box 
            display="flex" 
            justifyContent="space-between" 
            alignItems="center" 
            mb={4}
            sx={{
              background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
              p: 3,
              borderRadius: 3,
              backdropFilter: 'blur(10px)',
              border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
            }}
          >
            <Box display="flex" alignItems="center" gap={2}>
              <Avatar 
                sx={{ 
                  bgcolor: theme.palette.primary.main,
                  width: 48,
                  height: 48,
                  boxShadow: theme.shadows[8]
                }}
              >
                <School />
              </Avatar>
              <Box>
                <Typography 
                  variant="h4" 
                  component="h1"
                  sx={{
                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    fontWeight: 'bold',
                    mb: 0.5
                  }}
                >
                  Daily Standup Students
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Manage and view student information
                </Typography>
              </Box>
            </Box>
            
            <Tooltip title="Refresh Data">
              <IconButton 
                onClick={handleRefresh} 
                disabled={loading}
                sx={{
                  bgcolor: theme.palette.background.paper,
                  boxShadow: theme.shadows[4],
                  '&:hover': {
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    transform: 'rotate(180deg)',
                    transition: 'all 0.3s ease-in-out'
                  },
                  '&:disabled': {
                    bgcolor: alpha(theme.palette.action.disabled, 0.1)
                  }
                }}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        )}

        {/* Stats Cards */}
        <Grid container spacing={3} mb={4}>
          {loading ? (
            <>
              <StatsCardShimmer delay={100} />
              <StatsCardShimmer delay={200} />
              <Grid item xs={12} sm={6} md={4}>
                <ShimmerCard sx={{ animationDelay: '300ms', minHeight: 120 }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box>
                        <ShimmerBox width="60px" height="36px" borderRadius="8px" />
                        <Box mt={1}>
                          <ShimmerBox width="100px" height="16px" borderRadius="4px" />
                        </Box>
                      </Box>
                      <ShimmerBox width="56px" height="56px" borderRadius="50%" />
                    </Box>
                  </CardContent>
                </ShimmerCard>
              </Grid>
            </>
          ) : (
            <>
              <Grid item xs={12} sm={6} md={4}>
                <Zoom in={!loading} style={{ transitionDelay: '100ms' }}>
                  <Card 
                    sx={{
                      background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                      color: 'white',
                      borderRadius: 3,
                      boxShadow: theme.shadows[8],
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        transition: 'transform 0.3s ease-in-out',
                        boxShadow: theme.shadows[12]
                      }
                    }}
                  >
                    <CardContent>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box>
                          <Typography variant="h3" fontWeight="bold">
                            {count}
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Total Students
                          </Typography>
                        </Box>
                        <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 56, height: 56 }}>
                          <Person sx={{ fontSize: 28 }} />
                        </Avatar>
                      </Box>
                    </CardContent>
                  </Card>
                </Zoom>
              </Grid>
              
              <Grid item xs={12} sm={6} md={4}>
                <Zoom in={!loading} style={{ transitionDelay: '200ms' }}>
                  <Card 
                    sx={{
                      background: `linear-gradient(135deg, ${theme.palette.secondary.main}, ${theme.palette.secondary.dark})`,
                      color: 'white',
                      borderRadius: 3,
                      boxShadow: theme.shadows[8],
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        transition: 'transform 0.3s ease-in-out',
                        boxShadow: theme.shadows[12]
                      }
                    }}
                  >
                    <CardContent>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box>
                          <Typography variant="h3" fontWeight="bold">
                            100%
                          </Typography>
                          <Typography variant="body2" sx={{ opacity: 0.9 }}>
                            Active Rate
                          </Typography>
                        </Box>
                        <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 56, height: 56 }}>
                          <TrendingUp sx={{ fontSize: 28 }} />
                        </Avatar>
                      </Box>
                    </CardContent>
                  </Card>
                </Zoom>
              </Grid>
            </>
          )}
        </Grid>

        {/* Students Table */}
        <Paper 
          sx={{
            borderRadius: 3,
            overflow: 'hidden',
            boxShadow: theme.shadows[8],
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
          }}
        >
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow 
                  sx={{
                    background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.1)})`,
                  }}
                >
                  <TableCell sx={{ fontWeight: 'bold', fontSize: '1rem' }}>Student</TableCell>
                  <TableCell sx={{ fontWeight: 'bold', fontSize: '1rem' }}>Student ID</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', fontSize: '1rem' }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  // Show shimmer loading rows
                  Array.from({ length: 6 }).map((_, index) => (
                    <TableRowShimmer key={index} delay={index * 100} />
                  ))
                ) : students.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center" sx={{ py: 8 }}>
                      <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
                        <Avatar sx={{ bgcolor: alpha(theme.palette.info.main, 0.1), width: 64, height: 64 }}>
                          <Person sx={{ fontSize: 32, color: theme.palette.info.main }} />
                        </Avatar>
                        <Typography variant="h6" color="text.secondary">
                          No students found
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Try refreshing the data or check back later
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : (
                  // Display actual API data
                  students.map((student, index) => (
                    <TableRow 
                      key={student.Student_ID} 
                      hover
                      sx={{
                        '&:hover': {
                          backgroundColor: alpha(theme.palette.primary.main, 0.04),
                          transform: 'scale(1.001)',
                          transition: 'all 0.2s ease-in-out'
                        },
                        animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`
                      }}
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar 
                            sx={{ 
                              bgcolor: getAvatarColor(student.Student_ID),
                              boxShadow: theme.shadows[4],
                              fontWeight: 'bold'
                            }}
                          >
                            {student.name ? student.name.charAt(0).toUpperCase() : 'S'}
                          </Avatar>
                          <Box>
                            <Typography variant="body1" fontWeight="medium">
                              {student.name || 'Unknown'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Active Student
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={student.Student_ID}
                          size="small"
                          sx={{
                            fontFamily: 'monospace',
                            fontWeight: 'bold',
                            bgcolor: alpha(theme.palette.info.main, 0.1),
                            color: theme.palette.info.main
                          }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Standup Details">
                          <IconButton
                            onClick={() => handleViewStudent(student)}
                            sx={{
                              bgcolor: alpha(theme.palette.primary.main, 0.1),
                              color: theme.palette.primary.main,
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
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

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
      </Box>
    </Fade>
  );
};

export default MentorDailyStandupsList;