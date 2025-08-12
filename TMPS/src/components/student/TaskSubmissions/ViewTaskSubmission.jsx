// src/components/student/TaskSubmissions/ViewTaskSubmission.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Alert,
  Snackbar,
  Divider,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Backdrop
} from '@mui/material';
import {
  ArrowBack,
  Person,
  AttachFile,
  CheckCircle,
  Warning,
  Download,
  Visibility,
  Delete,
  Close
} from '@mui/icons-material';
import { taskSubmissionsAPI } from "../../../services/API/studenttask";
import LoadingSpinner from '../../common/LoadingSpinner';

const ViewTaskSubmission = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fileLoading, setFileLoading] = useState(false);
  const [fileContent, setFileContent] = useState(null);
  const [fileType, setFileType] = useState(null);
  const [showFileViewer, setShowFileViewer] = useState(false);
  const [snackbar, setSnackbar] = useState({ 
    open: false, 
    message: '', 
    severity: 'success' 
  });

  useEffect(() => {
    fetchTaskSubmission();
  }, [id]);

  const fetchTaskSubmission = async () => {
    try {
      setLoading(true);
      console.log('🔍 Fetching task submission for ID:', id);
      
      const response = await taskSubmissionsAPI.getById(id);
      console.log('📊 Task submission response:', response);
      
      setSubmission(response);
    } catch (error) {
      console.error('❌ Error fetching task submission:', error);
      setSnackbar({
        open: true,
        message: `Error loading submission: ${error.message}`,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSubmission = async () => {
    if (window.confirm('Are you sure you want to delete this submission?')) {
      try {
        await taskSubmissionsAPI.remove(id);
        setSnackbar({
          open: true,
          message: 'Submission deleted successfully',
          severity: 'success'
        });
        
        // Navigate back to submissions list after successful deletion
        setTimeout(() => {
          navigate('/student/task-submissions');
        }, 1500);
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

  // Fixed handleViewFile method
// Enhanced handleViewFile method with better error handling and debugging
const handleViewFile = async () => {
  if (!submission?.Task_Submit) {
    setSnackbar({
      open: true,
      message: 'No file available to view',
      severity: 'warning'
    });
    return;
  }

  try {
    setFileLoading(true);
    console.log('🔍 Loading file for Student ID:', submission.Student_ID);
    console.log('📄 Expected file path:', submission.Task_Submit);

    const url = `/api/student/task-submissions/view-submission/${submission.Student_ID}`;
    console.log('🌐 Request URL:', url);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/pdf,application/octet-stream,*/*',
      }
    });

    console.log('📡 Response details:', {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      url: response.url,
      ok: response.ok
    });

    if (!response.ok) {
      // Try to get error details from response
      let errorMessage;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorData.message || `HTTP ${response.status}`;
        console.log('📋 Error response data:', errorData);
      } catch (e) {
        const errorText = await response.text();
        errorMessage = errorText || `HTTP ${response.status}: ${response.statusText}`;
        console.log('📋 Error response text:', errorText);
      }
      throw new Error(errorMessage);
    }

    // Check content type
    const contentType = response.headers.get('content-type');
    console.log('📋 Content-Type:', contentType);

    // Get the response as blob
    const blob = await response.blob();
    console.log('💾 Blob details:', {
      size: blob.size,
      type: blob.type
    });

    // Enhanced validation for different file types
    if (contentType && contentType.includes('text/html')) {
      throw new Error('Server returned HTML instead of file. Check Django logs for errors.');
    }

    if (contentType && contentType.includes('application/json')) {
      // Try to parse as JSON to get error message
      const text = await blob.text();
      const errorData = JSON.parse(text);
      throw new Error(errorData.error || 'Server returned JSON error response');
    }

    // For small files, check if content looks like HTML
    if (blob.size < 10000) { // Only check small files to avoid performance issues
      const textCheck = await blob.text();
      if (textCheck.includes('<!DOCTYPE html>') || 
          textCheck.includes('<html') || 
          textCheck.includes('@react-refresh') ||
          textCheck.includes('webpack')) {
        console.log('🔍 Response content preview:', textCheck.substring(0, 500));
        throw new Error('Server returned HTML/JavaScript instead of file. Possible Django routing issue.');
      }
      
      // Create blob again since we consumed the original
      const fileBlob = new Blob([textCheck], { 
        type: contentType || 'application/octet-stream' 
      });
      
      const url = URL.createObjectURL(fileBlob);
      console.log('✅ Blob URL created:', url);

      // Determine file type for viewer
      let viewerType = 'unknown';
      if (contentType) {
        if (contentType.includes('pdf')) {
          viewerType = 'pdf';
        } else if (contentType.includes('image')) {
          viewerType = 'image';
        } else if (contentType.includes('text')) {
          viewerType = 'text';
        } else if (contentType.includes('officedocument') || 
                   contentType.includes('msword') || 
                   contentType.includes('excel')) {
          viewerType = 'office';
        }
      } else {
        // Guess from file extension
        const fileName = getFileName(submission.Task_Submit).toLowerCase();
        if (fileName.endsWith('.pdf')) {
          viewerType = 'pdf';
        } else if (fileName.match(/\.(jpg|jpeg|png|gif|bmp)$/)) {
          viewerType = 'image';
        } else if (fileName.match(/\.(txt|log|csv)$/)) {
          viewerType = 'text';
        } else if (fileName.match(/\.(doc|docx|xls|xlsx|ppt|pptx)$/)) {
          viewerType = 'office';
        }
      }

      setFileType(viewerType);
      setFileContent(url);
      setShowFileViewer(true);
      
    } else {
      // For larger files, create blob URL directly
      const url = URL.createObjectURL(blob);
      console.log('✅ Large file blob URL created:', url);

      // Determine type from content-type or filename
      let viewerType = 'pdf'; // Default assumption for larger files
      if (contentType) {
        if (contentType.includes('pdf')) {
          viewerType = 'pdf';
        } else if (contentType.includes('image')) {
          viewerType = 'image';
        } else if (contentType.includes('officedocument') || 
                   contentType.includes('msword') || 
                   contentType.includes('excel')) {
          viewerType = 'office';
        }
      }

      setFileType(viewerType);
      setFileContent(url);
      setShowFileViewer(true);
    }

  } catch (error) {
    console.error('❌ Error viewing file:', error);
    
    // Provide more specific error messages
    let userMessage = error.message;
    if (error.message.includes('Failed to fetch')) {
      userMessage = 'Network error: Cannot connect to server. Please check your connection.';
    } else if (error.message.includes('404')) {
      userMessage = 'File not found on server. It may have been moved or deleted.';
    } else if (error.message.includes('403')) {
      userMessage = 'Access denied. You may not have permission to view this file.';
    } else if (error.message.includes('500')) {
      userMessage = 'Server error. Please contact administrator or try again later.';
    }
    
    setSnackbar({
      open: true,
      message: `Error viewing file: ${userMessage}`,
      severity: 'error'
    });
  } finally {
    setFileLoading(false);
  }
};

// Additional debug function you can call to test the endpoint
const debugFileEndpoint = async () => {
  try {
    console.log('🐛 Starting debug for Student ID:', submission.Student_ID);
    
    // First, try the debug endpoint (if you implement it)
    const debugUrl = `/api/student/task-submissions/debug/${submission.Student_ID}`;
    const debugResponse = await fetch(debugUrl);
    
    if (debugResponse.ok) {
      const debugData = await debugResponse.json();
      console.log('🔍 Debug info:', debugData);
      
      setSnackbar({
        open: true,
        message: 'Debug info logged to console. Check browser developer tools.',
        severity: 'info'
      });
    } else {
      console.log('❌ Debug endpoint not available');
    }
  } catch (error) {
    console.error('❌ Debug failed:', error);
  }
};

  // Enhanced download function
  const handleDirectDownload = async () => {
    try {
      const fileName = getFileName(submission.Task_Submit);
      const response = await fetch(`/api/student/task-submissions/view-submission/${submission.Student_ID}`, {
        method: 'GET',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setSnackbar({
        open: true,
        message: 'File download started',
        severity: 'success'
      });
    } catch (error) {
      console.error('❌ Error downloading file:', error);
      setSnackbar({
        open: true,
        message: `Download failed: ${error.message}`,
        severity: 'error'
      });
    }
  };

  const handleCloseFileViewer = () => {
    setShowFileViewer(false);
    // Clean up blob URLs
    if (fileContent && (fileType === 'pdf' || fileType === 'image')) {
      URL.revokeObjectURL(fileContent);
    }
    setFileContent(null);
    setFileType(null);
  };

  if (loading) {
    return <LoadingSpinner message="Loading task submission details..." />;
  }

  if (!submission) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Warning sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          Task Submission Not Found
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          The requested task submission could not be found.
        </Typography>
        <Button
          variant="contained"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/student/task-submissions')}
        >
          Back to Task Submissions
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <IconButton 
            onClick={() => navigate('/student/task-submissions')}
            sx={{ mr: 2 }}
          >
            <ArrowBack />
          </IconButton>
          <Typography variant="h5">
            Task Submission Details
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={handleDeleteSubmission}
            sx={{ mr: 2 }}
          >
            Delete Submission
          </Button>
          <Button
            variant="contained"
            onClick={() => navigate('/student/task-submissions')}
          >
            Back to List
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            {/* Status Badge */}
            <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
              <Typography variant="h6" component="h2">
                Submission Information
              </Typography>
              <Chip 
                icon={<CheckCircle />} 
                label="Submitted" 
                color="success" 
                size="medium" 
              />
            </Box>

            <Divider sx={{ mb: 3 }} />

            {/* Student Information */}
            <Box mb={3}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Person sx={{ mr: 1 }} />
                Student Information
              </Typography>
              
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Student ID
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {submission.Student_ID}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Student Name
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {submission.Student_Name || 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
            </Box>

            <Divider sx={{ mb: 3 }} />

            {/* Submission Details */}
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                Submission Details
              </Typography>
              
              {submission.created_at && (
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    Submitted On
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatDate(submission.created_at)}
                  </Typography>
                </Box>
              )}

              {submission.updated_at && submission.updated_at !== submission.created_at && (
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    Last Updated
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatDate(submission.updated_at)}
                  </Typography>
                </Box>
              )}
            </Box>

            <Divider sx={{ mb: 3 }} />

            {/* File Information */}
            {submission.Task_Submit && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Submitted File
                </Typography>
                
                <Card variant="outlined" sx={{ mt: 2 }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Box display="flex" alignItems="center">
                        {getFileIcon(submission.Task_Submit)}
                        <Box ml={2}>
                          <Typography variant="body1" fontWeight="medium">
                            {getFileName(submission.Task_Submit)}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Task submission file
                          </Typography>
                        </Box>
                      </Box>
                      <Box>
                        <Button
                          variant="outlined"
                          startIcon={fileLoading ? <CircularProgress size={16} /> : <Visibility />}
                          onClick={handleViewFile}
                          sx={{ mr: 1 }}
                          disabled={fileLoading}
                        >
                          {fileLoading ? 'Loading...' : 'View File'}
                        </Button>
                        <Button
                          variant="outlined"
                          startIcon={<Download />}
                          onClick={handleDirectDownload}
                          sx={{ mr: 1 }}
                        >
                          Download
                        </Button>
                        <IconButton
                          color="primary"
                          onClick={() => window.open(`/api/student/task-submissions/view-submission/${submission.Student_ID}`, '_blank')}
                          title="Open in New Tab (for debugging)"
                        >
                          <Download />
                        </IconButton>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, bgcolor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom>
              Submission Status
            </Typography>
            
            <Box mb={3}>
              <Chip 
                icon={<CheckCircle />} 
                label="Successfully Submitted" 
                color="success" 
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" color="text.secondary">
                Your task has been submitted successfully and is available for review.
              </Typography>
            </Box>

            {submission.grade && (
              <Box mb={3}>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Grade
                </Typography>
                <Typography variant="h4" color="success.main" gutterBottom>
                  {submission.grade}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Graded submission
                </Typography>
              </Box>
            )}

            {submission.feedback && (
              <Box mb={3}>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="subtitle1" gutterBottom>
                  Feedback
                </Typography>
                <Typography variant="body2" sx={{ 
                  bgcolor: 'background.paper', 
                  p: 2, 
                  borderRadius: 1,
                  border: '1px solid',
                  borderColor: 'divider'
                }}>
                  {submission.feedback}
                </Typography>
              </Box>
            )}

            {!submission.grade && !submission.feedback && (
              <Box>
                <Divider sx={{ mb: 2 }} />
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    <strong>Pending Review</strong><br />
                    Your submission is awaiting review by the instructor. 
                    You will be notified once feedback or grades are available.
                  </Typography>
                </Alert>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* File Viewer Dialog */}
      <Dialog
        open={showFileViewer}
        onClose={handleCloseFileViewer}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {getFileName(submission?.Task_Submit)}
            </Typography>
            <IconButton onClick={handleCloseFileViewer}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0, height: '100%' }}>
          {fileContent && (
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              {fileType === 'pdf' && (
                <Box sx={{ height: '100%', width: '100%' }}>
                  {fileContent? (
                    <iframe
                      src={fileContent}
                      title="PDF Viewer"
                      style={{ 
                        width: '100%', 
                        height: '100%', 
                        border: 'none' 
                      }}
                      // title="PDF Viewer"
                      allowFullScreen
                    />
                  ):(
                   <Box textAlign={'center'} sx={{ p: 3 }}>
                    <Typography variant='h6' color='error '>
                      PDF preview failed.try downloading the file InterviewerSpeakingCard
                      </Typography>
                   </Box>
              )}
                </Box>
              )}
              
              {fileType === 'image' && (
                <Box sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center',
                  p: 2
                }}>
                  <img
                    src={fileContent}
                    alt="Submitted file"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '100%',
                      objectFit: 'contain'
                    }}
                  />
                </Box>
              )}
              
              {fileType === 'text' && (
                <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50', height: '100%' }}>
                    <pre style={{ 
                      whiteSpace: 'pre-wrap', 
                      wordBreak: 'break-word',
                      margin: 0,
                      fontFamily: 'monospace'
                    }}>
                      {fileContent}
                    </pre>
                  </Paper>
                </Box>
              )}
              
              {fileType === 'office' && (
                <Box sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center',
                  flexDirection: 'column',
                  p: 3
                }}>
                  <AttachFile sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Office Document
                  </Typography>
                  <Typography variant="body2" color="text.secondary" textAlign="center" paragraph>
                    Office documents (Word, Excel, PowerPoint) cannot be previewed in the browser. 
                    Please download the file to view its contents.
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Download />}
                    onClick={handleDirectDownload}
                  >
                    Download {getFileName(submission.Task_Submit)}
                  </Button>
                </Box>
              )}

              {fileType === 'unknown' && (
                <Box sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  justifyContent: 'center', 
                  alignItems: 'center',
                  flexDirection: 'column',
                  p: 3
                }}>
                  <AttachFile sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    File Preview Not Available
                  </Typography>
                  <Typography variant="body2" color="text.secondary" textAlign="center" paragraph>
                    This file type cannot be previewed in the browser. 
                    You can download it to view the content.
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Download />}
                    onClick={handleDirectDownload}
                  >
                    Download File
                  </Button>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            startIcon={<Download />}
            onClick={handleDirectDownload}
          >
            Download
          </Button>
          <Button onClick={handleCloseFileViewer}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Loading Backdrop */}
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={fileLoading}
      >
        <Box textAlign="center">
          <CircularProgress color="inherit" />
          <Typography variant="body2" sx={{ mt: 2 }}>
            Loading file...
          </Typography>
        </Box>
      </Backdrop>

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

export default ViewTaskSubmission;