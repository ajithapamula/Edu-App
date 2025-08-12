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
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  Skeleton,
  Breadcrumbs,
  Link,
  Badge
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Group as GroupIcon,
  Link as LinkIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  School as SchoolIcon,
  CalendarToday as CalendarTodayIcon,
  AccessTime as AccessTimeIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Schedule as ScheduledIcon,
  PlayCircleOutline as PlayCircleOutlineIcon,
  Business as BusinessIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';

// Import the sessions API
import { sessionsAPI } from '../../../services/API/sessions';

// Fallback date formatters
const fallbackDateFormatters = {
  medium: (date) => {
    if (!date) return 'Not set';
    try {
      const d = new Date(date);
      if (isNaN(d.getTime())) return 'Invalid date';
      return d.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch (error) {
      return 'Date error';
    }
  },
  dateTime: (date) => {
    if (!date) return 'Not set';
    try {
      const d = new Date(date);
      if (isNaN(d.getTime())) return 'Invalid date';
      return d.toLocaleString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch (error) {
      return 'DateTime error';
    }
  },
  time12: (date) => {
    if (!date) return 'Not set';
    try {
      const d = new Date(date);
      if (isNaN(d.getTime())) return 'Invalid time';
      return d.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit', 
        hour12: true 
      });
    } catch (error) {
      return 'Time error';
    }
  }
};

