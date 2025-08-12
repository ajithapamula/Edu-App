import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  LinearProgress,
  Chip,
  Grid,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import {
  Save,
  Cancel,
  CloudUpload,
  Storage
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { sessionRecordingsAPI } from '../../../services/API/sessionrecordings';

const MentorAddSessionRecording = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    Video_Name: '',
    Session_ID: '',
    Batch_ID: '',
    recordingFile: null
  });
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState(false);

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

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      const validTypes = ['video/mp4', 'video/webm', 'video/ogg', 'video/avi'];
      if (!validTypes.includes(file.type)) {
        setErrors(prev => ({
          ...prev,
          recordingFile: 'Please select a valid video file (MP4, WebM, OGG, AVI)'
        }));
        return;
      }

      // Validate file size (max 2GB)
      const maxSize = 2 * 1024 * 1024 * 1024; // 2GB in bytes
      if (file.size > maxSize) {
        setErrors(prev => ({
          ...prev,
          recordingFile: 'File size must be less than 2GB'
        }));
        return;
      }

      setFormData(prev => ({
        ...prev,
        recordingFile: file
      }));
      
      // Clear file error
      if (errors.recordingFile) {
        setErrors(prev => ({
          ...prev,
          recordingFile: ''
        }));
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.Video_Name.trim()) {
      newErrors.Video_Name = 'Video name is required';
    }

    if (!formData.Session_ID.trim()) {
      newErrors.Session_ID = 'Session ID is required';
    }

    if (!formData.Batch_ID.trim()) {
      newErrors.Batch_ID = 'Batch ID is required';
    }

    if (!formData.recordingFile) {
      newErrors.recordingFile = 'Recording file is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      // Prepare data for API call
      const uploadData = {
        file: formData.recordingFile,
        Video_Name: formData.Video_Name,
        Session_ID: formData.Session_ID,
        Batch_ID: formData.Batch_ID
      };

      // Call the API
      const response = await sessionRecordingsAPI.add(uploadData);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setSuccess(true);
      
      console.log('Upload successful:', response);
      
      setTimeout(() => {
        navigate('/mentor/session-recordings');
      }, 2000);

    } catch (error) {
      console.error('Upload failed:', error);
      setErrors({ submit: error.message || 'Failed to upload recording. Please try again.' });
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    navigate('/mentor/session-recordings');
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 'none' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Add New Session Recording
      </Typography>

      <Paper sx={{ p: 3, mt: 3, width: '100%' }}>
        {success && (
          <Alert severity="success" sx={{ mb: 3 }}>
            Session recording uploaded successfully! Redirecting to recordings list...
          </Alert>
        )}

        {errors.submit && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {errors.submit}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Basic Information */}
            <Box>
              <Typography variant="h6" gutterBottom>
                Recording Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Box>

            <TextField
              fullWidth
              label="Video Name"
              name="Video_Name"
              value={formData.Video_Name}
              onChange={handleInputChange}
              error={!!errors.Video_Name}
              helperText={errors.Video_Name}
              required
              placeholder="e.g., React Fundamentals - Session 1"
            />

            <TextField
              fullWidth
              label="Session ID"
              name="Session_ID"
              value={formData.Session_ID}
              onChange={handleInputChange}
              error={!!errors.Session_ID}
              helperText={errors.Session_ID || "Enter an active Session ID"}
              required
              placeholder="e.g., SES001"
            />

            <TextField
              fullWidth
              label="Batch ID"
              name="Batch_ID"
              value={formData.Batch_ID}
              onChange={handleInputChange}
              error={!!errors.Batch_ID}
              helperText={errors.Batch_ID || "Enter an active Batch ID"}
              required
              placeholder="e.g., BATCH001"
            />

            {/* File Upload */}
            <Box>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Recording File
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Box>

            <Box
              sx={{
                border: '2px dashed',
                borderColor: errors.recordingFile ? 'error.main' : 'grey.300',
                borderRadius: 2,
                p: 3,
                textAlign: 'center',
                cursor: 'pointer',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'action.hover'
                }
              }}
              onClick={() => document.getElementById('file-input').click()}
            >
              <input
                id="file-input"
                type="file"
                accept="video/*"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              
              <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              
              {formData.recordingFile ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    {formData.recordingFile.name}
                  </Typography>
                  <Chip
                    icon={<Storage />}
                    label={formatFileSize(formData.recordingFile.size)}
                    color="primary"
                    variant="outlined"
                  />
                </Box>
              ) : (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Click to select recording file
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Supported formats: MP4, WebM, OGG, AVI (Max: 2GB)
                  </Typography>
                </Box>
              )}
            </Box>
            
            {errors.recordingFile && (
              <Typography variant="caption" color="error" sx={{ display: 'block' }}>
                {errors.recordingFile}
              </Typography>
            )}

            {/* Upload Progress */}
            {uploading && (
              <Card sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Uploading Recording...
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={uploadProgress} 
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {uploadProgress}% complete
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Please don't close this page while uploading...
                  </Typography>
                </CardContent>
              </Card>
            )}

            {/* Action Buttons */}
            <Box display="flex" gap={2} justifyContent="flex-end" sx={{ mt: 3 }}>
              <Button
                variant="outlined"
                onClick={handleCancel}
                startIcon={<Cancel />}
                disabled={uploading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                startIcon={<Save />}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Save Recording'}
              </Button>
            </Box>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default MentorAddSessionRecording;