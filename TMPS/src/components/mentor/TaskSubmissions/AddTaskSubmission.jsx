import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Alert,
  LinearProgress,
  Paper,
  Chip,
  Divider
} from '@mui/material';
import {
  Upload,
  CloudUpload,
  Close,
  ArrowBack,
  Assignment,
  AttachFile,
  Description
} from '@mui/icons-material';

const MentorAddTaskSubmission = ({ onBack, onSave, taskId }) => {
  const [formData, setFormData] = useState({
    taskId: taskId || '',
    submissionText: '',
    timeSpent: '',
    notes: ''
  });
  const [attachments, setAttachments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [errors, setErrors] = useState({});
  const [tasks, setTasks] = useState([
    { id: 1, title: 'React Components Tutorial', dueDate: '2024-12-20' },
    { id: 2, title: 'Database Design Review', dueDate: '2024-12-18' },
    { id: 3, title: 'API Workshop Materials', dueDate: '2024-12-22' },
    { id: 4, title: 'Course Documentation Update', dueDate: '2024-12-25' }
  ]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const handleFileUpload = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const newAttachments = selectedFiles.map(file => ({
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      id: Date.now() + Math.random()
    }));

    setAttachments(prev => [...prev, ...newAttachments]);
  };

  const removeAttachment = (attachmentId) => {
    setAttachments(prev => prev.filter(attachment => attachment.id !== attachmentId));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.taskId) {
      newErrors.taskId = 'Please select a task';
    }

    if (!formData.submissionText.trim()) {
      newErrors.submissionText = 'Submission description is required';
    }

    if (!formData.timeSpent.trim()) {
      newErrors.timeSpent = 'Time spent is required';
    }

    if (attachments.length === 0) {
      newErrors.attachments = 'At least one attachment is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setUploading(true);
    
    try {
      // Simulate upload process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const submissionData = {
        ...formData,
        attachments: attachments.map(att => ({
          name: att.name,
          size: att.size,
          type: att.type
        })),
        submissionDate: new Date().toISOString(),
        status: 'submitted',
        submitter: 'Current User' // Replace with actual user
      };

      onSave && onSave(submissionData);
      
    } catch (error) {
      setErrors({ submit: 'Failed to submit. Please try again.' });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type) => {
    if (type.includes('pdf')) return <Description color="error" />;
    if (type.includes('image')) return <Description color="primary" />;
    if (type.includes('video')) return <Description color="secondary" />;
    return <AttachFile />;
  };

  const selectedTask = tasks.find(task => task.id.toString() === formData.taskId);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={onBack} sx={{ mr: 2 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h4" component="h1">
          Submit Task
        </Typography>
      </Box>

      {uploading && (
        <Box sx={{ mb: 3 }}>
          <Alert severity="info">
            Submitting your work... Please wait.
          </Alert>
          <LinearProgress sx={{ mt: 1 }} />
        </Box>
      )}

      {errors.submit && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {errors.submit}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Submission Form */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Submission Details
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth error={!!errors.taskId}>
                    <InputLabel>Select Task</InputLabel>
                    <Select
                      value={formData.taskId}
                      label="Select Task"
                      onChange={(e) => handleInputChange('taskId', e.target.value)}
                      disabled={uploading || taskId} // Disable if taskId is provided
                    >
                      {tasks.map((task) => (
                        <MenuItem key={task.id} value={task.id.toString()}>
                          <Box>
                            <Typography variant="body2">{task.title}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              Due: {new Date(task.dueDate).toLocaleDateString()}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.taskId && (
                      <Typography variant="caption" color="error">
                        {errors.taskId}
                      </Typography>
                    )}
                  </FormControl>
                </Grid>

                {selectedTask && (
                  <Grid item xs={12}>
                    <Alert severity="info">
                      <Typography variant="body2">
                        <strong>Task:</strong> {selectedTask.title}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Due Date:</strong> {new Date(selectedTask.dueDate).toLocaleDateString()}
                      </Typography>
                    </Alert>
                  </Grid>
                )}
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={6}
                    label="Submission Description"
                    value={formData.submissionText}
                    onChange={(e) => handleInputChange('submissionText', e.target.value)}
                    error={!!errors.submissionText}
                    helperText={errors.submissionText || 'Describe what you have completed and any important details'}
                    disabled={uploading}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Time Spent"
                    value={formData.timeSpent}
                    onChange={(e) => handleInputChange('timeSpent', e.target.value)}
                    error={!!errors.timeSpent}
                    helperText={errors.timeSpent || 'e.g., 5 hours, 2 days'}
                    disabled={uploading}
                    placeholder="e.g., 5 hours"
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Additional Notes (Optional)"
                    value={formData.notes}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                    disabled={uploading}
                    placeholder="Any additional information or challenges faced..."
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* File Upload */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Attachments
              </Typography>
              
              <Paper
                sx={{
                  border: '2px dashed',
                  borderColor: errors.attachments ? 'error.main' : 'primary.main',
                  borderRadius: 2,
                  p: 3,
                  textAlign: 'center',
                  cursor: 'pointer',
                  backgroundColor: 'action.hover',
                  '&:hover': {
                    backgroundColor: 'action.selected'
                  }
                }}
                onClick={() => document.getElementById('file-upload').click()}
              >
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  onChange={handleFileUpload}
                  style={{ display: 'none' }}
                  disabled={uploading}
                />
                
                <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6" gutterBottom>
                  Upload Files
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Drop files here or click to browse
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                  All file types accepted
                </Typography>
              </Paper>
              
              {errors.attachments && (
                <Alert severity="error" sx={{ mt: 1 }}>
                  {errors.attachments}
                </Alert>
              )}

              {/* File List */}
              {attachments.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Attached Files ({attachments.length})
                  </Typography>
                  
                  {attachments.map((attachment) => (
                    <Paper
                      key={attachment.id}
                      sx={{
                        p: 2,
                        mb: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getFileIcon(attachment.type)}
                        <Box sx={{ ml: 1 }}>
                          <Typography variant="body2" noWrap>
                            {attachment.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatFileSize(attachment.size)}
                          </Typography>
                        </Box>
                      </Box>
                      
                      <IconButton
                        size="small"
                        onClick={() => removeAttachment(attachment.id)}
                        disabled={uploading}
                      >
                        <Close />
                      </IconButton>
                    </Paper>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Submission Guidelines */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom color="primary">
                Submission Guidelines
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Required Items:</strong>
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                <li>
                  <Typography variant="body2">
                    Detailed description of completed work
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    All deliverable files
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Accurate time tracking
                  </Typography>
                </li>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="body2" paragraph>
                <strong>Tips for Success:</strong>
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                <li>
                  <Typography variant="body2">
                    Be specific about what you accomplished
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Include screenshots or examples when relevant
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2">
                    Note any challenges or learnings
                  </Typography>
                </li>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Buttons */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          onClick={onBack}
          disabled={uploading}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={uploading}
          startIcon={uploading ? null : <Upload />}
        >
          {uploading ? 'Submitting...' : 'Submit Task'}
        </Button>
      </Box>
    </Box>
  );
};

export default MentorAddTaskSubmission;