import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  Divider,
  IconButton,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Skeleton,
  CircularProgress,
  Slide,
  Snackbar
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  VolumeUp,
  Fullscreen,
  Person,
  Schedule,
  Visibility,
  Storage,
  Tag,
  School,
  ArrowBack,
  VideoLibrary,
  Close,
  Refresh
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';

// Import your API service
import { sessionRecordingsAPI } from '../../../services/API/sessionrecordings';

// Shimmer Loading Component for View Session Recording
const ViewSessionRecordingShimmer = () => {
  return (
    <Box>
      {/* Header Shimmer */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box flex={1} mr={3}>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <Skeleton variant="circular" width={40} height={40} />
            <Skeleton variant="text" width="60%" height={48} />
          </Box>
          <Box display="flex" gap={1} alignItems="center" flexWrap="wrap">
            <Skeleton variant="rectangular" width={140} height={32} sx={{ borderRadius: 16 }} />
            <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 12 }} />
            <Skeleton variant="rectangular" width={70} height={24} sx={{ borderRadius: 12 }} />
          </Box>
        </Box>
        
        <Box display="flex" gap={1}>
          <Skeleton variant="rectangular" width={120} height={36} sx={{ borderRadius: 1 }} />
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Video Player Shimmer */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 0, overflow: 'hidden', borderRadius: 2 }}>
            <Box
              sx={{
                position: 'relative',
                width: '100%',
                paddingTop: '56.25%', // 16:9 aspect ratio
                bgcolor: 'grey.200',
                borderRadius: 1
              }}
            >
              <Skeleton
                variant="rectangular"
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                }}
              />
              
              {/* Play button shimmer */}
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)'
                }}
              >
                <Skeleton variant="circular" width={80} height={80} />
              </Box>
              
              {/* Video controls shimmer */}
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  bgcolor: 'rgba(0,0,0,0.1)',
                  p: 2,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2
                }}
              >
                <Skeleton variant="circular" width={32} height={32} />
                <Skeleton variant="text" width={100} />
                <Box sx={{ flexGrow: 1 }} />
                <Skeleton variant="circular" width={32} height={32} />
                <Skeleton variant="circular" width={32} height={32} />
              </Box>
            </Box>
          </Paper>
          
          {/* Recording Details Shimmer */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Skeleton variant="text" width={120} height={32} sx={{ mb: 2 }} />
              <Skeleton variant="text" width="100%" height={20} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="90%" height={20} sx={{ mb: 1 }} />
              <Skeleton variant="text" width="70%" height={20} sx={{ mb: 2 }} />
              
              <Divider sx={{ my: 2 }} />
              
              <Grid container spacing={2}>
                {Array.from({ length: 4 }).map((_, index) => (
                  <Grid item xs={6} sm={3} key={index}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Skeleton variant="circular" width={24} height={24} />
                      <Box>
                        <Skeleton variant="text" width={60} height={16} />
                        <Skeleton variant="text" width={80} height={20} />
                      </Box>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar Shimmer */}
        <Grid item xs={12} lg={4}>
          {/* Recording Info Shimmer */}
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Skeleton variant="text" width={180} height={32} sx={{ mb: 2 }} />
              <Box display="flex" flexDirection="column" gap={2}>
                {Array.from({ length: 4 }).map((_, index) => (
                  <Box key={index}>
                    <Skeleton variant="text" width={100} height={16} sx={{ mb: 0.5 }} />
                    <Skeleton variant="text" width={150} height={20} />
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Quick Actions Shimmer */}
          <Card>
            <CardContent>
              <Skeleton variant="text" width={160} height={32} sx={{ mb: 2 }} />
              <Box display="flex" flexDirection="column" gap={1}>
                <Skeleton variant="rectangular" width="100%" height={36} sx={{ borderRadius: 1 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

// Enhanced Video Player Modal Component
const VideoPlayerModal = ({ open, onClose, videoUrl, videoTitle, recording }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  
  // Reset states when modal opens
  useEffect(() => {
    if (open && videoUrl) {
      setLoading(true);
      setError(null);
      setRetryCount(0);
    }
  }, [open, videoUrl]);
  
  const handleVideoLoad = () => {
    console.log('Video loaded successfully');
    setLoading(false);
    setError(null);
  };
  
  const handleVideoError = (e) => {
    console.error('Video loading error:', e);
    setLoading(false);
    setError('Failed to load video. Please check if the video file is accessible.');
  };

  const handleVideoCanPlay = () => {
    console.log('Video can start playing');
    setLoading(false);
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    setLoading(true);
    setError(null);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          maxHeight: '90vh',
          bgcolor: '#000'
        }
      }}
    >
      <DialogTitle
        sx={{
          background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
          color: 'white',
          position: 'relative',
          py: 2
        }}
      >
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <PlayArrow />
            <Box>
              <Typography variant="h6" noWrap>
                {videoTitle || 'Session Recording'}
              </Typography>
              {recording && (
                <Typography variant="body2" sx={{ opacity: 0.8 }}>
                  Batch: {recording.Batch_ID} | Session: {recording.Session_ID} | ID: {recording.id}
                </Typography>
              )}
            </Box>
          </Box>
          <IconButton 
            onClick={onClose} 
            sx={{ color: 'white' }}
          >
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent sx={{ p: 0, bgcolor: '#000', position: 'relative', minHeight: '300px' }}>
        {loading && (
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            minHeight="300px"
            color="white"
          >
            <CircularProgress color="primary" size={60} />
            <Typography sx={{ mt: 2, color: 'white' }}>
              Loading video...
            </Typography>
            {videoUrl && (
              <Typography variant="caption" sx={{ mt: 1, color: 'grey.400', textAlign: 'center' }}>
                {videoUrl.length > 60 ? `${videoUrl.substring(0, 60)}...` : videoUrl}
              </Typography>
            )}
          </Box>
        )}
        
        {error && (
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            minHeight="300px"
            p={3}
          >
            <Alert 
              severity="error" 
              sx={{ width: '100%', mb: 2 }}
              action={
                <Button color="inherit" size="small" onClick={handleRetry}>
                  Retry
                </Button>
              }
            >
              {error}
            </Alert>
            
            {recording && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1, width: '100%' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Video Details:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Name:</strong> {recording.Video_Name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Path:</strong> {recording.Video_Path}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Attempted URL:</strong> {videoUrl}
                </Typography>
              </Box>
            )}
          </Box>
        )}
        
        {videoUrl && !error && (
          <video
            key={`${videoUrl}-${retryCount}`} // Force re-render on retry
            controls
            autoPlay
            style={{
              width: '100%',
              height: 'auto',
              maxHeight: '70vh',
              backgroundColor: '#000',
              display: loading ? 'none' : 'block'
            }}
            onLoadedData={handleVideoLoad}
            onCanPlay={handleVideoCanPlay}
            onError={handleVideoError}
            controlsList="nodownload"
            preload="metadata"
          >
            <source src={videoUrl} type="video/mp4" />
            <source src={videoUrl} type="video/webm" />
            <source src={videoUrl} type="video/ogg" />
            <source src={videoUrl} type="video/avi" />
            <source src={videoUrl} type="video/mov" />
            Your browser does not support the video tag.
          </video>
        )}
      </DialogContent>
      
      <DialogActions sx={{ bgcolor: '#f5f5f5', px: 3, py: 2 }}>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
        {videoUrl && !error && (
          <Button
            href={videoUrl}
            target="_blank"
            rel="noopener noreferrer"
            variant="contained"
            startIcon={<Fullscreen />}
            sx={{
              background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)'
            }}
          >
            Open in New Tab
          </Button>
        )}
        {error && (
          <Button
            onClick={handleRetry}
            variant="contained"
            startIcon={<Refresh />}
            color="warning"
          >
            Retry Loading
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

// Transition component for modal
const Transition = React.forwardRef(function Transition(props, ref) {
  return <Slide direction="up" ref={ref} {...props} />;
});

const StudentViewSessionRecording = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [recording, setRecording] = useState(null);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState(null);
  
  // Video Player Modal States
  const [videoPlayer, setVideoPlayer] = useState({
    open: false,
    videoUrl: null,
    videoTitle: '',
    recording: null,
    loading: false
  });
  
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Fetch recording data from API
  useEffect(() => {
    fetchRecording();
  }, [id]);

  const fetchRecording = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Fetching recording with ID:', id);
      const response = await sessionRecordingsAPI.getById(id);
      
      console.log('API Response for getById:', response);
      
      if (response) {
        setRecording(response);
      } else {
        setError('Recording not found');
      }
    } catch (error) {
      console.error('Error fetching recording:', error);
      setError('Failed to load recording. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/student/session-recordings');
  };

  const handlePlay = async () => {
    try {
      setVideoPlayer(prev => ({ ...prev, loading: true }));
      
      console.log('🎥 Playing recording:', recording);
      
      // Use the direct stream URL that works from your SessionRecordingsList
      const videoUrl = `http://192.168.48.33:8000/api/trainer/video/stream-direct/${recording.id}`;
      
      console.log('🚀 Using direct video URL:', videoUrl);
      
      // Open the video player
      setVideoPlayer({
        open: true,
        videoUrl,
        videoTitle: recording.Video_Name || 'Session Recording',
        recording,
        loading: false
      });
      
      setSnackbar({
        open: true,
        message: 'Video player opened successfully!',
        severity: 'success'
      });
      
    } catch (error) {
      console.error('❌ Error playing video:', error);
      
      setVideoPlayer(prev => ({ ...prev, loading: false }));
      
      setSnackbar({
        open: true,
        message: `Failed to load video: ${error.message}`,
        severity: 'error'
      });
    }
  };

  const handleCloseVideoPlayer = () => {
    setVideoPlayer({
      open: false,
      videoUrl: null,
      videoTitle: '',
      recording: null,
      loading: false
    });
  };

  const togglePlay = () => {
    setPlaying(!playing);
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Helper function to extract filename from path
  const getFileName = (filePath) => {
    if (!filePath) return 'N/A';
    const parts = filePath.split('\\');
    return parts[parts.length - 1] || filePath;
  };

  // Helper function to get file size from path (mock implementation)
  const getFileSize = (filePath) => {
    // Since we don't have actual file size from API, return a placeholder
    return 'Unknown';
  };

  // Helper function to format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (error) {
      return 'N/A';
    }
  };

  // Show shimmer while loading
  if (loading) {
    return <ViewSessionRecordingShimmer />;
  }

  if (error || !recording) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || 'Recording not found or you don\'t have permission to view it.'}
        </Alert>
        <Button variant="contained" onClick={handleBack} startIcon={<ArrowBack />}>
          Back to Recordings
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header with Back Button - View Only */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box>
          <Box display="flex" alignItems="center" gap={2} mb={2}>
            <IconButton 
              onClick={handleBack}
              sx={{ 
                bgcolor: 'primary.main',
                color: 'white',
                '&:hover': { bgcolor: 'primary.dark' }
              }}
            >
              <ArrowBack />
            </IconButton>
            <Typography variant="h4" component="h1">
              {recording.Video_Name || 'Session Recording'}
            </Typography>
          </Box>
          <Box display="flex" gap={1} alignItems="center" flexWrap="wrap">
            <Chip 
              icon={<School />}
              label={`Batch ${recording.Batch_ID}`} 
              color="primary" 
              variant="outlined" 
            />
            <Chip 
              label={`Session ${recording.Session_ID}`} 
              color="secondary"
              size="small"
            />
            <Chip 
              label={`ID: ${recording.id}`} 
              color="default"
              size="small"
            />
            <Chip 
              icon={<Visibility />}
              label="View Only" 
              color="info"
              size="small"
            />
          </Box>
        </Box>
        
        {/* Only Play Video Button */}
        <Box display="flex" gap={1}>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            onClick={handlePlay}
            sx={{
              background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #1976D2 30%, #2196F3 90%)'
              }
            }}
          >
            Play Video
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Video Player */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 0, overflow: 'hidden' }}>
            <Box
              sx={{
                position: 'relative',
                width: '100%',
                paddingTop: '56.25%', // 16:9 aspect ratio
                bgcolor: 'black',
                borderRadius: 1,
                cursor: 'pointer'
              }}
              onClick={handlePlay}
            >
              {/* Video placeholder - replace with actual video player */}
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                <IconButton
                  sx={{ 
                    color: 'white', 
                    fontSize: '4rem',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
                  }}
                >
                  <PlayArrow sx={{ fontSize: '4rem' }} />
                </IconButton>
              </Box>
              
              {/* Video info overlay */}
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  bgcolor: 'rgba(0,0,0,0.7)',
                  color: 'white',
                  p: 2,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2
                }}
              >
                <Typography variant="body2">
                  Click to play video
                </Typography>
                <Box sx={{ flexGrow: 1 }} />
                <Typography variant="body2">
                  {getFileName(recording.Video_Path)}
                </Typography>
              </Box>
            </Box>
          </Paper>
          
          {/* Recording Details */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recording Details
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Session recording for Batch {recording.Batch_ID}, Session {recording.Session_ID}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <VideoLibrary color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Video Name
                      </Typography>
                      <Typography variant="body2">
                        {recording.Video_Name || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Storage color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        File Name
                      </Typography>
                      <Typography variant="body2">
                        {getFileName(recording.Video_Path)}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <School color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Batch ID
                      </Typography>
                      <Typography variant="body2">
                        {recording.Batch_ID || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Schedule color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Session ID
                      </Typography>
                      <Typography variant="body2">
                        {recording.Session_ID || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          {/* Recording Info */}
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recording Information
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Recording ID
                  </Typography>
                  <Typography variant="body2">
                    {recording.id}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Video Path
                  </Typography>
                  <Typography variant="body2" sx={{ 
                    wordBreak: 'break-all',
                    fontSize: '0.8rem'
                  }}>
                    {recording.Video_Path || 'N/A'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Batch Information
                  </Typography>
                  <Typography variant="body2">
                    Batch {recording.Batch_ID}, Session {recording.Session_ID}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    File Name
                  </Typography>
                  <Typography variant="body2">
                    {getFileName(recording.Video_Path)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* Quick Actions - View Only */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <Button
                  variant="contained"
                  startIcon={<PlayArrow />}
                  onClick={handlePlay}
                  fullWidth
                  sx={{
                    background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                    '&:hover': {
                      background: 'linear-gradient(45deg, #1976D2 30%, #2196F3 90%)'
                    }
                  }}
                >
                  Play Video
                </Button>
                <Alert severity="info" sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    You can only view this recording. Editing and downloading are not available.
                  </Typography>
                </Alert>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Video Player Modal */}
      <VideoPlayerModal
        open={videoPlayer.open}
        onClose={handleCloseVideoPlayer}
        videoUrl={videoPlayer.videoUrl}
        videoTitle={videoPlayer.videoTitle}
        recording={videoPlayer.recording}
      />

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

export default StudentViewSessionRecording;