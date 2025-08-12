import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Skeleton,
  Snackbar,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText
} from '@mui/material';
import {
  Visibility,
  Edit,
  Add,
  Refresh,
  Delete
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

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
  }
};

// Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box p={3}>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="h6">Something went wrong</Typography>
            <Typography variant="body2">
              {this.state.error?.message || 'An unexpected error occurred'}
            </Typography>
          </Alert>
          <Button 
            variant="contained" 
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try Again
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Shimmer Component for loading table rows
const ShimmerTableRow = () => (
  <TableRow>
    <TableCell><Skeleton variant="text" width="60%" /></TableCell>
    <TableCell><Skeleton variant="text" width="60%" /></TableCell>
    <TableCell><Skeleton variant="text" width="60%" /></TableCell>
    <TableCell><Skeleton variant="text" width="80%" /></TableCell>
    <TableCell><Skeleton variant="text" width="70%" /></TableCell>
    <TableCell><Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 3 }} /></TableCell>
    <TableCell><Skeleton variant="text" width="90%" /></TableCell>
    <TableCell><Skeleton variant="text" width="90%" /></TableCell>
    <TableCell><Skeleton variant="text" width="60%" /></TableCell>
    <TableCell><Skeleton variant="text" width="60%" /></TableCell>
    <TableCell><Skeleton variant="rectangular" width={70} height={32} sx={{ borderRadius: 1 }} /></TableCell>
  </TableRow>
);

const SessionsList = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [deleteDialog, setDeleteDialog] = useState({ open: false, session: null });
  const [deleteLoading, setDeleteLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await sessionsAPI.getAll();
      
      // Debug: Log the actual response structure
      console.log('Raw API Response:', response);
      
      setSessions(response);
      
    } catch (err) {
      setError('Failed to fetch sessions');
      console.error('Error fetching sessions:', err);
      setSnackbar({
        open: true,
        message: 'Failed to fetch sessions: ' + err.message,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleViewSession = (sessionId) => {
    navigate(`/trainer/sessions/view/${sessionId}`);
  };

  const handleEditSession = (session) => {
    navigate(`/trainer/sessions/edit/${session.Session_ID}`);
  };

  const handleDeleteClick = (session) => {
    setDeleteDialog({
      open: true,
      session: session
    });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteDialog.session) return;

    try {
      setDeleteLoading(true);
      
      await sessionsAPI.remove(deleteDialog.session.Session_ID);
      
      // Remove the session from the local state
      setSessions(prevSessions => 
        prevSessions.filter(session => 
          session.Session_ID !== deleteDialog.session.Session_ID
        )
      );
      
      setSnackbar({
        open: true,
        message: `Session "${deleteDialog.session.Session_ID}" deleted successfully`,
        severity: 'success'
      });
      
      // Close the dialog
      setDeleteDialog({ open: false, session: null });
      
    } catch (err) {
      console.error('Error deleting session:', err);
      setSnackbar({
        open: true,
        message: 'Failed to delete session: ' + err.message,
        severity: 'error'
      });
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, session: null });
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'active':
        return 'primary';
      case 'cancelled':
        return 'error';
      case 'in-progress':
        return 'warning';
      default:
        return 'default';
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

  // Safe date formatting function
  const formatDate = (dateValue, formatter = 'dateTime') => {
    try {
      if (!dateValue) return 'Not set';
      
      // Handle different date formats
      let date;
      if (typeof dateValue === 'string') {
        date = new Date(dateValue);
      } else if (dateValue instanceof Date) {
        date = dateValue;
      } else {
        return 'Invalid date';
      }
      
      // Check if date is valid
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

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (error && !loading) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={fetchSessions} startIcon={<Refresh />}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <ErrorBoundary>
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" gutterBottom>
            Session Attendance
          </Typography>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchSessions}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => navigate('/trainer/sessions/create')}
            >
              Create Session
            </Button>
          </Box>
        </Box>

        {/* Sessions Table */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Session Records ({sessions.length} total)
            </Typography>
            
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Session ID</TableCell>
                    <TableCell>Batch ID</TableCell>
                    <TableCell>Student ID</TableCell>
                    <TableCell>Student Name</TableCell>
                    <TableCell>Session Link</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Start Date Time</TableCell>
                    <TableCell>End Date Time</TableCell>
                    <TableCell>Attended</TableCell>
                    <TableCell>Percentage</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loading ? (
                    // Shimmer effect for table rows
                    Array.from({ length: 5 }).map((_, index) => (
                      <ShimmerTableRow key={index} />
                    ))
                  ) : sessions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={11} align="center">
                        <Typography variant="body1" color="textSecondary">
                          No session records found
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    sessions.map((session, index) => (
                      <TableRow key={session.Session_ID || index}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {session.Session_ID || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {session.Batch_ID || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {session.Student_ID || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {session.Student_Name || 'No name'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {session.Session_Link ? (
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => window.open(session.Session_Link, '_blank')}
                              sx={{ fontSize: '0.75rem' }}
                            >
                              Open Link
                            </Button>
                          ) : (
                            <Typography variant="body2" color="textSecondary">
                              No link
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={session.Status || 'Unknown'}
                            color={getStatusColor(session.Status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(session.Start_DateTime)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDate(session.End_DateTime)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={session.Attended || 'N/A'}
                            color={getAttendanceColor(session.Attended)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {session.Percentage ? `${session.Percentage}%` : 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={1} alignItems="center">
                            <Visibility 
                              sx={{ 
                                cursor: 'pointer', 
                                color: 'text.secondary', 
                                '&:hover': { color: 'primary.main' } 
                              }}
                              onClick={() => handleViewSession(session.Session_ID)}
                              titleAccess="View Session"
                            />
                            <Edit 
                              sx={{ 
                                cursor: 'pointer', 
                                color: 'text.secondary', 
                                '&:hover': { color: 'secondary.main' } 
                              }}
                              onClick={() => handleEditSession(session)}
                              titleAccess="Edit Session"
                            />
                            <Delete 
                              sx={{ 
                                cursor: 'pointer', 
                                color: 'text.secondary', 
                                '&:hover': { color: 'error.main' } 
                              }}
                              onClick={() => handleDeleteClick(session)}
                              titleAccess="Delete Session"
                            />
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

        {/* Delete Confirmation Dialog */}
        <Dialog
          open={deleteDialog.open}
          onClose={handleDeleteCancel}
          aria-labelledby="delete-dialog-title"
          aria-describedby="delete-dialog-description"
        >
          <DialogTitle id="delete-dialog-title">
            Confirm Delete
          </DialogTitle>
          <DialogContent>
            <DialogContentText id="delete-dialog-description">
              Are you sure you want to delete this session record?
              <br />
              <strong>Session ID:</strong> {deleteDialog.session?.Session_ID}
              <br />
              <strong>Student:</strong> {deleteDialog.session?.Student_Name || 'N/A'}
              <br />
              <br />
              This action cannot be undone.
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button 
              onClick={handleDeleteCancel} 
              disabled={deleteLoading}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleDeleteConfirm} 
              color="error" 
              variant="contained"
              disabled={deleteLoading}
              startIcon={deleteLoading ? <CircularProgress size={16} /> : <Delete />}
            >
              {deleteLoading ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </ErrorBoundary>
  );
};

export default SessionsList;