const ViewSession = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [sessionData, setSessionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      fetchSessionDetails();
    }
  }, [id]);

  const fetchSessionDetails = async () => {
    try {
      setLoading(true);
      setError('');
      
      // First try to get specific session, if that fails, get all and filter
      let session = null;
      
      try {
        session = await sessionsAPI.getById(id);
      } catch (getByIdError) {
        console.log('getById failed, trying getAll approach:', getByIdError);
        
        // Fallback: get all sessions and find the one with matching ID
        const allSessions = await sessionsAPI.getAll();
        session = allSessions.find(s => 
          s.Session_ID === parseInt(id) || 
          s.id === parseInt(id)
        );
      }
      
      if (session) {
        console.log('Session found:', session);
        setSessionData(session);
      } else {
        setError('Session not found');
      }
      
    } catch (err) {
      setError('Failed to fetch session details');
      console.error('Error fetching session details:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'active':
        return 'primary';
      case 'cancelled':
        return 'error';
      case 'scheduled':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return <CheckCircleIcon />;
      case 'active':
        return <PlayCircleOutlineIcon />;
      case 'cancelled':
        return <CancelIcon />;
      case 'scheduled':
        return <ScheduledIcon />;
      default:
        return <ScheduleIcon />;
    }
  };

  const getAttendanceColor = (attended) => {
    switch (attended?.toLowerCase()) {
      case 'present':
        return 'success';
      case 'absent':
        return 'error';
      case 'late':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatDate = (dateValue, formatter = 'dateTime') => {
    try {
      if (!dateValue) return 'Not set';
      
      let date;
      if (typeof dateValue === 'string') {
        date = new Date(dateValue);
      } else if (dateValue instanceof Date) {
        date = dateValue;
      } else {
        return 'Invalid date';
      }
      
      if (isNaN(date.getTime())) {
        console.warn('Invalid date value:', dateValue);
        return 'Invalid date';
      }
      
      return fallbackDateFormatters[formatter](date);
    } catch (error) {
      console.error('Error formatting date:', error, 'Date value:', dateValue);
      return 'Date error';
    }
  };

  const calculateDuration = (startTime, endTime) => {
    try {
      if (!startTime || !endTime) return 'N/A';
      
      const start = new Date(startTime);
      const end = new Date(endTime);
      
      if (isNaN(start.getTime()) || isNaN(end.getTime())) return 'N/A';
      
      const diffMs = end - start;
      const diffMins = Math.round(diffMs / (1000 * 60));
      
      if (diffMins < 60) {
        return `${diffMins} minutes`;
      } else {
        const hours = Math.floor(diffMins / 60);
        const mins = diffMins % 60;
        return `${hours}h ${mins}m`;
      }
    } catch (error) {
      return 'N/A';
    }
  };

  if (loading) {
    return (
      <Box>
        {/* Header Skeleton */}
        <Box display="flex" alignItems="center" mb={3}>
          <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
          <Skeleton variant="text" width={300} height={40} />
        </Box>
        
        {/* Content Skeleton */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Skeleton variant="text" width="80%" height={40} />
                <Skeleton variant="text" width="60%" height={20} />
                <Box sx={{ mt: 3 }}>
                  <Skeleton variant="rectangular" width="100%" height={200} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Skeleton variant="rectangular" width="100%" height={300} />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  }

  if (error || !sessionData) {
    return (
      <Box>
        <Box display="flex" alignItems="center" mb={3}>
          <IconButton onClick={() => navigate(-1)} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h5">Session Details</Typography>
        </Box>
        
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="h6">{error || 'Session not found'}</Typography>
          <Typography variant="body2">
            The session you're looking for doesn't exist or couldn't be loaded.
          </Typography>
        </Alert>
        
        <Box display="flex" gap={2}>
          <Button 
            variant="outlined" 
            onClick={() => navigate(-1)} 
            startIcon={<ArrowBackIcon />}
          >
            Go Back
          </Button>
          <Button 
            variant="contained" 
            onClick={fetchSessionDetails}
            startIcon={<RefreshIcon />}
          >
            Retry
          </Button>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link 
          color="inherit" 
          onClick={() => navigate('/trainer/sessions')}
          sx={{ cursor: 'pointer' }}
        >
          Sessions
        </Link>
        <Typography color="text.primary">
          Session {sessionData.Session_ID}
        </Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate(-1)} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <ScheduleIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              Session Details
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Session ID: {sessionData.Session_ID} • Student: {sessionData.Student_Name}
            </Typography>
          </Box>
        </Box>
        
        <Box display="flex" gap={1}>
          <Chip
            icon={getStatusIcon(sessionData.Status)}
            label={sessionData.Status || 'Unknown'}
            color={getStatusColor(sessionData.Status)}
            size="large"
            sx={{ fontWeight: 'bold' }}
          />
        </Box>
      </Box>

      
      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Session Overview */}
        <Grid item xs={12} md={8}>
          <Card elevation={3}>
            <CardHeader
              avatar={
                <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                  <SchoolIcon />
                </Avatar>
              }
              title={
                <Typography variant="h5" fontWeight="bold">
                  Session Information
                </Typography>
              }
              subheader={`Batch ID: ${sessionData.Batch_ID} • Student ID: ${sessionData.Student_ID}`}
            />
            <CardContent>
              <Grid container spacing={4}>
                {/* Student Information */}
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="flex-start" mb={3}>
                    <PersonIcon sx={{ mr: 2, mt: 0.5, color: 'primary.main' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Student Details
                      </Typography>
                      <Typography variant="h6" fontWeight="bold">
                        {sessionData.Student_Name || 'No name provided'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Student ID: {sessionData.Student_ID}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>

                {/* Batch Information */}
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="flex-start" mb={3}>
                    <BusinessIcon sx={{ mr: 2, mt: 0.5, color: 'secondary.main' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Batch Information
                      </Typography>
                      <Typography variant="h6" fontWeight="bold">
                        Batch {sessionData.Batch_ID}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Training Group
                      </Typography>
                    </Box>
                  </Box>
                </Grid>

                {/* Session Timing */}
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="flex-start" mb={3}>
                    <AccessTimeIcon sx={{ mr: 2, mt: 0.5, color: 'success.main' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Session Timing
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        Start: {formatDate(sessionData.Start_DateTime)}
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        End: {formatDate(sessionData.End_DateTime)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Duration: {calculateDuration(sessionData.Start_DateTime, sessionData.End_DateTime)}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>

                {/* Session Link */}
                <Grid item xs={12} sm={6}>
                  <Box display="flex" alignItems="flex-start" mb={3}>
                    <LinkIcon sx={{ mr: 2, mt: 0.5, color: 'info.main' }} />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        Session Access
                      </Typography>
                      {sessionData.Session_Link ? (
                        <Button
                          variant="outlined"
                          startIcon={<PlayCircleOutlineIcon />}
                          onClick={() => window.open(sessionData.Session_Link, '_blank')}
                          sx={{ mt: 1 }}
                        >
                          Open Session Link
                        </Button>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No session link available
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Session Statistics */}
        <Grid item xs={12} md={4}>
          <Card elevation={3}>
            <CardHeader
              title={
                <Typography variant="h6" fontWeight="bold">
                  Session Statistics
                </Typography>
              }
              avatar={
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <AssessmentIcon />
                </Avatar>
              }
            />
            <CardContent>
              <Grid container spacing={2}>
                {/* Attendance Status */}
                <Grid item xs={12}>
                  <Paper 
                    sx={{ 
                      p: 3, 
                      textAlign: 'center',
                      bgcolor: getAttendanceColor(sessionData.Attended) === 'success' ? 'success.light' : 
                             getAttendanceColor(sessionData.Attended) === 'error' ? 'error.light' : 'warning.light',
                      color: getAttendanceColor(sessionData.Attended) === 'success' ? 'success.contrastText' : 
                             getAttendanceColor(sessionData.Attended) === 'error' ? 'error.contrastText' : 'warning.contrastText'
                    }}
                  >
                    <Badge
                      badgeContent={getAttendanceColor(sessionData.Attended) === 'success' ? '✓' : '✗'}
                      color={getAttendanceColor(sessionData.Attended)}
                    >
                      <GroupIcon sx={{ fontSize: 40, mb: 1 }} />
                    </Badge>
                    <Typography variant="h4" fontWeight="bold">
                      {sessionData.Attended || 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      Attendance Status
                    </Typography>
                  </Paper>
                </Grid>

                {/* Attendance Percentage */}
                <Grid item xs={12}>
                  <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                    <TimelineIcon sx={{ fontSize: 40, mb: 1 }} />
                    <Typography variant="h4" fontWeight="bold">
                      {sessionData.Percentage ? `${sessionData.Percentage}%` : 'N/A'}
                    </Typography>
                    <Typography variant="body2">
                      Completion Rate
                    </Typography>
                  </Paper>
                </Grid>

                {/* Session ID */}
                <Grid item xs={6}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="info.main" fontWeight="bold">
                      {sessionData.Session_ID}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Session ID
                    </Typography>
                  </Paper>
                </Grid>

                {/* Batch ID */}
                <Grid item xs={6}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="secondary.main" fontWeight="bold">
                      {sessionData.Batch_ID}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Batch ID
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card sx={{ mt: 2 }} elevation={2}>
            <CardHeader
              title={
                <Typography variant="h6" fontWeight="bold">
                  Quick Actions
                </Typography>
              }
            />
            <CardContent>
              <List dense>
                <ListItem button onClick={() => navigate(`/trainer/sessions/edit/${sessionData.Session_ID}`)}>
                  <ListItemIcon>
                    <ScheduleIcon color="primary" />
                  </ListItemIcon>
                  <ListItemText primary="Edit Session" secondary="Modify session details" />
                </ListItem>
                
                <Divider />
                
                <ListItem button onClick={() => navigate('/trainer/sessions')}>
                  <ListItemIcon>
                    <GroupIcon color="secondary" />
                  </ListItemIcon>
                  <ListItemText primary="View All Sessions" secondary="Go back to session list" />
                </ListItem>

                <Divider />

                <ListItem button onClick={fetchSessionDetails}>
                  <ListItemIcon>
                    <RefreshIcon color="info" />
                  </ListItemIcon>
                  <ListItemText primary="Refresh Data" secondary="Reload session information" />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Session Details Table */}
      <Card sx={{ mt: 3 }} elevation={3}>
        <CardHeader
          title={
            <Typography variant="h6" fontWeight="bold">
              Complete Session Record
            </Typography>
          }
          subheader="All available session information"
        />
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Field</strong></TableCell>
                  <TableCell><strong>Value</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Session ID</TableCell>
                  <TableCell>{sessionData.Session_ID || 'N/A'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Batch ID</TableCell>
                  <TableCell>{sessionData.Batch_ID || 'N/A'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Student ID</TableCell>
                  <TableCell>{sessionData.Student_ID || 'N/A'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Student Name</TableCell>
                  <TableCell>{sessionData.Student_Name || 'No name provided'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Session Link</TableCell>
                  <TableCell>
                    {sessionData.Session_Link ? (
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<LinkIcon />}
                        onClick={() => window.open(sessionData.Session_Link, '_blank')}
                      >
                        Open Link
                      </Button>
                    ) : (
                      'No link available'
                    )}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>
                    <Chip
                      icon={getStatusIcon(sessionData.Status)}
                      label={sessionData.Status || 'Unknown'}
                      color={getStatusColor(sessionData.Status)}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Start Date & Time</TableCell>
                  <TableCell>{formatDate(sessionData.Start_DateTime)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>End Date & Time</TableCell>
                  <TableCell>{formatDate(sessionData.End_DateTime)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Duration</TableCell>
                  <TableCell>{calculateDuration(sessionData.Start_DateTime, sessionData.End_DateTime)}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Attendance Status</TableCell>
                  <TableCell>
                    <Chip
                      label={sessionData.Attended || 'N/A'}
                      color={getAttendanceColor(sessionData.Attended)}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Completion Percentage</TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {sessionData.Percentage ? `${sessionData.Percentage}%` : 'N/A'}
                    </Typography>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ViewSession;