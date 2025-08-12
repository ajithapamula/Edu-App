import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  CircularProgress,
  Skeleton,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Add,
  Visibility,
  Edit,
  Delete,
  Download,
  Refresh,
  Close,
  Upload
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ConfirmDialog from '../../common/ConfirmDialog';
import { courseDocumentsAPI } from '../../../services/API/courseDocuments';

// Shimmer Loading Component
const CourseDocumentsShimmer = ({ rows = 8 }) => {
  const shimmerRows = Array.from({ length: rows }, (_, index) => index);

  return (
    <Box>
      {/* Header Shimmer */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Skeleton variant="text" width={200} height={40} />
        <Skeleton variant="rectangular" width={150} height={36} sx={{ borderRadius: 1 }} />
      </Box>

      {/* Filters Shimmer */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" gap={2} alignItems="center">
          <Skeleton variant="rectangular" width={300} height={40} sx={{ borderRadius: 1 }} />
          <Skeleton variant="rectangular" width={120} height={40} sx={{ borderRadius: 1 }} />
        </Box>
      </Paper>

      {/* Table Shimmer */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><Skeleton variant="text" width={80} /></TableCell>
              <TableCell><Skeleton variant="text" width={100} /></TableCell>
              <TableCell><Skeleton variant="text" width={120} /></TableCell>
              <TableCell><Skeleton variant="text" width={150} /></TableCell>
              <TableCell><Skeleton variant="text" width={100} /></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {shimmerRows.map((index) => (
              <TableRow key={index}>
                <TableCell>
                  <Skeleton variant="text" width={20} />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width={20} />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width={150} />
                </TableCell>
                <TableCell>
                  <Skeleton variant="text" width={120} />
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="circular" width={32} height={32} />
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination Shimmer */}
      <Box display="flex" justifyContent="flex-end" mt={2}>
        <Skeleton variant="text" width={200} height={40} />
      </Box>

      {/* Loading Message */}
      <Box display="flex" justifyContent="center" alignItems="center" mt={2}>
        <Typography variant="body2" color="text.secondary">
          Loading course documents...
        </Typography>
      </Box>
    </Box>
  );
};

const CourseDocumentsList = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, documentId: null });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Enhanced Edit Modal States
  const [editDialog, setEditDialog] = useState({ open: false, document: null });
  const [editForm, setEditForm] = useState({
    title: '',
    batchId: '',
    file: null
  });
  const [editLoading, setEditLoading] = useState(false);
  
  const navigate = useNavigate();

  // Fetch documents from API
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await courseDocumentsAPI.getAll();
      
      // Handle different response structures
      const documentsData = response.data || response.documents || response;
      
      if (Array.isArray(documentsData)) {
        // Transform API response to only include required fields
        const transformedDocuments = documentsData.map(doc => ({
          batchId: doc.Batch_ID || doc.batchId,
          documentId: doc.Document_ID || doc.id,
          title: doc.Document_Title ? doc.Document_Title.replace(/"/g, '') : 'Untitled',
          uploadDateTime: doc.Document_Upload_DateTime || doc.uploadDate || doc.createdAt,
          // Keep original data for reference
          _original: doc
        }));
        
        setDocuments(transformedDocuments);
        console.log('Transformed documents:', transformedDocuments);
      } else {
        console.error('Unexpected API response structure:', response);
        setError('Failed to load documents: Invalid response format');
        setDocuments([]);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError(error.message || 'Failed to load course documents');
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleRefresh = () => {
    fetchDocuments();
  };

  const handleDelete = (documentId) => {
    setDeleteDialog({ open: true, documentId });
  };

  const confirmDelete = async () => {
    try {
      setError(null);
      await courseDocumentsAPI.remove(deleteDialog.documentId);
      
      // Remove from local state
      setDocuments(documents.filter(doc => doc.documentId !== deleteDialog.documentId));
      setSuccess('Document deleted successfully');
      setDeleteDialog({ open: false, documentId: null });
    } catch (error) {
      console.error('Error deleting document:', error);
      setError(error.message || 'Failed to delete document');
      setDeleteDialog({ open: false, documentId: null });
    }
  };

  const handleView = (documentId) => {
    navigate(`/trainer/course-documents/${documentId}`);
  };

  const handleDownload = async (document) => {
    try {
      setError(null);
      
      // Check if we have a direct path from API
      if (document._original?.Document_Path) {
        const documentPath = document._original.Document_Path;
        
        // If it's a full URL, open it directly
        if (documentPath.startsWith('http')) {
          window.open(documentPath, '_blank');
          setSuccess('Document download initiated');
          return;
        }
      }
      
      // Fallback to API call
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
      } else {
        navigate(`/trainer/course-documents/${document.documentId}`);
      }
      
      setSuccess('Document download initiated');
    } catch (error) {
      console.error('Error downloading document:', error);
      setError(error.message || 'Failed to download document');
    }
  };

  // Enhanced Edit Modal Functions
  const handleEdit = (document) => {
    setEditForm({
      title: document.title ? String(document.title) : '',
      batchId: document.batchId ? String(document.batchId) : '',
      file: null
    });
    setEditDialog({ open: true, document });
  };

  const handleEditClose = () => {
    setEditDialog({ open: false, document: null });
    setEditForm({
      title: '',
      batchId: '',
      file: null
    });
  };

  const handleEditFormChange = (field) => (event) => {
    if (field === 'file') {
      setEditForm(prev => ({
        ...prev,
        [field]: event.target.files[0] || null
      }));
    } else {
      setEditForm(prev => ({
        ...prev,
        [field]: event.target.value
      }));
    }
  };

  const handleEditSubmit = async () => {
    try {
      setEditLoading(true);
      setError(null);
      
      // Ensure we have valid string values
      const titleValue = editForm.title ? String(editForm.title).trim() : '';
      const batchIdValue = editForm.batchId ? String(editForm.batchId).trim() : '';
      
      // Validate required fields
      if (!titleValue) {
        setError('Document title is required');
        setEditLoading(false);
        return;
      }
      
      if (!batchIdValue) {
        setError('Batch ID is required');
        setEditLoading(false);
        return;
      }
      
      const updateData = {
        Document_Title: `"${titleValue}"`,
        Batch_ID: batchIdValue
      };
      
      // If file is selected, add it to the update
      if (editForm.file) {
        updateData.file = editForm.file;
      }
      
      const response = await courseDocumentsAPI.update(editDialog.document.documentId, updateData);
      
      // Update local state
      const updatedDocuments = documents.map(doc => 
        doc.documentId === editDialog.document.documentId 
          ? { 
              ...doc, 
              title: titleValue,
              batchId: batchIdValue,
              _original: { ...doc._original, ...updateData }
            }
          : doc
      );
      setDocuments(updatedDocuments);
      setSuccess('Document updated successfully');
      handleEditClose();
    } catch (error) {
      console.error('Error updating document:', error);
      setError(error.message || 'Failed to update document');
    } finally {
      setEditLoading(false);
    }
  };

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = (doc.title?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
                         (doc.documentId?.toString() || '').includes(searchTerm.toLowerCase()) ||
                         (doc.batchId?.toString() || '').includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  // Show shimmer loading UI
  if (loading) {
    return <CourseDocumentsShimmer rows={8} />;
  }

  return (
    <Box>
      {/* Error Snackbar */}
      <Snackbar 
        open={!!error} 
        autoHideDuration={6000} 
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>

      {/* Success Snackbar */}
      <Snackbar 
        open={!!success} 
        autoHideDuration={4000} 
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success" sx={{ width: '100%' }}>
          {success}
        </Alert>
      </Snackbar>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          Course Documents ({filteredDocuments.length})
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => navigate('/trainer/course-documents/add')}
        >
          Add Document
        </Button>
      </Box>

      {/* Search Filter */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            placeholder="Search by title, document ID, or batch ID..."
            value={searchTerm}
            onChange={handleSearch}
            size="small"
            sx={{ minWidth: 400 }}
          />

          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Paper>

      {/* Documents Table */}
      {filteredDocuments.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Documents Found
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            {documents.length === 0 
              ? "No course documents available. Click 'Add Document' to create your first document."
              : "No documents match your current search criteria. Try adjusting your search term."
            }
          </Typography>
          {documents.length === 0 && (
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => navigate('/trainer/course-documents/add')}
            >
              Add First Document
            </Button>
          )}
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Batch ID</strong></TableCell>
                <TableCell><strong>Document ID</strong></TableCell>
                <TableCell><strong>Document Title</strong></TableCell>
                <TableCell><strong>Upload Date & Time</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredDocuments
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((document) => (
                  <TableRow key={document.documentId} hover>
                    <TableCell>{document.batchId || 'N/A'}</TableCell>
                    <TableCell>{document.documentId || 'N/A'}</TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {document.title || 'Untitled'}
                      </Typography>
                    </TableCell>
                    <TableCell>{formatDateTime(document.uploadDateTime)}</TableCell>
                    <TableCell>
                      <IconButton 
                        size="small" 
                        title="View Document"
                        onClick={() => handleView(document.documentId)}
                      >
                        <Visibility />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        title="Download Document"
                        onClick={() => handleDownload(document)}
                      >
                        <Download />
                      </IconButton>
                      <IconButton 
                        size="small"
                        title="Edit Document"
                        onClick={() => handleEdit(document)}
                      >
                        <Edit />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        color="error"
                        title="Delete Document"
                        onClick={() => handleDelete(document.documentId)}
                      >
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
          
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredDocuments.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
          />
        </TableContainer>
      )}

      {/* Enhanced Edit Modal */}
      <Dialog 
        open={editDialog.open} 
        onClose={handleEditClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              Edit Document
            </Typography>
            <IconButton onClick={handleEditClose} size="small">
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Document Title"
                value={editForm.title}
                onChange={handleEditFormChange('title')}
                variant="outlined"
                required
                helperText="Enter the document title"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Batch ID"
                value={editForm.batchId}
                onChange={handleEditFormChange('batchId')}
                variant="outlined"
                required
                helperText="Enter the batch ID"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Replace Document File (Optional)
                </Typography>
                <input
                  accept=".pdf,.doc,.docx,.txt,.ppt,.pptx"
                  style={{ display: 'none' }}
                  id="edit-file-input"
                  type="file"
                  onChange={handleEditFormChange('file')}
                />
                <label htmlFor="edit-file-input">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<Upload />}
                    fullWidth
                  >
                    {editForm.file ? editForm.file.name : 'Choose New File'}
                  </Button>
                </label>
                {editForm.file && (
                  <Box mt={1}>
                    <Typography variant="body2" color="text.secondary">
                      Selected: {editForm.file.name} ({(editForm.file.size / 1024 / 1024).toFixed(2)} MB)
                    </Typography>
                  </Box>
                )}
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  <strong>Current Document:</strong> {editDialog.document?.title}
                  <br />
                  <strong>Current Batch ID:</strong> {editDialog.document?.batchId}
                  <br />
                  <strong>Upload Date:</strong> {formatDateTime(editDialog.document?.uploadDateTime)}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        
        <DialogActions sx={{ p: 2 }}>
          <Button 
            onClick={handleEditClose} 
            color="inherit"
            disabled={editLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleEditSubmit} 
            variant="contained"
            disabled={editLoading || !editForm.title?.trim() || !editForm.batchId?.trim()}
            startIcon={editLoading ? <CircularProgress size={20} /> : null}
          >
            {editLoading ? 'Updating...' : 'Update Document'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, documentId: null })}
        onConfirm={confirmDelete}
        title="Delete Document"
        message="Are you sure you want to delete this document? This action cannot be undone."
      />
    </Box>
  );
};

export default CourseDocumentsList;