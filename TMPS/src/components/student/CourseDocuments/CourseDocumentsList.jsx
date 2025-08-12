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
  TablePagination,
  Skeleton,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Visibility,
  Refresh
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
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

const StudentCourseDocumentsList = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
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

  // Navigate to student-specific view route
  const handleView = (documentId) => {
    console.log('Navigating to view document:', documentId);
    navigate(`/student/course-documents/view/${documentId}`);
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
              ? "No course documents available at this time."
              : "No documents match your current search criteria. Try adjusting your search term."
            }
          </Typography>
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
                        color="primary"
                      >
                        <Visibility />
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
    </Box>
  );
};

export default StudentCourseDocumentsList;