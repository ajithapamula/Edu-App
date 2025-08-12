import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Grid,
  Paper,
  Divider,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  CircularProgress,
  Skeleton
} from '@mui/material';
import {
  Assignment,
  Schedule,
  Person,
  CalendarToday,
  CheckCircle,
  Warning,
  Info,
  Download,
  ArrowBack,
  QuestionAnswer,
  Category
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { trainerTasksAPI } from '../../../services/API/trainertasks'; // Adjust path as needed

// Simplified Shimmer Loading Component for your API structure
const ViewTrainerTaskShimmer = () => {
  return (
    <Box>
      {/* Header Shimmer */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Skeleton variant="rectangular" width={120} height={36} sx={{ mb: 2, borderRadius: 1 }} />
          <Skeleton variant="text" width="60%" height={48} sx={{ mb: 1 }} />
          <Box display="flex" gap={1} flexWrap="wrap">
            <Skeleton variant="rectangular" width={90} height={24} sx={{ borderRadius: 12 }} />
          </Box>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Content Shimmer */}
        <Grid item xs={12} md={8}>
          {/* Task Details Card Shimmer */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Skeleton variant="text" width={150} height={32} sx={{ mb: 2 }} />
              <Skeleton variant="text" width="100%" height={20} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="95%" height={20} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="80%" height={20} sx={{ mb: 2 }} />
              
              <Divider sx={{ my: 2 }} />
              
              <Grid container spacing={2}>
                {Array.from({ length: 3 }).map((_, index) => (
                  <Grid item xs={6} md={4} key={index}>
                    <Box display="flex" alignItems="center" mb={1}>
                      <Skeleton variant="circular" width={20} height={20} sx={{ mr: 1 }} />
                      <Skeleton variant="text" width={80} height={16} />
                    </Box>
                    <Skeleton variant="text" width={90} height={20} />
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>

          {/* Task Questions Shimmer */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Skeleton variant="text" width={120} height={32} sx={{ mb: 2 }} />
              <Box sx={{ pl: 2 }}>
                <Skeleton variant="text" width="90%" height={20} sx={{ mb: 1 }} />
                <Skeleton variant="text" width="85%" height={20} sx={{ mb: 1 }} />
                <Skeleton variant="text" width="75%" height={20} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar Shimmer */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Skeleton variant="text" width={100} height={32} sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Skeleton variant="text" width={60} height={16} sx={{ mb: 1 }} />
                  <Skeleton variant="text" width={40} height={20} />
                </Grid>
                <Grid item xs={6}>
                  <Skeleton variant="text" width={80} height={16} sx={{ mb: 1 }} />
                  <Skeleton variant="text" width={50} height={20} />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Loading message */}
      <Box display="flex" justifyContent="center" alignItems="center" mt={3}>
        <CircularProgress size={20} sx={{ mr: 1 }} />
        <Typography variant="body2" color="text.secondary">
          Loading task details...
        </Typography>
      </Box>
    </Box>
  );
};

const MentorViewTrainerTask = () => {
  // FIXED: Changed from taskId to id to match route parameter
  const { id } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Debug logging
  console.log('ViewTrainerTask - URL params:', useParams());
  console.log('ViewTrainerTask - Task ID:', id);

  useEffect(() => {
    // Only fetch if we have a valid ID
    if (id && id !== 'undefined') {
      fetchTask();
    } else {
      setError('Invalid task ID provided');
      setLoading(false);
    }
  }, [id]);

  const fetchTask = async () => {
    try {
      setLoading(true);
      setError('');
      
      console.log('Fetching task with ID:', id);
      
      // Validate ID before making API call
      if (!id || id === 'undefined' || id === 'null') {
        throw new Error('Invalid task ID');
      }
      
      // Call your actual API
      const response = await trainerTasksAPI.getTaskById(id);
      console.log('API Response:', response);
      
      // Check if response contains data
      if (!response) {
        throw new Error('No data received from server');
      }
      
      // Transform the API response to match your component's needs
      const transformedTask = transformApiResponse(response);
      console.log('Transformed task:', transformedTask);
      setTask(transformedTask);
      
    } catch (err) {
      console.error('Full error details:', err);
      setError('Failed to fetch task details: ' + (err.message || err.toString()));
    } finally {
      setLoading(false);
    }
  };

  // Transform your API response to match the component structure
  const transformApiResponse = (apiData) => {
    if (!apiData) return null;

    // Handle both single object and array responses
    const taskData = Array.isArray(apiData) ? apiData[0] : apiData;
    
    if (!taskData) return null;

    // Parse the Task_Box to extract individual questions
    const questions = taskData.Task_Box ? 
      taskData.Task_Box.split('?').map(q => q.trim()).filter(q => q).map(q => q.endsWith('?') ? q : q + '?') : 
      [];

    return {
      id: taskData.ID,
      batchId: taskData.Batch_ID,
      sessionId: taskData.Session_ID,
      title: `Task #${taskData.ID} - Session ${taskData.Session_ID}`,
      description: `Training task for Batch ${taskData.Batch_ID} containing ${questions.length} question${questions.length !== 1 ? 's' : ''}`,
      questions: questions,
      taskBox: taskData.Task_Box,
      // Add default values for fields that might not exist in your API
      // category: 'Training',
      assignedDate: new Date().toISOString(),
      // Store original data for reference
      originalData: taskData
    };
  };

  // Show shimmer while loading
  if (loading) {
    return <ViewTrainerTaskShimmer />;
  }

  if (error) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/mentor/tasks')}
          sx={{ mb: 2 }}
        >
          Back to Tasks
        </Button>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button
          variant="contained"
          onClick={() => window.location.reload()}
          sx={{ mt: 2 }}
        >
          Retry
        </Button>
      </Box>
    );
  }

  if (!task) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/mentor/tasks')}
          sx={{ mb: 2 }}
        >
          Back to Tasks
        </Button>
        <Alert severity="warning" sx={{ mb: 3 }}>
          Task not found
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/mentor/tasks')}
            sx={{ 
              mb: 2,
              bgcolor: 'primary.main',
              color: 'white',
              '&:hover': { bgcolor: 'primary.dark' }
            }}
          >
            Back to Tasks
          </Button>
          <Typography variant="h4" gutterBottom>
            {task.title}
          </Typography>
          
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Task Details */}
        <Grid item xs={12} md={8}>
          {/* Main Task Information */}
          <Card sx={{ mb: 3, borderRadius: 2, boxShadow: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Task Description
              </Typography>
              <Typography variant="body1" paragraph>
                {task.description}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6} md={4}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Assignment sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="body2" color="textSecondary">
                      Task ID
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    #{task.id}
                  </Typography>
                </Grid>
                
                <Grid item xs={6} md={4}>
                  <Box display="flex" alignItems="center" mb={1}>
                   
                    <Typography variant="body2" color="textSecondary">
                      Batch ID
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    {task.batchId}
                  </Typography>
                </Grid>
                
                <Grid item xs={6} md={4}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Schedule sx={{ mr: 1, fontSize: 20 }} />
                    <Typography variant="body2" color="textSecondary">
                      Session ID
                    </Typography>
                  </Box>
                  <Typography variant="body1">
                    {task.sessionId}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Task Questions */}
          <Card sx={{ mb: 3, borderRadius: 2, boxShadow: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <QuestionAnswer sx={{ mr: 1 }} />
                Task Questions ({task.questions.length})
              </Typography>
              
              {task.questions.length > 0 ? (
                <List>
                  {task.questions.map((question, index) => (
                    <ListItem key={index} sx={{ pl: 0 }}>
                      <ListItemIcon>
                        <Avatar
                          sx={{
                            width: 28,
                            height: 28,
                            bgcolor: 'primary.main',
                            fontSize: '0.875rem'
                          }}
                        >
                          {index + 1}
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText 
                        primary={question}
                        primaryTypographyProps={{
                          variant: 'body1',
                          sx: { fontWeight: 500 }
                        }}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="textSecondary" sx={{ pl: 2 }}>
                  No questions available for this task.
                </Typography>
              )}
            </CardContent>
          </Card>

          
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Task Summary */}
          <Card sx={{ borderRadius: 2, boxShadow: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Task Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Total Questions
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {task.questions.length}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  
                 
                </Grid>
              </Grid>
              
              <Divider sx={{ my: 2 }} />
              
              
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <span>Task ID:</span>
                  <strong>#{task.id}</strong>
                </Typography>
                <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <span>Batch ID:</span>
                  <strong>{task.batchId}</strong>
                </Typography>
                <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <span>Session ID:</span>
                  <strong>{task.sessionId}</strong>
                </Typography>
                <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Questions:</span>
                  <strong>{task.questions.length}</strong>
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
export default MentorViewTrainerTask;