import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  Grid,
  Card,
  CardContent,
  Divider,
  Chip,
  CircularProgress,
  Snackbar
} from '@mui/material';
import {
  Save,
  Cancel,
  Assignment,
  Group,
  ArrowBack
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { trainerTasksAPI } from '../../../services/API/trainertasks'; // Adjust path as needed

const AddTrainerTask = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    Task_Box: '',
    Batch_ID: '',
    Session_ID: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.Batch_ID.trim()) {
      newErrors.Batch_ID = 'Batch ID is required';
    } else if (isNaN(formData.Batch_ID) || parseInt(formData.Batch_ID) <= 0) {
      newErrors.Batch_ID = 'Batch ID must be a valid positive number';
    }

    if (!formData.Session_ID.trim()) {
      newErrors.Session_ID = 'Session ID is required';
    } else if (isNaN(formData.Session_ID) || parseInt(formData.Session_ID) <= 0) {
      newErrors.Session_ID = 'Session ID must be a valid positive number';
    }

    if (!formData.Task_Box.trim()) {
      newErrors.Task_Box = 'Task content is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      // Prepare data for API
      const taskData = {
        Task_Box: formData.Task_Box.trim(),
        Batch_ID: parseInt(formData.Batch_ID),
        Session_ID: parseInt(formData.Session_ID)
      };

      console.log('Sending task data:', taskData);
      
      const response = await trainerTasksAPI.addTask(taskData);
      
      console.log('Task created successfully:', response);
      
      setSnackbar({
        open: true,
        message: `Task created successfully! Task ID: ${response.Task_ID || 'Unknown'}`,
        severity: 'success'
      });

      // Navigate back to tasks list after a short delay
      setTimeout(() => {
        navigate('/trainer/tasks');
      }, 2000);

    } catch (error) {
      console.error('Error creating task:', error);
      setSnackbar({
        open: true,
        message: error.message || 'Failed to create task. Please try again.',
        severity: 'error'
      });
      setErrors({ submit: error.message || 'Failed to create task. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/trainer/tasks');
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Parse questions from Task_Box for preview
  const parseQuestions = (taskBox) => {
    if (!taskBox.trim()) return [];
    return taskBox.split('?').map(q => q.trim()).filter(q => q).map(q => q.endsWith('?') ? q : q + '?');
  };

  const questions = parseQuestions(formData.Task_Box);

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Button
          startIcon={<ArrowBack />}
          onClick={handleCancel}
          sx={{ 
            bgcolor: 'primary.main',
            color: 'white',
            '&:hover': { bgcolor: 'primary.dark' }
          }}
        >
          Back to Tasks
        </Button>
        <Assignment sx={{ fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          Create New Trainer Task
        </Typography>
      </Box>

      <Paper sx={{ p: 3, borderRadius: 2, boxShadow: 2 }}>
        {errors.submit && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {errors.submit}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Basic Information */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Assignment />
                Task Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            {/* Required Fields Info */}
            <Grid item xs={12}>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Required Information:</strong> All fields are required to create a trainer task. 
                  Batch ID and Session ID must be valid existing IDs in the system.
                </Typography>
              </Alert>
            </Grid>

            {/* Form Fields */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Batch ID *"
                name="Batch_ID"
                type="number"
                value={formData.Batch_ID}
                onChange={handleInputChange}
                error={!!errors.Batch_ID}
                helperText={errors.Batch_ID || 'Enter a valid Batch ID from the system'}
                required
                disabled={loading}
                inputProps={{ min: 1 }}
                placeholder="e.g., 1"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Session ID *"
                name="Session_ID"
                type="number"
                value={formData.Session_ID}
                onChange={handleInputChange}
                error={!!errors.Session_ID}
                helperText={errors.Session_ID || 'Enter a valid Session ID from the system'}
                required
                disabled={loading}
                inputProps={{ min: 1 }}
                placeholder="e.g., 1"
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Task Content (Task Box) *"
                name="Task_Box"
                value={formData.Task_Box}
                onChange={handleInputChange}
                error={!!errors.Task_Box}
                helperText={errors.Task_Box || 'Enter the task questions or content. Separate questions with question marks.'}
                required
                disabled={loading}
                placeholder="What is python?, What are arrays?, How do you create a function in JavaScript?"
              />
            </Grid>

            {/* Preview Section */}
            {formData.Task_Box && (
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Task Preview
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Card variant="outlined" sx={{ bgcolor: 'grey.50' }}>
                  <CardContent>
                    <Box display="flex" alignItems="flex-start" gap={1} mb={2}>
                      <Assignment color="primary" />
                      <Box flex={1}>
                        <Typography variant="h6" color="primary">
                          Task #{formData.Batch_ID ? `Batch-${formData.Batch_ID}` : 'XX'}-{formData.Session_ID ? `Session-${formData.Session_ID}` : 'XX'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Training task containing {questions.length} question{questions.length !== 1 ? 's' : ''}
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                      <Chip
                        icon={<Group />}
                        label={`Batch: ${formData.Batch_ID || 'Not set'}`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Chip
                        label={`Session: ${formData.Session_ID || 'Not set'}`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label="Training"
                        size="small"
                        variant="outlined"
                      />
                    </Box>

                    {questions.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Questions ({questions.length}):
                        </Typography>
                        <Box component="ol" sx={{ pl: 2, m: 0 }}>
                          {questions.map((question, index) => (
                            <Box component="li" key={index} sx={{ mb: 0.5 }}>
                              <Typography variant="body2">
                                {question}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </Box>
                    )}

                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="caption" color="text.secondary">
                      <strong>Raw Content:</strong> "{formData.Task_Box}"
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Action Buttons */}
            <Grid item xs={12}>
              <Box display="flex" gap={2} justifyContent="flex-end" sx={{ mt: 3 }}>
                <Button
                  variant="outlined"
                  onClick={handleCancel}
                  startIcon={<Cancel />}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Save />}
                  disabled={loading || !formData.Batch_ID || !formData.Session_ID || !formData.Task_Box}
                  sx={{
                    background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                    '&:hover': {
                      background: 'linear-gradient(45deg, #1976D2 30%, #2196F3 90%)'
                    }
                  }}
                >
                  {loading ? 'Creating Task...' : 'Create Task'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>

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

export default AddTrainerTask;