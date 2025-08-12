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
  TablePagination,
} from '@mui/material';
import {
  Visibility,
  Search,
  PlayArrow,
  Close,
  VideoLibrary,
  Refresh,
  Fullscreen,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Import the API service
import { sessionRecordingsAPI } from '../../../services/API/sessionrecordings';

// Shimmer Loading Component for Session Recordings
const SessionRecordingsShimmer = ({ rows = 6 }) => {
  const shimmerRows = Array.from({ length: rows }, (_, index) => index);

  return (
    <Box>
      {/* Header Shimmer */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Skeleton variant="text" width={250} height={48} />
        <Skeleton variant="rectangular" width={160} height={40} sx={{ borderRadius: 1 }} />
      </Box>

      {/* Search and Filter Shimmer */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" gap={2} alignItems="center">
          <Skeleton variant="rectangular" width={400} height={40} sx={{ borderRadius: 1 }} />
          <Skeleton variant="rectangular" width={120} height={40} sx={{ borderRadius: 1 }} />
          <Skeleton variant="rectangular" width={100} height={40} sx={{ borderRadius: 1 }} />
        </Box>
      </Paper>

      {/* Table Shimmer */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><Skeleton variant="text" width={150} /></TableCell>
              <TableCell><Skeleton variant="text" width={100} /></TableCell>
              <TableCell><Skeleton variant="text" width={80} /></TableCell>
              <TableCell><Skeleton variant="text" width={80} /></TableCell>
              <TableCell><Skeleton variant="text" width={120} /></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {shimmerRows.map((index) => (
              <TableRow key={index}>
                <TableCell>
                  <Box>
                    <Skeleton variant="text" width={180} height={20} />
                    <Skeleton variant="text" width={120} height={16} />
                  </Box>
                </TableCell>
                <TableCell><Skeleton variant="text" width={140} /></TableCell>
                <TableCell><Skeleton variant="text" width={80} /></TableCell>
                <TableCell><Skeleton variant="text" width={70} /></TableCell>
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

      <Box display="flex" justifyContent="center" alignItems="center" mt={2}>
        <Typography variant="body2" color="text.secondary">
          Loading session recordings...
        </Typography>
      </Box>
    </Box>
  );
};

// Enhanced Video Player Modal Component with better error handling
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

const StudentSessionRecordingsList= () => {
  const navigate = useNavigate();
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
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

  // Fetch recordings from API
  useEffect(() => {
    fetchRecordings();
  }, []);

  const fetchRecordings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await sessionRecordingsAPI.getAll();
      
      console.log('Fetched recordings:', response);
      
      // Handle response based on your API structure
      if (response && Array.isArray(response)) {
        setRecordings(response);
      } else if (response && response.data && Array.isArray(response.data)) {
        setRecordings(response.data);
      } else {
        setRecordings([]);
      }
    } catch (error) {
      console.error('Error fetching recordings:', error);
      setError('Failed to load session recordings. Please try again.');
      setSnackbar({
        open: true,
        message: 'Failed to load session recordings',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (event) => {
    const newSearchTerm = event.target.value;
    setSearchTerm(newSearchTerm);
    setPage(0);
  };

  const handleRefresh = async () => {
    await fetchRecordings();
    setSnackbar({
      open: true,
      message: 'Session recordings refreshed successfully',
      severity: 'success'
    });
  };

  const handleView = (recordingId) => {
    navigate(`/student/session-recordings/view/${recordingId}`);
  };

  // Enhanced handlePlay function using direct URL
  const handlePlay = async (recording) => {
    try {
      setVideoPlayer(prev => ({ ...prev, loading: true }));
      
      setSnackbar({
        open: true,
        message: 'Loading video...',
        severity: 'info'
      });

      console.log('🎥 Playing recording:', recording);
      
      // Use the direct video URL pattern that works in your browser
      const videoUrl = `http://192.168.48.33:8000/api/trainer/video/stream-direct/${recording.id}`;
      
      console.log('🚀 Using direct video URL:', videoUrl);
      
      // Open the video player immediately
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

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Helper function to safely access properties
  const safeGet = (obj, primaryField, alternateField = null, defaultValue = '') => {
    if (!obj) return defaultValue;
    
    // Try primary field first
    if (obj[primaryField] !== undefined && obj[primaryField] !== null) {
      return obj[primaryField];
    }
    
    // Try alternate field if provided
    if (alternateField && obj[alternateField] !== undefined && obj[alternateField] !== null) {
      return obj[alternateField];
    }
    
    return defaultValue;
  };

  // Helper function to extract filename from path
  const getFileName = (filePath) => {
    if (!filePath) return 'N/A';
    const parts = filePath.split('\\');
    return parts[parts.length - 1] || filePath;
  };

  // Updated Play button rendering function
  const renderPlayButton = (recording) => (
    <Tooltip title="Play Recording">
      <IconButton 
        size="small" 
        color="primary"
        onClick={() => handlePlay(recording)}
        disabled={videoPlayer.loading}
      >
        {videoPlayer.loading ? (
          <CircularProgress size={20} />
        ) : (
          <PlayArrow />
        )}
      </IconButton>
    </Tooltip>
  );

  const filteredRecordings = recordings.filter(recording => {
    if (!recording) return false;
    
    const videoName = safeGet(recording, 'Video_Name', '').toLowerCase();
    const batchId = safeGet(recording, 'Batch_ID', '').toString().toLowerCase();
    const sessionId = safeGet(recording, 'Session_ID', '').toString().toLowerCase();
    const searchLower = searchTerm.toLowerCase();
    
    const matchesSearch = videoName.includes(searchLower) || 
                         batchId.includes(searchLower) || 
                         sessionId.includes(searchLower);
    return matchesSearch;
  });

  if (loading) {
    return <SessionRecordingsShimmer rows={8} />;
  }

  if (error && recordings.length === 0) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={fetchRecordings} startIcon={<Refresh />}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <VideoLibrary sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Session Recordings
          </Typography>
        </Box>
      </Box>

      {/* Search Controls */}
      <Paper sx={{ p: 2, mb: 3, borderRadius: 2, boxShadow: 2 }}>
        <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
          <TextField
            placeholder="Search by video name, batch ID, or session ID..."
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={handleSearch}
            InputProps={{
              startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            sx={{ flexGrow: 1, minWidth: 300 }}
          />
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* Recordings Table */}
      <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Video Name</TableCell>
              <TableCell>Batch ID</TableCell>
              <TableCell>Session ID</TableCell>
              <TableCell>Video Path</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRecordings.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Alert severity="info" sx={{ m: 2 }}>
                    No session recordings found. {searchTerm && "Try adjusting your search criteria."}
                  </Alert>
                </TableCell>
              </TableRow>
            ) : (
              filteredRecordings
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((recording) => (
                  <TableRow key={recording.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2" fontWeight="medium">
                          {safeGet(recording, 'Video_Name', 'Untitled Recording')}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          ID: {recording.id}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={safeGet(recording, 'Batch_ID', 'N/A')} 
                        color="primary"
                        variant="outlined"
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={safeGet(recording, 'Session_ID', 'N/A')} 
                        color="secondary"
                        variant="outlined"
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title={safeGet(recording, 'Video_Path', 'N/A')}>
                        <Typography variant="body2" sx={{ 
                          maxWidth: 200, 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {getFileName(safeGet(recording, 'Video_Path', 'N/A'))}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    <TableCell align="center">
                      <Box display="flex" gap={0.5} justifyContent="center">
                        {renderPlayButton(recording)}
                        
                        <Tooltip title="View Details">
                          <IconButton 
                            size="small" 
                            color="info"
                            onClick={() => handleView(recording.id)}
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
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={filteredRecordings.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>

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
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity} 
          sx={{ width: '100%' }}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default StudentSessionRecordingsList;