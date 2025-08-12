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

const StudentTrainerTasksList = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Edit Modal States
  
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
    
    const navigationPath = `/student/tasks/view/${taskId}`;
    console.log('🔍 Navigating to:', navigationPath);
    
    navigate(navigationPath);
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
                      
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Edit Modal */}
   
      {/* Snackbar for notifications */}
    
    </Box>
  );
};

export default StudentTrainerTasksList;