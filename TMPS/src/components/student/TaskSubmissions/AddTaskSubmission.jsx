import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardHeader,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  ArrowBack as ArrowBackIcon,
  Assignment as AssignmentIcon,
  AttachFile as AttachFileIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Send as SendIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useApi } from '../../../hooks/useApi';
import studentService from '../../../services/studentService';
import LoadingSpinner from '../../common/LoadingSpinner';
import { formatDate } from '../../../utils/dateUtils';

const AddTaskSubmission = () => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [submissionData, setSubmissionData] = useState({
    title: '',
    description: '',
    submissionType: 'file',
    textContent: '',
    url: '',
    notes: '',
  });
  const [attachments, setAttachments] = useState([]);
  const [isDraft, setIsDraft] = useState(false);
  const { loading, error, makeRequest } = useApi();

  useEffect(() => {
    if (taskId) {
      fetchTaskDetails();
    }
  }, [taskId]);

  const fetchTaskDetails = async () => {
    try {
      await makeRequest(async () => {
        const data = await studentService.getTrainerTask(taskId);
        setTask(data);
        
        // If there's an existing submission, populate the form
        if (data.existingSubmission) {
          setSubmissionData({
            title: data.existingSubmission.title || '',
            description: data.existingSubmission.description || '',
            submissionType: data.existingSubmission.type || 'file',
            textContent: data.existingSubmission.textContent || '',
            url: data.existingSubmission.url || '',
            notes: data.existingSubmission.notes || '',
          });
          setAttachments(data.existingSubmission.attachments || []);
        }
      });
    } catch (error) {
      console.error('Error fetching task details:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setSubmissionData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const newAttachments = files.map(file => ({
      id: Date.now() + Math.random(),
      file,
      name: file.name,
      size: (file.size / 1024 / 1024).toFixed(2) + ' MB',
      type: file.type,
      uploaded: false,
    }));
    setAttachments(prev => [...prev, ...newAttachments]);
  };

  const removeAttachment = (attachmentId) => {
    setAttachments(prev => prev.filter(att => att.id !== attachmentId));
  };

  const handleSubmit = async (asDraft = false) => {
    try {
      setIsDraft(asDraft);
      
      const formData = new FormData();
      formData.append('taskId', taskId);
      formData.append('title', submissionData.title);
      formData.append('description', submissionData.description);
      formData.append('submissionType', submissionData.submissionType);
      formData.append('textContent', submissionData.textContent);
      formData.append('url', submissionData.url);
      formData.append('notes', submissionData.notes);
      formData.append('isDraft', asDraft);

      attachments.forEach((attachment, index) => {
        if (attachment.file) {
          formData.append(`attachments`, attachment.file);
        }
      });

      await makeRequest(async () => {
        await studentService.addTaskSubmission(formData);
      });

      navigate(`/student/task-submissions`);
    } catch (error) {
      console.error('Error submitting task:', error);
    }
  };

  const getDaysRemaining = (dueDate) => {
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = due - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (loading) return <LoadingSpinner />;

  if (!task) {
    return (
      <Box>
        <Typography>Task not found.</Typography>
        <Button onClick={() => navigate(-1)} startIcon={<ArrowBackIcon />}>
          Go Back
        </Button>
      </Box>
    );
  }

  const daysRemaining = getDaysRemaining(task.dueDate);

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={() => navigate(-1)} sx={{ mr: 1 }}>
          <ArrowBackIcon />
        </IconButton>
        <AssignmentIcon sx={{ mr: 1 }} />
        <Typography variant="h5" fontWeight="bold">
          Submit Task: {task.title}
        </Typography>
      </Box>

      {/* Due Date Alert */}
      {daysRemaining <= 3 && (
        <Alert 
          severity={daysRemaining < 0 ? 'error' : daysRemaining <= 1 ? 'warning' : 'info'} 
          sx={{ mb: 2 }}
        >
          {daysRemaining < 0 
            ? `This task is overdue by ${Math.abs(daysRemaining)} day(s)!`
            : daysRemaining === 0 
            ? 'This task is due today!'
            : `This task is due in ${daysRemaining} day(s).`
          }
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Submission Form */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader title="Submission Details" />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Submission Title"
                    value={submissionData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    placeholder="Enter a title for your submission"
                    required
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Submission Type</InputLabel>
                    <Select
                      value={submissionData.submissionType}
                      label="Submission Type"
                      onChange={(e) => handleInputChange('submissionType', e.target.value)}
                    >
                      <MenuItem value="file">File Upload</MenuItem>
                      <MenuItem value="text">Text Content</MenuItem>
                      <MenuItem value="url">URL/Link</MenuItem>
                      <MenuItem value="mixed">Mixed (Files + Text)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Description"
                    value={submissionData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Describe your submission and approach"
                  />
                </Grid>

                {/* Conditional Content Based on Submission Type */}
                {(submissionData.submissionType === 'text' || submissionData.submissionType === 'mixed') && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      multiline
                      rows={8}
                      label="Text Content"
                      value={submissionData.textContent}
                      onChange={(e) => handleInputChange('textContent', e.target.value)}
                      placeholder="Enter your submission content here..."
                    />
                  </Grid>
                )}

                {(submissionData.submissionType === 'url' || submissionData.submissionType === 'mixed') && (
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="URL/Link"
                      value={submissionData.url}
                      onChange={(e) => handleInputChange('url', e.target.value)}
                      placeholder="https://example.com/your-work"
                    />
                  </Grid>
                )}

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    label="Additional Notes"
                    value={submissionData.notes}
                    onChange={(e) => handleInputChange('notes', e.target.value)}
                    placeholder="Any additional notes or comments"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* File Upload Section */}
          {(submissionData.submissionType === 'file' || submissionData.submissionType === 'mixed') && (
            <Card sx={{ mt: 2 }}>
              <CardHeader title="File Attachments" />
              <CardContent>
                <Box
                  sx={{
                    border: '2px dashed #ccc',
                    borderRadius: 2,
                    p: 3,
                    textAlign: 'center',
                    mb: 2,
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: 'primary.main',
                      backgroundColor: 'action.hover',
                    },
                  }}
                  onClick={() => document.getElementById('file-upload').click()}
                >
                  <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                  <Typography variant="h6" gutterBottom>
                    Click to upload files
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    or drag and drop your files here
                  </Typography>
                  <input
                    id="file-upload"
                    type="file"
                    multiple
                    hidden
                    onChange={handleFileUpload}
                    accept=".pdf,.doc,.docx,.txt,.zip,.jpg,.png,.ppt,.pptx"
                  />
                </Box>

                {attachments.length > 0 && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Attached Files:
                    </Typography>
                    <List>
                      {attachments.map((attachment, index) => (
                        <React.Fragment key={attachment.id}>
                          <ListItem>
                            <ListItemIcon>
                              <AttachFileIcon />
                            </ListItemIcon>
                            <ListItemText
                              primary={attachment.name}
                              secondary={`${attachment.size} • ${attachment.type}`}
                            />
                            <IconButton 
                              onClick={() => removeAttachment(attachment.id)}
                              color="error"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </ListItem>
                          {index < attachments.length - 1 && <Divider />}
                        </React.Fragment>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<SaveIcon />}
              onClick={() => handleSubmit(true)}
              disabled={!submissionData.title.trim()}
            >
              Save as Draft
            </Button>
            <Button
              variant="contained"
              startIcon={<SendIcon />}
              onClick={() => handleSubmit(false)}
              disabled={!submissionData.title.trim()}
            >
              Submit Final
            </Button>
          </Box>
        </Grid>

        {/* Task Information Sidebar */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Task Information" />
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {task.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {task.description}
              </Typography>

              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Due Date
                </Typography>
                <Typography 
                  variant="body1"
                  color={daysRemaining < 0 ? 'error' : 'text.primary'}
                >
                  {formatDate(task.dueDate)}
                </Typography>
              </Box>

              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Priority
                </Typography>
                <Chip
                  label={task.priority?.toUpperCase()}
                  size="small"
                  color={
                    task.priority === 'high' ? 'error' :
                    task.priority === 'medium' ? 'warning' :
                    'success'
                  }
                />
              </Box>

              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Estimated Time
                </Typography>
                <Typography variant="body1">
                  {task.estimatedHours || 'Not specified'} hours
                </Typography>
              </Box>
            </CardContent>
          </Card>

          {/* Requirements */}
          {task.requirements && task.requirements.length > 0 && (
            <Card sx={{ mt: 2 }}>
              <CardHeader title="Requirements" />
              <CardContent>
                <List dense>
                  {task.requirements.map((requirement, index) => (
                    <ListItem key={index} sx={{ pl: 0 }}>
                      <ListItemIcon>
                        <DescriptionIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={requirement}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}

          {/* Deliverables */}
          {task.deliverables && task.deliverables.length > 0 && (
            <Card sx={{ mt: 2 }}>
              <CardHeader title="Expected Deliverables" />
              <CardContent>
                <List dense>
                  {task.deliverables.map((deliverable, index) => (
                    <ListItem key={index} sx={{ pl: 0 }}>
                      <ListItemIcon>
                        <AssignmentIcon color="secondary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={deliverable.title}
                        secondary={deliverable.description}
                        primaryTypographyProps={{ variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}

          {/* Submission Guidelines */}
          <Paper sx={{ p: 2, mt: 2, bgcolor: 'info.light' }}>
            <Typography variant="subtitle2" gutterBottom>
              Submission Guidelines:
            </Typography>
            <Typography variant="body2" component="ul" sx={{ pl: 2, mb: 0 }}>
              <li>Ensure all requirements are met</li>
              <li>Use clear and descriptive titles</li>
              <li>Include proper documentation</li>
              <li>Test your work before submission</li>
              <li>Save drafts frequently</li>
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AddTaskSubmission;