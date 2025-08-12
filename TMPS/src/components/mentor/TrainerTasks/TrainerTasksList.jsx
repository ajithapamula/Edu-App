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
  IconButton,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Tooltip,
  Skeleton,
  CircularProgress,
  Slide,
  Snackbar,
  Grid
} from '@mui/material';
import {
  Visibility,
  Edit,
  Search,
  Assignment,
  Group,
  Save,
  Cancel,
  Close,
  Refresh
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { trainerTasksAPI } from '../../../services/API/trainertasks'

// Shimmer Loading Component
const TrainerTasksShimmer = ({ rows = 6 }) => {
  const shimmerRows = Array.from({ length: rows }, (_, index) => index);

  return (
    <Box>
      {/* Header Shimmer */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Skeleton variant="text" width={200} height={48} />
      </Box>

      {/* Search Shimmer */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
          <Skeleton variant="rectangular" width={300} height={40} sx={{ borderRadius: 1 }} />
        </Box>
      </Paper>

      {/* Summary Cards Shimmer */}
      <Box display="flex" gap={2} mb={3}>
        <Paper sx={{ p: 2, flex: 1, textAlign: 'center' }}>
          <Skeleton variant="text" width={40} height={32} sx={{ mx: 'auto', mb: 1 }} />
          <Skeleton variant="text" width={80} height={20} sx={{ mx: 'auto' }} />
        </Paper>
      </Box>

      {/* Table Shimmer */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><Skeleton variant="text" width={60} /></TableCell>
              <TableCell><Skeleton variant="text" width={80} /></TableCell>
              <TableCell><Skeleton variant="text" width={100} /></TableCell>
              <TableCell><Skeleton variant="text" width={200} /></TableCell>
              <TableCell><Skeleton variant="text" width={100} /></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {shimmerRows.map((index) => (
              <TableRow key={index}>
                <TableCell><Skeleton variant="text" width={40} /></TableCell>
                <TableCell><Skeleton variant="text" width={60} /></TableCell>
                <TableCell><Skeleton variant="text" width={80} /></TableCell>
                <TableCell><Skeleton variant="text" width={250} /></TableCell>
                <TableCell>
                  <Box display="flex" gap={1} justifyContent="center">
                    {Array.from({ length: 2 }).map((_, btnIndex) => (
                      <Skeleton key={btnIndex} variant="circular" width={32} height={32} />
                    ))}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

// Transition component for modal
const Transition = React.forwardRef(function Transition(props, ref) {
  return <Slide direction="up" ref={ref} {...props} />;
});

const MentorTrainerTasksList = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Edit Modal States
  const [editDialog, setEditDialog] = useState({ open: false, task: null });
  const [editForm, setEditForm] = useState({
    Task_Box: '',
    Batch_ID: '',
    Session_ID: ''
  });
  const [editLoading, setEditLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Format task data to handle the actual API response structure
  const formatTaskData = (task) => {
    return {
      ID: task.ID || task.id,
      Batch_ID: task.Batch_ID || task.batch_id,
      Session_ID: task.Session_ID || task.session_id,
      Task_Box: task.Task_Box || task.task_box || ''
    };
  };

  // Fetch tasks from API
  const fetchTasks = async () => {
    try {
      setError(null);
      const response = await trainerTasksAPI.getAllTasks();
      
      console.log('API Response:', response);
      
      // Handle different response structures
      let tasksData = [];
      if (response?.data) {
        tasksData = Array.isArray(response.data) ? response.data : [response.data];
      } else if (Array.isArray(response)) {
        tasksData = response;
      } else if (response?.tasks) {
        tasksData = Array.isArray(response.tasks) ? response.tasks : [response.tasks];
      }
      
      // Format tasks data
      const formattedTasks = tasksData.map(formatTaskData);
      setTasks(formattedTasks);
      
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setError(error.message || 'Failed to fetch tasks. Please try again.');
      
      setSnackbar({
        open: true,
        message: error.message || 'Failed to fetch tasks',
        severity: 'error'
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchTasks();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchTasks();
  };

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleView = (taskId) => {
    console.log('🔍 handleView called with taskId:', taskId);
    console.log('🔍 taskId type:', typeof taskId);
    console.log('🔍 taskId value:', JSON.stringify(taskId));
    
    if (!taskId || taskId === 'undefined' || taskId === 'null') {
      console.error('❌ Invalid taskId passed to handleView:', taskId);
      alert('Invalid task ID. Please check the console for details.');
      return;
    }
    
    const navigationPath = `/mentor/tasks/view/${taskId}`;
    console.log('🔍 Navigating to:', navigationPath);
    
    navigate(navigationPath);
  };

  const handleEdit = (task) => {
    setEditForm({
      Task_Box: task.Task_Box || '',
      Batch_ID: task.Batch_ID || '',
      Session_ID: task.Session_ID || ''
    });
    setEditDialog({ open: true, task });
  };

  const handleEditClose = () => {
    setEditDialog({ open: false, task: null });
    setEditForm({
      Task_Box: '',
      Batch_ID: '',
      Session_ID: ''
    });
  };

  const handleEditFormChange = (field) => (event) => {
    setEditForm(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleEditSubmit = async () => {
    try {
      setEditLoading(true);
      
      // Validate required fields
      if (!editForm.Batch_ID || !editForm.Session_ID) {
        setSnackbar({
          open: true,
          message: 'Batch ID and Session ID are required fields',
          severity: 'error'
        });
        return;
      }
      
      // Prepare data for API - include all required fields
      const updateData = {
        Task_Box: editForm.Task_Box,
        Batch_ID: parseInt(editForm.Batch_ID), // Ensure it's a number
        Session_ID: parseInt(editForm.Session_ID) // Ensure it's a number
      };
      
      console.log('Sending update data:', updateData);
      
      const response = await trainerTasksAPI.updateTask(editDialog.task.ID, updateData);
      console.log('Update response:', response);
      // Update local state with the new data
      const updatedTasks = tasks.map(task => 
        task.ID === editDialog.task.ID ? {
          ...task,
          Task_Box: updateData.Task_Box,
          Batch_ID: updateData.Batch_ID,
          Session_ID: updateData.Session_ID
        } : task
      );
      setTasks(updatedTasks);
      
      handleEditClose();
      setSnackbar({
        open: true,
        message: 'Task updated successfully!',
        severity: 'success'
      });
      
    } catch (error) {
      console.error('Error updating task:', error);
      setSnackbar({
        open: true,
        message: error.message || 'Failed to update task',
        severity: 'error'
      });
    } finally {
      setEditLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Filter tasks based on search term
  const filteredTasks = tasks.filter(task => {
    const taskBox = (task.Task_Box || '').toLowerCase();
    const searchLower = searchTerm.toLowerCase();
    return taskBox.includes(searchLower) || 
           task.ID.toString().includes(searchLower) ||
           task.Batch_ID.toString().includes(searchLower) ||
           task.Session_ID.toString().includes(searchLower);
  });

  if (loading) {
    return <TrainerTasksShimmer rows={8} />;
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <Assignment sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Trainer Tasks
          </Typography>
          <IconButton 
            onClick={handleRefresh} 
            disabled={refreshing}
            sx={{ ml: 1 }}
            title="Refresh tasks"
          >
            <Refresh sx={{ 
              animation: refreshing ? 'spin 1s linear infinite' : 'none',
              '@keyframes spin': {
                '0%': { transform: 'rotate(0deg)' },
                '100%': { transform: 'rotate(360deg)' }
              }
            }} />
          </IconButton>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }} 
          onClose={() => setError(null)}
          action={
            <Button color="inherit" size="small" onClick={handleRefresh}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      )}

      {/* Search Control */}
      <Paper sx={{ p: 2, mb: 3, borderRadius: 2, boxShadow: 2 }}>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            placeholder="Search tasks by ID, Batch ID, Session ID, or content..."
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={handleSearch}
            InputProps={{
              startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            sx={{ flexGrow: 1, maxWidth: 500 }}
          />
        </Box>
      </Paper>

      {/* Tasks Summary */}
      <Box display="flex" gap={2} mb={3}>
        <Paper sx={{ p: 2, flex: 1, textAlign: 'center', borderRadius: 2 }}>
          <Typography variant="h6" color="primary">
            {tasks.length}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total Tasks
          </Typography>
        </Paper>
      </Box>

      {/* Tasks Table */}
      <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Task ID</strong></TableCell>
              <TableCell><strong>Batch ID</strong></TableCell>
              <TableCell><strong>Session ID</strong></TableCell>
              <TableCell><strong>Task Content</strong></TableCell>
              <TableCell align="center"><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredTasks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Alert severity="info" sx={{ m: 2 }}>
                    {tasks.length === 0 
                      ? "No tasks found."
                      : "No tasks match your search criteria."
                    }
                  </Alert>
                </TableCell>
              </TableRow>
            ) : (
              filteredTasks.map((task) => (
                <TableRow key={task.ID} hover>
                  <TableCell>
                    <Chip 
                      label={task.ID} 
                      color="primary" 
                      variant="outlined"
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Group fontSize="small" color="action" />
                      <Typography variant="body2">
                        {task.Batch_ID}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {task.Session_ID}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2" sx={{ 
                        wordBreak: 'break-word',
                        maxWidth: 400,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical'
                      }}>
                        {task.Task_Box || 'No content'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                  <Box display="flex" gap={1} justifyContent="center">
                      <Tooltip title="View Task">
                        <IconButton 
                          size="small" 
                          color="info"
                          onClick={() => handleView(task.ID)}
                        >
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Task">
                        <IconButton 
                          size="small" 
                          color="warning"
                          onClick={() => handleEdit(task)}
                        >
                          <Edit />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit Modal */}
      <Dialog 
        open={editDialog.open} 
        onClose={handleEditClose}
        TransitionComponent={Transition}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            boxShadow: '0 24px 38px 3px rgba(0,0,0,0.14)',
          }
        }}
      >
        <DialogTitle
          sx={{
            background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
            color: 'white',
            position: 'relative'
          }}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={2}>
              <Assignment />
              <Typography variant="h6">
                Edit Task (ID: {editDialog.task?.ID})
              </Typography>
            </Box>
            <IconButton 
              onClick={handleEditClose} 
              sx={{ color: 'white' }}
              disabled={editLoading}
            >
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers sx={{ p: 3 }}>
          <Box display="flex" flexDirection="column" gap={3}>
            {/* Task IDs Display */}
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Current Task:</strong> ID {editDialog.task?.ID} | 
                Original Batch: {editDialog.task?.Batch_ID} | 
                Original Session: {editDialog.task?.Session_ID}
              </Typography>
            </Alert>
            
            {/* Form Fields */}
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Batch ID *"
                  type="number"
                  value={editForm.Batch_ID}
                  onChange={handleEditFormChange('Batch_ID')}
                  variant="outlined"
                  disabled={editLoading}
                  required
                  helperText="Enter the Batch ID for this task"
                  error={!editForm.Batch_ID}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Session ID *"
                  type="number"
                  value={editForm.Session_ID}
                  onChange={handleEditFormChange('Session_ID')}
                  variant="outlined"
                  disabled={editLoading}
                  required
                  helperText="Enter the Session ID for this task"
                  error={!editForm.Session_ID}
                />
              </Grid>
            </Grid>
            
            <TextField
              fullWidth
              label="Task Content"
              value={editForm.Task_Box}
              onChange={handleEditFormChange('Task_Box')}
              variant="outlined"
              multiline
              rows={6}
              disabled={editLoading}
              helperText="Enter the task questions or content"
              placeholder="What is python?, what are array?"
            />
          </Box>
        </DialogContent>
        
        <DialogActions sx={{ p: 2, backgroundColor: '#f8f9fa' }}>
          <Button 
            onClick={handleEditClose} 
            variant="outlined"
            disabled={editLoading}
            startIcon={<Cancel />}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleEditSubmit} 
            variant="contained"
            disabled={editLoading || !editForm.Batch_ID || !editForm.Session_ID}
            startIcon={editLoading ? <CircularProgress size={20} color="inherit" /> : <Save />}
            sx={{
              background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #1976D2 30%, #2196F3 90%)'
              }
            }}
          >
            {editLoading ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity} 
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MentorTrainerTasksList;