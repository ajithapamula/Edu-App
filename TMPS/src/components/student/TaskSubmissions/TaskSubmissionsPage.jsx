import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Alert,
  Snackbar,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  CloudUpload,
  Assignment,
  Visibility,
  Delete,
  AttachFile,
  Close,
  CheckCircle,
  Warning,
  Upload,
  Person,
  Search,
  BugReport
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../../common/LoadingSpinner';
import { taskSubmissionsAPI } from "../../../services/API/studenttask";

const TaskSubmissionPage = () => {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [openSubmitDialog, setOpenSubmitDialog] = useState(false);
  
  // Form state matching your backend exactly
  const [formData, setFormData] = useState({
    Student_ID: '',
    Task_Submit: null
  });
  
  const [studentLoading, setStudentLoading] = useState(false);
  const [studentFound, setStudentFound] = useState(null); // null, true, or false
  const [studentName, setStudentName] = useState(''); // Keep student name separate
  const [debugInfo, setDebugInfo] = useState(null);
  
  const [snackbar, setSnackbar] = useState({ 
    open: false, 
    message: '', 
    severity: 'success' 
  });

  const navigate = useNavigate();

  // Debug function to check database
  const debugSubmission = async () => {
    try {
      console.log('🔍 Debugging submission data...');
      
      // Check what students exist in the database
      const studentsResponse = await fetch('/api/debug/students', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (studentsResponse.ok) {
        const studentsData = await studentsResponse.json();
        console.log('📊 Available students:', studentsData);
        setDebugInfo(studentsData);
        
        setSnackbar({
          open: true,
          message: `Found ${studentsData.total_students} students in database. Check console for details.`,
          severity: 'info'
        });
      } else {
        console.log('❌ Could not fetch students list');
        setSnackbar({
          open: true,
          message: 'Debug endpoint not available. Add the debug endpoint to your Django backend.',
          severity: 'warning'
        });
      }
      
      // Test the form data that would be sent
      console.log('📤 Current form data:', {
        Student_ID: formData.Student_ID,
        Student_ID_Type: typeof formData.Student_ID,
        Task_Submit: formData.Task_Submit ? {
          name: formData.Task_Submit.name,
          size: formData.Task_Submit.size,
          type: formData.Task_Submit.type
        } : null,
        Student_Name: studentName
      });
      
    } catch (error) {
      console.error('❌ Debug error:', error);
      setSnackbar({
        open: true,
        message: 'Debug failed. Check console for details.',
        severity: 'error'
      });
    }
  };

  // Fetch existing submissions
  const fetchSubmissions = async () => {
    try {
      setLoading(true);
      console.log('🔍 Fetching task submissions...');
      
      const response = await taskSubmissionsAPI.getAll();
      console.log('📊 Raw API response:', response);
      
      // Handle the response properly
      let submissions = [];
      if (Array.isArray(response)) {
        submissions = response;
      } else if (response && Array.isArray(response.data)) {
        submissions = response.data;
      } else if (response && typeof response === 'object') {
        // If single object, wrap in array
        submissions = [response];
      }
      
      console.log('📈 Processed submissions:', submissions);
      setSubmissions(submissions);
      
    } catch (error) {
      console.error('❌ Error fetching submissions:', error);
      setSnackbar({
        open: true,
        message: `Error loading submissions: ${error.message}`,
        severity: 'error'
      });
      setSubmissions([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch student name by ID
  const fetchStudentName = async (studentId) => {
    if (!studentId.trim()) {
      setStudentName('');
      setStudentFound(null);
      return;
    }

    try {
      setStudentLoading(true);
      setStudentFound(null);
      
      console.log('🔍 Fetching student name for ID:', studentId);
      
      // Try the student name endpoint first
      try {
        const response = await fetch(`/api/get-student-name/${studentId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        if (response.ok) {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            const name = data.student_name || data.name || '';
            
            if (name) {
              setStudentName(name);
              setStudentFound(true);
              console.log('✅ Student found:', name);
              return;
            }
          }
        }
      } catch (endpointError) {
        console.log('📝 Student name endpoint not available, using alternative method');
      }
      
      // Alternative: Use existing task submission to validate student
      try {
        const existingSubmission = await taskSubmissionsAPI.getById(studentId);
        if (existingSubmission && existingSubmission.Student_Name) {
          setStudentName(existingSubmission.Student_Name);
          setStudentFound(true);
          console.log('✅ Student found via existing submission:', existingSubmission.Student_Name);
          return;
        }
      } catch (submissionError) {
        console.log('📝 No existing submission found for student');
      }
      
      // If we reach here, student was not found
      setStudentName('');
      setStudentFound(false);
      console.log('❌ Student ID not found');
      
    } catch (error) {
      console.error('❌ Error fetching student name:', error);
      setStudentName('');
      setStudentFound(false);
    } finally {
      setStudentLoading(false);
    }
  };

  // Debounce function for student ID lookup
  const useDebounce = (callback, delay) => {
    const timeoutRef = React.useRef(null);
    
    return React.useCallback((...args) => {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => callback(...args), delay);
    }, [callback, delay]);
  };

  const debouncedFetchStudentName = useDebounce(fetchStudentName, 800);

  // Handle Student ID change
  const handleStudentIdChange = (value) => {
    setFormData(prev => ({
      ...prev,
      Student_ID: value
    }));
    
    // Trigger debounced student name lookup
    debouncedFetchStudentName(value);
  };

  // Handle file selection
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type (matching backend validation)
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'image/jpeg',
        'image/png'
      ];
      
      if (!allowedTypes.includes(file.type)) {
        setSnackbar({
          open: true,
          message: 'Invalid file type. Please upload PDF, Word, Excel, or Image files only.',
          severity: 'error'
        });
        return;
      }
      
      // Validate file size (5MB limit - matching backend)
      const maxSize = 5 * 1024 * 1024; // 5MB
      if (file.size > maxSize) {
        setSnackbar({
          open: true,
          message: 'File size exceeds 5MB limit. Please choose a smaller file.',
          severity: 'error'
        });
        return;
      }
      
      setFormData(prev => ({
        ...prev,
        Task_Submit: file
      }));
    }
  };

  // Handle task submission - enhanced with debugging
  const handleSubmitTask = async () => {
    try {
      // Validation
      if (!formData.Student_ID.trim()) {
        setSnackbar({
          open: true,
          message: 'Please enter your Student ID',
          severity: 'error'
        });
        return;
      }

      if (!formData.Task_Submit) {
        setSnackbar({
          open: true,
          message: 'Please select a file to submit',
          severity: 'error'
        });
        return;
      }

      setSubmitting(true);
      setUploadProgress(0);
      
      // Enhanced logging for debugging
      console.log('📤 Submitting task with data:', {
        Student_ID: formData.Student_ID.trim(),
        Student_ID_Type: typeof formData.Student_ID,
        fileName: formData.Task_Submit.name,
        fileSize: formData.Task_Submit.size,
        fileType: formData.Task_Submit.type,
        Student_Name_Found: studentName
      });

      // Prepare form data exactly as backend expects
      const submissionData = new FormData();
      submissionData.append('Student_ID', formData.Student_ID.trim());
      submissionData.append('Task_Submit', formData.Task_Submit);
      
      // Log FormData contents (for debugging)
      console.log('📦 FormData contents:');
      for (let [key, value] of submissionData.entries()) {
        if (value instanceof File) {
          console.log(`${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
        } else {
          console.log(`${key}: ${value}`);
        }
      }

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Submit using your existing API
      const response = await taskSubmissionsAPI.add(submissionData);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      console.log('✅ Submission response:', response);
      
      setSnackbar({
        open: true,
        message: `Task submitted successfully!`,
        severity: 'success'
      });
      
      // Reset form
      setFormData({
        Student_ID: '',
        Task_Submit: null
      });
      setStudentName('');
      setStudentFound(null);
      
      setOpenSubmitDialog(false);
      
      // Refresh submissions
      await fetchSubmissions();
      
    } catch (error) {
      console.error('❌ Detailed submission error:', {
        message: error.message,
        stack: error.stack,
        formData: {
          Student_ID: formData.Student_ID,
          fileName: formData.Task_Submit?.name,
          fileSize: formData.Task_Submit?.size
        }
      });
      
      let errorMessage = 'Failed to submit task. Please try again.';
      
      if (error.message.includes('Invalid or non-existent Student_ID')) {
        errorMessage = `Student ID "${formData.Student_ID}" not found in database. Please check the ID or contact administrator.`;
      } else if (error.message.includes('404')) {
        errorMessage = 'Submission endpoint not found. Please contact administrator.';
      }
      
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error'
      });
    } finally {
      setSubmitting(false);
      setUploadProgress(0);
    }
  };

  // Navigate to view submission details
  const handleViewSubmission = (studentId) => {
    navigate(`/student/task-submissions/view/${studentId}`);
  };

  // Delete submission
  const handleDeleteSubmission = async (studentId) => {
    if (window.confirm('Are you sure you want to delete this submission?')) {
      try {
        await taskSubmissionsAPI.remove(studentId);
        setSnackbar({
          open: true,
          message: 'Submission deleted successfully',
          severity: 'success'
        });
        fetchSubmissions();
      } catch (error) {
        console.error('Error deleting submission:', error);
        setSnackbar({
          open: true,
          message: 'Failed to delete submission',
          severity: 'error'
        });
      }
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get file type icon
  const getFileIcon = (fileName) => {
    if (!fileName) return <AttachFile />;
    const ext = fileName.split('.').pop()?.toLowerCase();
    
    switch (ext) {
      case 'pdf':
        return <AttachFile color="error" />;
      case 'doc':
      case 'docx':
        return <AttachFile color="primary" />;
      case 'xls':
      case 'xlsx':
        return <AttachFile color="success" />;
      case 'jpg':
      case 'jpeg':
      case 'png':
        return <AttachFile color="warning" />;
      default:
        return <AttachFile />;
    }
  };

  // Get filename from URL or path
  const getFileName = (filePath) => {
    if (!filePath) return 'No file';
    if (filePath.includes('/')) {
      return filePath.split('/').pop();
    }
    return filePath;
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  // Load submissions on component mount
  useEffect(() => {
    fetchSubmissions();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Loading task submissions..." />;
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          Task Submissions
        </Typography>
        <Button
          variant="contained"
          startIcon={<Upload />}
          onClick={() => setOpenSubmitDialog(true)}
          color="primary"
        >
          Submit New Task
        </Button>
      </Box>

      {/* Debug Info Display */}
      {debugInfo && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
          <Typography variant="h6" gutterBottom>
            Debug Information
          </Typography>
          <Typography variant="body2" paragraph>
            <strong>Total Students in Database:</strong> {debugInfo.total_students}
          </Typography>
          <Typography variant="body2" paragraph>
            <strong>Sample Student IDs:</strong> {debugInfo.students?.map(s => s.ID).join(', ')}
          </Typography>
          <Typography variant="body2" paragraph>
            <strong>Table Structure:</strong> {debugInfo.table_structure?.map(col => col.column_name).join(', ')}
          </Typography>
        </Paper>
      )}

      {/* Submissions List */}
      <Box>
        {submissions.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Assignment sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Task Submissions Yet
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              You haven't submitted any tasks yet. Click "Submit New Task" to get started.
            </Typography>
            <Button
              variant="contained"
              startIcon={<Upload />}
              onClick={() => setOpenSubmitDialog(true)}
              sx={{ mt: 2 }}
            >
              Submit Your First Task
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {submissions.map((submission, index) => (
              <Grid item xs={12} md={6} lg={4} key={submission.Student_ID || index}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <Typography variant="h6" component="h2" gutterBottom>
                        {submission.Student_Name || 'Unknown Student'}
                      </Typography>
                      <Chip 
                        icon={<CheckCircle />} 
                        label="Submitted" 
                        color="success" 
                        size="small" 
                      />
                    </Box>
                    
                    <Box mb={2}>
                      <Typography variant="body2" display="flex" alignItems="center" gutterBottom>
                        <Person fontSize="small" sx={{ mr: 1 }} />
                        <strong>Student ID:</strong> {submission.Student_ID}
                      </Typography>
                      <Typography variant="body2" display="flex" alignItems="center" gutterBottom>
                        <Person fontSize="small" sx={{ mr: 1 }} />
                        <strong>Student Name:</strong> {submission.Student_Name || 'N/A'}
                      </Typography>
                      <Typography variant="body2" display="flex" alignItems="center" gutterBottom>
                        {getFileIcon(submission.Task_Submit)}
                        <strong style={{ marginLeft: 8 }}>File:</strong> 
                        <span style={{ marginLeft: 4 }}>
                          {getFileName(submission.Task_Submit)}
                        </span>
                      </Typography>
                      {submission.created_at && (
                        <Typography variant="body2" gutterBottom>
                          <strong>Submitted:</strong> {formatDate(submission.created_at)}
                        </Typography>
                      )}
                    </Box>

                    {submission.grade && (
                      <Alert severity="success" sx={{ mt: 2 }}>
                        <Typography variant="caption">
                          <strong>Grade:</strong> {submission.grade}
                        </Typography>
                      </Alert>
                    )}
                  </CardContent>
                  
                  <CardActions>
                    <Button
                      variant="outlined"
                      startIcon={<Visibility />}
                      onClick={() => handleViewSubmission(submission.Student_ID)}
                      size="small"
                    >
                      View Details
                    </Button>
                    <IconButton
                      color="error"
                      onClick={() => handleDeleteSubmission(submission.Student_ID)}
                      size="small"
                    >
                      <Delete />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>

      {/* Task Submission Dialog */}
      <Dialog 
        open={openSubmitDialog} 
        onClose={() => !submitting && setOpenSubmitDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Submit New Task
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="body2">
                <strong>Submission Requirements:</strong><br />
                • <strong>Student ID:</strong> Your unique student identifier<br />
                • <strong>Task Submit:</strong> File to submit (PDF, Word, Excel, Images)<br />
                • <strong>Student Name:</strong> Auto-filled from your Student ID<br />
                • Maximum file size: 5MB
              </Typography>
            </Alert>

            <TextField
              label="Student ID"
              value={formData.Student_ID}
              onChange={(e) => handleStudentIdChange(e.target.value)}
              fullWidth
              required
              margin="normal"
              placeholder="Enter your Student ID"
              disabled={submitting}
              InputProps={{
                endAdornment: studentLoading ? (
                  <Search />
                ) : studentFound === true ? (
                  <CheckCircle color="success" />
                ) : studentFound === false ? (
                  <Warning color="warning" />
                ) : null
              }}
              helperText={
                studentFound === false 
                  ? "Student ID not found in existing records (you can still submit)" 
                  : studentFound === true 
                    ? `Student found: ${studentName}`
                    : "Enter Student ID (name will be auto-filled by system)"
              }
            />
            
            <TextField
              label="Student Name"
              value={studentName}
              fullWidth
              margin="normal"
              disabled
              placeholder="Student Name will be auto-filled by system"
              InputProps={{
                readOnly: true,
              }}
              helperText="The system will automatically fetch your name from the database"
              sx={{
                '& .MuiInputBase-input.Mui-disabled': {
                  WebkitTextFillColor: studentName ? 'rgba(0, 0, 0, 0.87)' : 'rgba(0, 0, 0, 0.38)',
                },
              }}
            />
            
            <Box mt={3}>
              <Button
                variant="outlined"
                component="label"
                startIcon={<CloudUpload />}
                fullWidth
                disabled={submitting}
                sx={{ mb: 2, py: 2 }}
              >
                {formData.Task_Submit ? 'Change Task Submit File' : 'Choose Task Submit File'}
                <input
                  type="file"
                  hidden
                  onChange={handleFileChange}
                  accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png"
                />
              </Button>
              
              {formData.Task_Submit && (
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box display="flex" alignItems="center">
                      {getFileIcon(formData.Task_Submit.name)}
                      <Box ml={1}>
                        <Typography variant="body2" fontWeight="medium">
                          {formData.Task_Submit.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {(formData.Task_Submit.size / 1024 / 1024).toFixed(2)} MB
                        </Typography>
                      </Box>
                    </Box>
                    <IconButton 
                      size="small" 
                      onClick={() => setFormData(prev => ({ ...prev, Task_Submit: null }))}
                      disabled={submitting}
                    >
                      <Close />
                    </IconButton>
                  </Box>
                </Paper>
              )}
            </Box>
            
            {submitting && (
              <Box mt={2}>
                <Typography variant="body2" gutterBottom>
                  Uploading... {uploadProgress}%
                </Typography>
                <LinearProgress variant="determinate" value={uploadProgress} />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={debugSubmission}
            color="info"
            variant="outlined"
            startIcon={<BugReport />}
            sx={{ mr: 'auto' }}
            disabled={submitting}
          >
            Debug Info
          </Button>
          <Button 
            onClick={() => setOpenSubmitDialog(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSubmitTask}
            disabled={submitting || !formData.Student_ID.trim() || !formData.Task_Submit || studentLoading}
            startIcon={submitting ? null : <Upload />}
          >
            {submitting ? 'Submitting...' : 'Submit Task'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
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

export default TaskSubmissionPage;