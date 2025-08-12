import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  IconButton,
  Card,
  CardContent,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Skeleton,
  Tooltip,
  Snackbar,
  Container,
  Fade,
  Slide,
  Zoom,
  Chip,
  Avatar,
  Stack,
  Divider
} from '@mui/material';
import {
  ArrowBack,
  Download,
  Edit,
  Delete,
  Share,
  Close,
  Save,
  Cancel,
  CheckCircle,
  ErrorOutline,
  ContentCopy,
  Visibility,
  InsertDriveFile,
  CloudDownload,
  OpenInNew,
  Schedule,
  Folder,
  Assignment,
  Description,
  Star,
  StarBorder
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import ConfirmDialog from '../../common/ConfirmDialog';
import { courseDocumentsAPI } from '../../../services/API/courseDocuments';

// Enhanced shimmer loading with blue theme
const ViewDocumentShimmer = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Fade in timeout={800}>
        <Box>
          {/* Header Shimmer with blue gradient */}
          <Box 
            display="flex" 
            alignItems="center" 
            mb={4}
            sx={{
              p: 3,
              borderRadius: 4,
              background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
              border: '1px solid #2196f3'
            }}
          >
            <Skeleton 
              variant="circular" 
              width={64} 
              height={64} 
              sx={{ 
                mr: 3,
                bgcolor: 'rgba(33, 150, 243, 0.2)'
              }} 
            />
            <Box sx={{ flexGrow: 1 }}>
              <Skeleton 
                variant="text" 
                width={350} 
                height={48} 
                sx={{ mb: 1, borderRadius: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }}
              />
              <Skeleton 
                variant="text" 
                width={250} 
                height={28} 
                sx={{ borderRadius: 1, bgcolor: 'rgba(33, 150, 243, 0.1)' }}
              />
            </Box>
            <Box display="flex" gap={2}>
              {Array.from({ length: 5 }).map((_, index) => (
                <Skeleton 
                  key={index} 
                  variant="rectangular" 
                  width={120} 
                  height={45} 
                  sx={{ 
                    borderRadius: 3,
                    bgcolor: 'rgba(33, 150, 243, 0.2)',
                    animation: `pulse 1.5s ease-in-out infinite ${index * 0.2}s`
                  }} 
                />
              ))}
            </Box>
          </Box>

          {/* Content shimmer with blue cards */}
          <Paper 
            sx={{ 
              p: 5, 
              borderRadius: 4, 
              background: 'linear-gradient(135deg, #ffffff 0%, #f8fafe 100%)',
              boxShadow: '0 24px 48px rgba(33, 150, 243, 0.15)',
              border: '1px solid rgba(33, 150, 243, 0.1)'
            }}
          >
            <Skeleton 
              variant="text" 
              width={400} 
              height={40} 
              sx={{ mb: 4, borderRadius: 2, bgcolor: 'rgba(33, 150, 243, 0.1)' }}
            />
            
            <Grid container spacing={3}>
              {Array.from({ length: 6 }).map((_, index) => (
                <Grid item xs={12} sm={6} lg={4} key={index}>
                  <Card sx={{ 
                    borderRadius: 3,
                    border: '2px solid #e3f2fd',
                    bgcolor: '#fafcff'
                  }}>
                    <CardContent>
                      <Skeleton 
                        variant="rectangular" 
                        width="100%" 
                        height={120} 
                        sx={{ 
                          borderRadius: 2,
                          bgcolor: 'rgba(33, 150, 243, 0.1)',
                          animation: `pulse 2s ease-in-out infinite ${index * 0.3}s`
                        }} 
                      />
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Box>
      </Fade>
    </Container>
  );
};

const MentorViewCourseDocument = () => {
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [editDialog, setEditDialog] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    title: ''
  });
  
  const navigate = useNavigate();
  const { id } = useParams();

  // Transform API response to component format
  const transformDocumentData = (apiDoc) => {
    if (!apiDoc) return null;
    
    return {
      batchId: apiDoc.Batch_ID || apiDoc.batchId,
      documentId: apiDoc.Document_ID || apiDoc.id,
      title: apiDoc.Document_Title ? apiDoc.Document_Title.replace(/"/g, '') : 'Untitled',
      path: apiDoc.Document_Path || apiDoc.path,
      uploadDateTime: apiDoc.Document_Upload_DateTime || apiDoc.uploadDate || apiDoc.createdAt,
      _original: apiDoc
    };
  };

  // Fetch document data
  const fetchDocument = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await courseDocumentsAPI.getById(id);
      console.log('API Response for document:', response);
      
      const documentData = response.data || response.document || response;
      
      if (documentData) {
        const transformedDoc = transformDocumentData(documentData);
        setDocument(transformedDoc);
      } else {
        setError('Document not found');
        setDocument(null);
      }
    } catch (error) {
      console.error('Error fetching document:', error);
      setError(error.message || 'Failed to load document');
      setDocument(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchDocument();
    }
  }, [id]);

  const handleView = () => {
    if (document.path && document.path.startsWith('http')) {
      window.open(document.path, '_blank');
      setSnackbar({
        open: true,
        message: '🔍 Opening document in new tab...',
        severity: 'success'
      });
    } else {
      setSnackbar({
        open: true,
        message: '❌ Document path not available for viewing',
        severity: 'error'
      });
    }
  };

  const handleEdit = () => {
    if (document) {
      setEditForm({
        title: document.title ? String(document.title) : ''
      });
      setEditDialog(true);
    }
  };

  const handleEditClose = () => {
    setEditDialog(false);
    setEditForm({
      title: ''
    });
  };

  const handleEditFormChange = (field) => (event) => {
    setEditForm(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleEditSubmit = async () => {
    try {
      setEditLoading(true);
      setError(null);
      
      // Ensure we have valid string values
      const titleValue = editForm.title ? String(editForm.title).trim() : '';
      
      // Validate required field
      if (!titleValue) {
        setError('Document title is required');
        setEditLoading(false);
        return;
      }
      
      const updateData = {
        Document_Title: `"${titleValue}"`
      };
      
      const response = await courseDocumentsAPI.update(document.documentId, updateData);
      
      const updatedDocument = {
        ...document,
        title: titleValue
      };
      
      setDocument(updatedDocument);
      setEditDialog(false);
      setSnackbar({
        open: true,
        message: '✨ Document title updated successfully!',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error updating document:', error);
      setError(error.message || 'Failed to update document');
      setSnackbar({
        open: true,
        message: '😞 Failed to update document',
        severity: 'error'
      });
    } finally {
      setEditLoading(false);
    }
  };

  const handleDelete = () => {
    setDeleteDialog(true);
  };

  const confirmDelete = async () => {
    try {
      setError(null);
      await courseDocumentsAPI.remove(document.documentId);
      
      setSnackbar({
        open: true,
        message: '🗑️ Document deleted successfully!',
        severity: 'success'
      });
      
      setTimeout(() => {
        navigate('/trainer/course-documents');
      }, 1500);
    } catch (error) {
      console.error('Error deleting document:', error);
      setError(error.message || 'Failed to delete document');
      setSnackbar({
        open: true,
        message: '😞 Failed to delete document',
        severity: 'error'
      });
    }
    setDeleteDialog(false);
  };

  const handleDownload = async () => {
    try {
      setError(null);
      
      if (document.path && document.path.startsWith('http')) {
        window.open(document.path, '_blank');
        setSnackbar({
          open: true,
          message: '📥 Download started!',
          severity: 'success'
        });
        return;
      }
      
      const response = await courseDocumentsAPI.viewDocument(document.documentId);
      
      if (response.url) {
        window.open(response.url, '_blank');
      } else if (response.blob) {
        const url = window.URL.createObjectURL(response.blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = document.title || 'document';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
      
      setSnackbar({
        open: true,
        message: '📥 Download started!',
        severity: 'success'
      });
    } catch (error) {
      console.error('Error downloading document:', error);
      setError(error.message || 'Failed to download document');
      setSnackbar({
        open: true,
        message: '😞 Failed to download document',
        severity: 'error'
      });
    }
  };

  const handleShare = () => {
    const documentUrl = `${window.location.origin}/trainer/course-documents/${id}`;
    navigator.clipboard.writeText(documentUrl).then(() => {
      setSnackbar({
        open: true,
        message: '📋 Document link copied to clipboard!',
        severity: 'success'
      });
    }).catch(() => {
      setSnackbar({
        open: true,
        message: '😞 Failed to copy link to clipboard',
        severity: 'error'
      });
    });
  };

  const handleCopyPath = () => {
    if (document.path) {
      navigator.clipboard.writeText(document.path).then(() => {
        setSnackbar({
          open: true,
          message: '📋 File path copied to clipboard!',
          severity: 'success'
        });
      }).catch(() => {
        setSnackbar({
          open: true,
          message: '😞 Failed to copy path to clipboard',
          severity: 'error'
        });
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'Not available';
    try {
      return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  const getFileIcon = () => {
    return <Description sx={{ fontSize: 40, color: '#1976d2' }} />;
  };

  if (loading) {
    return <ViewDocumentShimmer />;
  }

  if (error && !document) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Fade in timeout={600}>
          <Box>
            {/* Error Header */}
            <Paper
              sx={{
                p: 4,
                mb: 4,
                borderRadius: 4,
                background: 'linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%)',
                border: '2px solid #f44336',
                boxShadow: '0 8px 24px rgba(244, 67, 54, 0.2)'
              }}
            >
              <Box display="flex" alignItems="center">
                <IconButton 
                  onClick={() => navigate('/trainer/course-documents')} 
                  sx={{ 
                    mr: 3,
                    bgcolor: '#f44336',
                    color: 'white',
                    width: 56,
                    height: 56,
                    '&:hover': { 
                      bgcolor: '#d32f2f', 
                      transform: 'scale(1.05)' 
                    },
                    transition: 'all 0.3s ease',
                    boxShadow: '0 4px 12px rgba(244, 67, 54, 0.3)'
                  }}
                >
                  <ArrowBack />
                </IconButton>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#d32f2f', mb: 1 }}>
                    📄 Document Not Found
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    The requested document could not be located
                  </Typography>
                </Box>
              </Box>
            </Paper>
            
            <Alert 
              severity="error" 
              icon={<ErrorOutline />}
              sx={{ 
                borderRadius: 3,
                boxShadow: '0 8px 24px rgba(244,67,54,0.2)',
                fontSize: '1.1rem',
                border: '1px solid #f44336'
              }}
            >
              {error}
            </Alert>
          </Box>
        </Fade>
      </Container>
    );
  }

  if (!document) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Fade in timeout={600}>
          <Box>
            <Box display="flex" alignItems="center" mb={4}>
              <IconButton 
                onClick={() => navigate('/trainer/course-documents')} 
                sx={{ mr: 2 }}
              >
                <ArrowBack />
              </IconButton>
              <Typography variant="h4">📄 Document Not Found</Typography>
            </Box>
            <Alert severity="error" sx={{ borderRadius: 3 }}>
              The requested document could not be found.
            </Alert>
          </Box>
        </Fade>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Error Alert */}
      {error && (
        <Zoom in timeout={500}>
          <Alert 
            severity="error" 
            sx={{ 
              mb: 3, 
              borderRadius: 3, 
              boxShadow: '0 4px 12px rgba(244, 67, 54, 0.2)',
              border: '1px solid #f44336'
            }} 
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        </Zoom>
      )}

      {/* Enhanced Header with Blue Gradient */}
      <Fade in timeout={800}>
        <Paper
          sx={{
            p: 3,
            mb: 3,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 50%, #1565c0 100%)',
            color: 'white',
            boxShadow: '0 8px 24px rgba(33, 150, 243, 0.3)',
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'url("data:image/svg+xml,<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\'><circle cx=\'20\' cy=\'20\' r=\'1.5\' fill=\'white\' opacity=\'0.1\'/><circle cx=\'80\' cy=\'80\' r=\'1.5\' fill=\'white\' opacity=\'0.1\'/><circle cx=\'40\' cy=\'70\' r=\'1\' fill=\'white\' opacity=\'0.1\'/></svg>")',
              backgroundRepeat: 'repeat'
            }
          }}
        >
          <Box display="flex" alignItems="center" position="relative" zIndex={1}>
            <IconButton 
              onClick={() => navigate('/mentor/course-documents')} 
              sx={{ 
                mr: 2.5,
                bgcolor: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                width: 48,
                height: 48,
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                '&:hover': { 
                  bgcolor: 'rgba(255, 255, 255, 0.3)',
                  transform: 'translateY(-2px) scale(1.05)',
                  boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)'
                },
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
              <ArrowBack sx={{ fontSize: 24 }} />
            </IconButton>
            
            <Box sx={{ flexGrow: 1 }}>
              <Typography 
                variant="h5" 
                sx={{ 
                  fontWeight: 'bold',
                  mb: 0.5,
                  textShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
                }}
              >
                📄 Document Center
              </Typography>
              <Typography 
                variant="body1" 
                sx={{ 
                  fontWeight: 300,
                  opacity: 0.9,
                  textShadow: '0 1px 2px rgba(0, 0, 0, 0.2)'
                }}
              >
                Complete document management and viewing
              </Typography>
            </Box>
            
            <Stack direction="row" spacing={1.5}>
              <Tooltip title="View Document" arrow>
                <Button
                  variant="contained"
                  startIcon={<Visibility />}
                  onClick={handleView}
                  sx={{ 
                    bgcolor: 'rgba(255, 255, 255, 0.9)',
                    color: '#1976d2',
                    borderRadius: 2,
                    px: 2.5,
                    py: 1,
                    fontWeight: 'bold',
                    fontSize: '0.85rem',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
                    backdropFilter: 'blur(10px)',
                    '&:hover': { 
                      bgcolor: 'white',
                      transform: 'translateY(-1px)',
                      boxShadow: '0 6px 16px rgba(0, 0, 0, 0.3)'
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  View
                </Button>
              </Tooltip>
              
              <Tooltip title="Download Document" arrow>
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  onClick={handleDownload}
                  sx={{ 
                    borderColor: 'rgba(255, 255, 255, 0.7)',
                    color: 'white',
                    borderRadius: 2,
                    px: 2.5,
                    py: 1,
                    borderWidth: 1.5,
                    fontWeight: 'bold',
                    fontSize: '0.85rem',
                    backdropFilter: 'blur(10px)',
                    '&:hover': { 
                      borderColor: 'white',
                      bgcolor: 'rgba(255, 255, 255, 0.1)',
                      transform: 'translateY(-1px)',
                      borderWidth: 1.5
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  Download
                </Button>
              </Tooltip>
              
              <Tooltip title="Share Document" arrow>
                <Button
                  variant="outlined"
                  startIcon={<Share />}
                  onClick={handleShare}
                  sx={{ 
                    borderColor: 'rgba(255, 255, 255, 0.7)',
                    color: 'white',
                    borderRadius: 2,
                    px: 2.5,
                    py: 1,
                    borderWidth: 1.5,
                    fontWeight: 'bold',
                    fontSize: '0.85rem',
                    backdropFilter: 'blur(10px)',
                    '&:hover': { 
                      borderColor: 'white',
                      bgcolor: 'rgba(255, 255, 255, 0.1)',
                      transform: 'translateY(-1px)',
                      borderWidth: 1.5
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  Share
                </Button>
              </Tooltip>
              
              <Tooltip title="Edit Document" arrow>
                <Button
                  variant="contained"
                  startIcon={<Edit />}
                  onClick={handleEdit}
                  sx={{ 
                    bgcolor: 'rgba(255, 255, 255, 0.9)',
                    color: '#1976d2',
                    borderRadius: 2,
                    px: 2.5,
                    py: 1,
                    fontWeight: 'bold',
                    fontSize: '0.85rem',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
                    backdropFilter: 'blur(10px)',
                    '&:hover': { 
                      bgcolor: 'white',
                      transform: 'translateY(-1px)',
                      boxShadow: '0 6px 16px rgba(0, 0, 0, 0.3)'
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  Edit
                </Button>
              </Tooltip>
              
              <Tooltip title="Delete Document" arrow>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<Delete />}
                  onClick={handleDelete}
                  sx={{ 
                    borderColor: '#ff5252',
                    color: '#ff5252',
                    borderRadius: 2,
                    px: 2.5,
                    py: 1,
                    borderWidth: 1.5,
                    fontWeight: 'bold',
                    fontSize: '0.85rem',
                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    '&:hover': { 
                      borderColor: '#ff1744',
                      color: '#ff1744',
                      bgcolor: 'rgba(255, 255, 255, 0.2)',
                      transform: 'translateY(-1px)',
                      borderWidth: 1.5
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                  }}
                >
                  Delete
                </Button>
              </Tooltip>
            </Stack>
          </Box>
        </Paper>
      </Fade>

      {/* Main Document Information Card with Blue Theme */}
      <Slide in direction="up" timeout={1000}>
        <Paper 
          sx={{ 
            p: 4,
            borderRadius: 3,
            background: 'linear-gradient(135deg, #ffffff 0%, #f8fafe 50%, #f0f7ff 100%)',
            boxShadow: '0 12px 32px rgba(33, 150, 243, 0.15)',
            border: '1px solid rgba(33, 150, 243, 0.1)',
            position: 'relative',
            overflow: 'hidden',
            '&::before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '4px',
              background: 'linear-gradient(90deg, #2196f3 0%, #1976d2 50%, #1565c0 100%)'
            }
          }}
        >
          {/* Document Title Section */}
          <Box display="flex" alignItems="center" mb={4}>
            <Avatar 
              sx={{ 
                background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
                width: 64,
                height: 64,
                mr: 3,
                boxShadow: '0 8px 20px rgba(33, 150, 243, 0.3)',
                border: '3px solid white'
              }}
            >
              {getFileIcon()}
            </Avatar>
            <Box sx={{ flexGrow: 1 }}>
              <Typography 
                variant="h5" 
                sx={{ 
                  fontWeight: 'bold',
                  color: '#1976d2',
                  mb: 1.5,
                  textShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                }}
              >
                {document.title}
              </Typography>
              <Stack direction="row" spacing={1.5}>
                <Chip 
                  icon={<Description />}
                  label="Course Document"
                  sx={{ 
                    background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
                    color: '#1976d2',
                    fontWeight: 'bold',
                    fontSize: '0.8rem',
                    border: '1px solid #2196f3'
                  }}
                />
                <Chip 
                  icon={<StarBorder />}
                  label="Active"
                  variant="outlined"
                  sx={{ 
                    borderColor: '#2196f3',
                    color: '#1976d2',
                    fontWeight: 'bold',
                    fontSize: '0.8rem'
                  }}
                />
              </Stack>
            </Box>
          </Box>
          
          <Divider sx={{ mb: 3, borderColor: '#e3f2fd' }} />
          
          <Typography 
            variant="h6" 
            gutterBottom 
            sx={{ 
              fontWeight: 'bold',
              color: '#1976d2',
              mb: 3,
              display: 'flex',
              alignItems: 'center',
              gap: 1.5
            }}
          >
            <InsertDriveFile sx={{ color: '#2196f3', fontSize: 28 }} />
            Document Information
          </Typography>
          
          <Grid container spacing={3}>
            {/* Batch ID Card */}
            <Grid item xs={12} sm={6} lg={4}>
              <Zoom in timeout={600} style={{ transitionDelay: '100ms' }}>
                <Card 
                  sx={{ 
                    p: 3,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%)',
                    border: '1.5px solid #2196f3',
                    boxShadow: '0 6px 18px rgba(33, 150, 243, 0.2)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative',
                    overflow: 'hidden',
                    '&:hover': {
                      transform: 'translateY(-8px) scale(1.02)',
                      boxShadow: '0 12px 28px rgba(33, 150, 243, 0.3)'
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: -30,
                      right: -30,
                      width: 60,
                      height: 60,
                      background: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '50%'
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" mb={2}>
                    <Folder sx={{ color: '#1976d2', fontSize: 26, mr: 1.5 }} />
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: '#0d47a1',
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}
                    >
                      Batch ID
                    </Typography>
                  </Box>
                  <Typography 
                    variant="h5" 
                    sx={{ 
                      fontWeight: 'bold',
                      color: '#1976d2',
                      textShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                    }}
                  >
                    {document.batchId || 'N/A'}
                  </Typography>
                </Card>
              </Zoom>
            </Grid>

            {/* Document ID Card */}
            <Grid item xs={12} sm={6} lg={4}>
              <Zoom in timeout={600} style={{ transitionDelay: '200ms' }}>
                <Card 
                  sx={{ 
                    p: 3,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafe 50%, #e8f4fd 100%)',
                    border: '1.5px solid #2196f3',
                    boxShadow: '0 6px 18px rgba(33, 150, 243, 0.15)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative',
                    overflow: 'hidden',
                    '&:hover': {
                      transform: 'translateY(-8px) scale(1.02)',
                      boxShadow: '0 12px 28px rgba(33, 150, 243, 0.25)',
                      background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%)'
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: -30,
                      right: -30,
                      width: 60,
                      height: 60,
                      background: 'rgba(33, 150, 243, 0.05)',
                      borderRadius: '50%'
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" mb={2}>
                    <Assignment sx={{ color: '#2196f3', fontSize: 26, mr: 1.5 }} />
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: '#1976d2',
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}
                    >
                      Document ID
                    </Typography>
                  </Box>
                  <Typography 
                    variant="h5" 
                    sx={{ 
                      fontWeight: 'bold',
                      color: '#2196f3',
                      textShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                    }}
                  >
                    {document.documentId || 'N/A'}
                  </Typography>
                </Card>
              </Zoom>
            </Grid>

            {/* Document Title Card */}
            <Grid item xs={12} sm={6} lg={4}>
              <Zoom in timeout={600} style={{ transitionDelay: '300ms' }}>
                <Card 
                  sx={{ 
                    p: 3,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, #e8f4fd 0%, #d1e9fc 50%, #bbdefb 100%)',
                    border: '1.5px solid #42a5f5',
                    boxShadow: '0 6px 18px rgba(66, 165, 245, 0.2)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative',
                    overflow: 'hidden',
                    '&:hover': {
                      transform: 'translateY(-8px) scale(1.02)',
                      boxShadow: '0 12px 28px rgba(66, 165, 245, 0.3)'
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: -30,
                      right: -30,
                      width: 60,
                      height: 60,
                      background: 'rgba(255, 255, 255, 0.2)',
                      borderRadius: '50%'
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" mb={2}>
                    <Description sx={{ color: '#1976d2', fontSize: 26, mr: 1.5 }} />
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: '#0d47a1',
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}
                    >
                      Document Title
                    </Typography>
                  </Box>
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      fontWeight: 'bold',
                      color: '#1976d2',
                      wordBreak: 'break-word',
                      lineHeight: 1.3,
                      textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
                    }}
                  >
                    {document.title || 'Untitled'}
                  </Typography>
                </Card>
              </Zoom>
            </Grid>

            {/* Upload Date Time Card */}
            <Grid item xs={12} lg={6}>
              <Zoom in timeout={600} style={{ transitionDelay: '400ms' }}>
                <Card 
                  sx={{ 
                    p: 3,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, #f3f8ff 0%, #e8f2ff 50%, #ddeeff 100%)',
                    border: '1.5px solid #64b5f6',
                    boxShadow: '0 6px 18px rgba(100, 181, 246, 0.2)',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    position: 'relative',
                    overflow: 'hidden',
                    '&:hover': {
                      transform: 'translateY(-8px) scale(1.01)',
                      boxShadow: '0 12px 28px rgba(100, 181, 246, 0.3)'
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: -30,
                      right: -30,
                      width: 60,
                      height: 60,
                      background: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '50%'
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" mb={2}>
                    <Schedule sx={{ color: '#1976d2', fontSize: 26, mr: 1.5 }} />
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: '#0d47a1',
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}
                    >
                      Upload Date & Time
                    </Typography>
                  </Box>
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      fontWeight: 'medium',
                      color: '#1976d2',
                      textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)'
                    }}
                  >
                    {formatDateTime(document.uploadDateTime)}
                  </Typography>
                </Card>
              </Zoom>
            </Grid>

            {/* Document Path Card */}
            <Grid item xs={12} lg={6}>
              <Zoom in timeout={600} style={{ transitionDelay: '500ms' }}>
                <Card 
                  sx={{ 
                    p: 3,
                    borderRadius: 3,
                    background: 'linear-gradient(135deg, #ffffff 0%, #f5f9ff 50%, #eef7ff 100%)',
                    border: '1.5px solid #90caf9',
                    boxShadow: '0 6px 18px rgba(144, 202, 249, 0.2)',
                    position: 'relative',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    overflow: 'hidden',
                    '&:hover': {
                      transform: 'translateY(-8px) scale(1.01)',
                      boxShadow: '0 12px 28px rgba(144, 202, 249, 0.3)',
                      background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%)'
                    },
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: -30,
                      right: -30,
                      width: 60,
                      height: 60,
                      background: 'rgba(33, 150, 243, 0.05)',
                      borderRadius: '50%'
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" mb={2}>
                    <OpenInNew sx={{ color: '#1976d2', fontSize: 26, mr: 1.5 }} />
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: '#0d47a1',
                        fontWeight: 'bold',
                        fontSize: '0.9rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}
                    >
                      Document Path
                    </Typography>
                  </Box>
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      wordBreak: 'break-all',
                      color: '#1976d2',
                      pr: 5,
                      lineHeight: 1.4,
                      fontFamily: 'monospace',
                      bgcolor: 'rgba(33, 150, 243, 0.05)',
                      p: 1.5,
                      borderRadius: 2,
                      border: '1px solid rgba(33, 150, 243, 0.1)'
                    }}
                  >
                    {document.path || 'Path not available'}
                  </Typography>
                  <Tooltip title="Copy file path" arrow>
                    <IconButton 
                      onClick={handleCopyPath}
                      sx={{ 
                        position: 'absolute',
                        top: 12,
                        right: 12,
                        bgcolor: '#2196f3',
                        color: 'white',
                        width: 32,
                        height: 32,
                        boxShadow: '0 3px 8px rgba(33, 150, 243, 0.3)',
                        '&:hover': { 
                          bgcolor: '#1976d2',
                          transform: 'scale(1.1)',
                          boxShadow: '0 4px 12px rgba(33, 150, 243, 0.4)'
                        },
                        transition: 'all 0.3s ease'
                      }}
                      size="small"
                    >
                      <ContentCopy fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Card>
              </Zoom>
            </Grid>
          </Grid>
        </Paper>
      </Slide>

      {/* Enhanced Edit Modal with Blue Theme */}
      <Dialog 
        open={editDialog} 
        onClose={handleEditClose}
        TransitionComponent={Slide}
        TransitionProps={{ direction: "up" }}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 4,
            boxShadow: '0 24px 48px rgba(33, 150, 243, 0.2)',
            background: 'linear-gradient(135deg, #ffffff 0%, #f8fafe 100%)',
            border: '1px solid rgba(33, 150, 243, 0.1)'
          }
        }}
      >
        <DialogTitle
          sx={{
            background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
            color: 'white',
            position: 'relative',
            py: 3,
            borderRadius: '16px 16px 0 0'
          }}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={2}>
              <Edit sx={{ fontSize: 32 }} />
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                ✏️ Edit Document Title
              </Typography>
            </Box>
            <IconButton 
              onClick={handleEditClose} 
              sx={{ 
                color: 'white',
                bgcolor: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(10px)',
                '&:hover': { 
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  transform: 'scale(1.1)'
                }
              }}
              disabled={editLoading}
            >
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers sx={{ p: 4 }}>
          <Typography 
            variant="body1" 
            color="text.secondary" 
            sx={{ 
              mb: 4, 
              fontSize: '1.1rem',
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}
          >
            📝 Update the document title with a descriptive name
          </Typography>
          
          <TextField
            fullWidth
            label="Document Title"
            value={editForm.title}
            onChange={handleEditFormChange('title')}
            variant="outlined"
            required
            disabled={editLoading}
            helperText="Enter a clear and descriptive title for this document"
            sx={{ 
              mb: 4,
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
                bgcolor: '#fafcff',
                '&:hover fieldset': {
                  borderColor: '#2196f3'
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#2196f3',
                  borderWidth: 2
                }
              },
              '& .MuiInputLabel-root.Mui-focused': {
                color: '#2196f3'
              }
            }}
          />
          
          <Card 
            sx={{ 
              p: 3,
              background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)',
              borderRadius: 3,
              border: '2px solid #2196f3'
            }}
          >
            <Typography 
              variant="subtitle1" 
              gutterBottom 
              sx={{ 
                fontWeight: 'bold',
                color: '#1976d2',
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                mb: 2
              }}
            >
              <Assignment sx={{ color: '#1976d2' }} />
              Current Document Information:
            </Typography>
            <Box sx={{ 
              bgcolor: 'rgba(255, 255, 255, 0.7)', 
              p: 2, 
              borderRadius: 2,
              border: '1px solid rgba(33, 150, 243, 0.2)'
            }}>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.8 }}>
                📄 <strong>Document ID:</strong> {document.documentId}
                <br />
                🎓 <strong>Batch ID:</strong> {document.batchId}
                <br />
                📅 <strong>Upload Date:</strong> {formatDateTime(document.uploadDateTime)}
              </Typography>
            </Box>
          </Card>
        </DialogContent>
        
        <DialogActions sx={{ p: 3, bgcolor: '#f8fafe' }}>
          <Stack direction="row" spacing={3} sx={{ width: '100%' }}>
            <Button 
              onClick={handleEditClose} 
              variant="outlined"
              disabled={editLoading}
              startIcon={<Cancel />}
              sx={{ 
                flex: 1,
                borderRadius: 3,
                py: 1.5,
                borderWidth: 2,
                borderColor: '#90caf9',
                color: '#1976d2',
                '&:hover': {
                  borderWidth: 2,
                  borderColor: '#2196f3',
                  bgcolor: '#e3f2fd'
                }
              }}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleEditSubmit} 
              variant="contained"
              disabled={editLoading || !editForm.title?.trim()}
              startIcon={editLoading ? <CircularProgress size={20} color="inherit" /> : <Save />}
              sx={{
                flex: 1,
                borderRadius: 3,
                py: 1.5,
                background: 'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
                boxShadow: '0 8px 16px rgba(33, 150, 243, 0.3)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
                  boxShadow: '0 12px 24px rgba(33, 150, 243, 0.4)',
                  transform: 'translateY(-2px)'
                },
                '&:disabled': {
                  background: '#e0e0e0',
                  color: '#9e9e9e'
                },
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
              }}
            >
              {editLoading ? 'Saving...' : '✨ Save Changes'}
            </Button>
          </Stack>
        </DialogActions>
      </Dialog>

      {/* Enhanced Delete Confirmation */}
      <ConfirmDialog
        open={deleteDialog}
        onClose={() => setDeleteDialog(false)}
        onConfirm={confirmDelete}
        title="🗑️ Delete Document"
        message={
          <Box>
            <Typography gutterBottom sx={{ fontSize: '1.1rem', mb: 2 }}>
              Are you sure you want to delete this document?
            </Typography>
            <Alert 
              severity="warning" 
              sx={{ 
                borderRadius: 3,
                border: '1px solid #ff9800',
                '& .MuiAlert-message': {
                  fontSize: '1rem'
                }
              }}
            >
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                <strong>"{document?.title}"</strong> will be permanently deleted. This action cannot be undone.
              </Typography>
            </Alert>
          </Box>
        }
      />

      {/* Enhanced Success/Error Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        TransitionComponent={Slide}
        TransitionProps={{ direction: 'up' }}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity} 
          sx={{ 
            width: '100%',
            borderRadius: 3,
            boxShadow: '0 8px 24px rgba(33, 150, 243, 0.2)',
            fontSize: '1.1rem',
            border: snackbar.severity === 'success' 
              ? '1px solid #4caf50' 
              : '1px solid #f44336',
            '& .MuiAlert-icon': {
              fontSize: '1.5rem'
            }
          }}
          icon={snackbar.severity === 'success' ? <CheckCircle /> : <ErrorOutline />}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default MentorViewCourseDocument;