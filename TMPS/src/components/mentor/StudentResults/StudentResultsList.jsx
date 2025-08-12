import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardHeader,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Typography,
  TextField,
  InputAdornment,
  Grid,
  Skeleton,
  Button,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import studentResultsService from '../../../services/API/studentresults';

// Skeleton Component
const ResultsTableSkeleton = () => (
  <TableContainer component={Paper} variant="outlined">
    <Table>
      <TableHead>
        <TableRow>
          {Array.from({ length: 6 }).map((_, index) => (
            <TableCell key={index}>
              <Skeleton variant="text" width="100%" height={24} />
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {Array.from({ length: 4 }).map((_, rowIndex) => (
          <TableRow key={rowIndex}>
            {Array.from({ length: 6 }).map((_, cellIndex) => (
              <TableCell key={cellIndex}>
                {cellIndex === 5 ? (
                  <Box display="flex" justifyContent="center">
                    <Skeleton variant="circular" width={32} height={32} />
                  </Box>
                ) : (
                  <Skeleton variant="text" width="80px" height={20} />
                )}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);

const MentorStudentResultsList = () => {
  const navigate = useNavigate();
  const [studentResults, setStudentResults] = useState([]);
  const [filteredResults, setFilteredResults] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchStudentResults();
  }, []);

  useEffect(() => {
    const filtered = studentResults.filter(student =>
      student.Student_Name?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredResults(filtered);
  }, [studentResults, searchTerm]);

  const fetchStudentResults = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError('');
      
      const response = await studentResultsService.getAllStudentResults();
      
      if (response.success) {
        console.log('API Response:', response.data);
        setStudentResults(response.data);
      } else {
        setError(response.error || 'Failed to fetch student results');
      }
    } catch (error) {
      console.error('Error fetching student results:', error);
      setError('Failed to fetch student results. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    fetchStudentResults(true);
  };

  const handleViewDetails = (student) => {
    // Navigate to the ViewStudentResults page with the student ID
    navigate(`/mentor/student-results/view/${student.Student_ID}`);
  };

  const getPerformanceColor = (percentage) => {
    const numPercentage = parseFloat(percentage);
    if (numPercentage >= 80) return 'success.main';
    if (numPercentage >= 60) return 'info.main';
    if (numPercentage >= 40) return 'warning.main';
    return 'error.main';
  };

  const getPerformanceChipColor = (percentage) => {
    const numPercentage = parseFloat(percentage);
    if (numPercentage >= 80) return 'success';
    if (numPercentage >= 60) return 'info';
    if (numPercentage >= 40) return 'warning';
    return 'error';
  };

  const getPerformanceLabel = (percentage) => {
    const numPercentage = parseFloat(percentage);
    if (numPercentage >= 90) return 'Excellent';
    if (numPercentage >= 80) return 'Good';
    if (numPercentage >= 60) return 'Average';
    if (numPercentage > 0) return 'Poor';
    return 'N/A';
  };

  return (
    <Box>
      <Card>
        <CardHeader
          title={
            <Box display="flex" alignItems="center" gap={1}>
              <TrendingUpIcon />
              <Typography variant="h6">Student Results</Typography>
            </Box>
          }
          action={
            <Button
              variant="outlined"
              size="small"
              startIcon={refreshing ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={handleRefresh}
              disabled={loading || refreshing}
            >
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
          }
        />
        <CardContent>
          {/* Search Filter */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={4}>
              {loading ? (
                <Skeleton variant="rounded" width="100%" height={40} />
              ) : (
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Search students..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              )}
            </Grid>
          </Grid>

          {error && (
            <Alert 
              severity="error" 
              sx={{ mb: 2 }}
              action={
                <Button color="inherit" size="small" onClick={handleRefresh}>
                  Retry
                </Button>
              }
            >
              {error}
            </Alert>
          )}

          {loading ? (
            <ResultsTableSkeleton />
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Student Name</strong></TableCell>
                    <TableCell><strong>Attendance %</strong></TableCell>
                    <TableCell><strong>Mock Test %</strong></TableCell>
                    <TableCell><strong>Mock Interview %</strong></TableCell>
                    <TableCell><strong>Standup Call %</strong></TableCell>
                    <TableCell align="center"><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredResults.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} align="center">
                        <Typography variant="body2" color="text.secondary">
                          {searchTerm 
                            ? 'No students found matching your search.' 
                            : 'No student results available.'}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredResults.map((student) => (
                      <TableRow key={student.Student_ID} hover>
                        <TableCell>
                          <Typography variant="subtitle2" fontWeight="medium">
                            {student.Student_Name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            ID: {student.Student_ID}
                          </Typography>
                        </TableCell>
                        
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography
                              variant="body1"
                              fontWeight="medium"
                              sx={{ color: getPerformanceColor(student.Avg_Attendance_Percentage) }}
                            >
                              {student.Avg_Attendance_Percentage}%
                            </Typography>
                            <Chip
                              size="small"
                              label={getPerformanceLabel(student.Avg_Attendance_Percentage)}
                              color={getPerformanceChipColor(student.Avg_Attendance_Percentage)}
                              variant="outlined"
                            />
                          </Box>
                        </TableCell>
                        
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography
                              variant="body1"
                              fontWeight="medium"
                              sx={{ color: getPerformanceColor(student.Overall_Mock_Test_Percentage) }}
                            >
                              {student.Overall_Mock_Test_Percentage}%
                            </Typography>
                            {parseFloat(student.Overall_Mock_Test_Percentage) > 0 && (
                              <Chip
                                size="small"
                                label={getPerformanceLabel(student.Overall_Mock_Test_Percentage)}
                                color={getPerformanceChipColor(student.Overall_Mock_Test_Percentage)}
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </TableCell>
                        
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography
                              variant="body1"
                              fontWeight="medium"
                              sx={{ color: getPerformanceColor(student.Overall_Mock_Interview_Percentage) }}
                            >
                              {student.Overall_Mock_Interview_Percentage}%
                            </Typography>
                            {parseFloat(student.Overall_Mock_Interview_Percentage) > 0 && (
                              <Chip
                                size="small"
                                label={getPerformanceLabel(student.Overall_Mock_Interview_Percentage)}
                                color={getPerformanceChipColor(student.Overall_Mock_Interview_Percentage)}
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </TableCell>
                        
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography
                              variant="body1"
                              fontWeight="medium"
                              sx={{ color: getPerformanceColor(student.Overall_Standup_Call_Percentage) }}
                            >
                              {student.Overall_Standup_Call_Percentage}%
                            </Typography>
                            {parseFloat(student.Overall_Standup_Call_Percentage) > 0 && (
                              <Chip
                                size="small"
                                label={getPerformanceLabel(student.Overall_Standup_Call_Percentage)}
                                color={getPerformanceChipColor(student.Overall_Standup_Call_Percentage)}
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </TableCell>
                        
                        <TableCell align="center">
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              sx={{
                                color: 'text.secondary',
                                '&:hover': {
                                  color: 'primary.main',
                                  backgroundColor: 'transparent',
                                }
                              }}
                              onClick={() => handleViewDetails(student)}
                            >
                              <VisibilityIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Summary Stats */}
          {!loading && filteredResults.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="primary">
                      {filteredResults.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Students
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="success.main">
                      {filteredResults.filter(s => parseFloat(s.Avg_Attendance_Percentage) >= 80).length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Good Attendance
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="info.main">
                      {(filteredResults.reduce((sum, s) => sum + parseFloat(s.Avg_Attendance_Percentage), 0) / filteredResults.length).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Attendance
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="warning.main">
                      {(filteredResults.reduce((sum, s) => sum + parseFloat(s.Overall_Mock_Test_Percentage), 0) / filteredResults.length).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Mock Test
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default MentorStudentResultsList;