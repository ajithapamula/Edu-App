import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardHeader,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Typography,
  TextField,
  InputAdornment,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Skeleton,
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as VisibilityIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
  TrendingUp as TrendingUpIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { useApi } from '../../../hooks/useApi';
import trainerService from '../../../services/trainerService';
import LoadingSpinner from '../../common/LoadingSpinner';
import { formatDate } from '../../../utils/dateUtils';
import { useNavigate } from 'react-router-dom';

// Shimmer/Skeleton component for table rows
const TableRowSkeleton = () => (
  <TableRow>
    <TableCell>
      <Box>
        <Skeleton variant="text" width="60%" height={24} />
        <Skeleton variant="text" width="80%" height={20} />
        <Skeleton variant="text" width="40%" height={16} />
      </Box>
    </TableCell>
    <TableCell>
      <Box>
        <Skeleton variant="text" width="70%" height={20} />
        <Skeleton variant="text" width="50%" height={16} />
      </Box>
    </TableCell>
    <TableCell>
      <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 1 }} />
    </TableCell>
    <TableCell>
      <Box sx={{ width: '100%' }}>
        <Skeleton variant="text" width="100%" height={16} />
        <Skeleton variant="rectangular" width="100%" height={6} sx={{ borderRadius: 3, my: 0.5 }} />
        <Skeleton variant="text" width="60%" height={14} />
      </Box>
    </TableCell>
    <TableCell>
      <Box>
        <Skeleton variant="text" width="60%" height={20} />
        <Skeleton variant="text" width="80%" height={16} />
      </Box>
    </TableCell>
    <TableCell>
      <Box>
        <Skeleton variant="text" width="50%" height={24} />
        <Skeleton variant="text" width="40%" height={16} />
      </Box>
    </TableCell>
    <TableCell>
      <Skeleton variant="rectangular" width={70} height={24} sx={{ borderRadius: 1 }} />
    </TableCell>
    <TableCell>
      <Skeleton variant="text" width="80%" height={20} />
    </TableCell>
    <TableCell align="center">
      <Box display="flex" gap={1}>
        <Skeleton variant="circular" width={32} height={32} />
        <Skeleton variant="circular" width={32} height={32} />
        <Skeleton variant="circular" width={32} height={32} />
      </Box>
    </TableCell>
  </TableRow>
);

// Dummy data
const DUMMY_COMPILATIONS = [
  {
    id: 1,
    title: "Mathematics Weekly Assessment",
    description: "Comprehensive math test covering algebra and geometry topics for grade 10 students",
    studentName: "Alice Johnson",
    studentId: "STU001",
    type: "weekly",
    status: "completed",
    completionPercentage: 95,
    completedTests: 8,
    totalTests: 8,
    testTypes: ["Multiple Choice", "Short Answer"],
    overallScore: 85,
    totalMarks: 100,
    overallPercentage: 85,
    dueDate: "2025-06-10T10:00:00Z",
    createdAt: "2025-05-28T08:00:00Z",
    isOverdue: false
  },
  {
    id: 2,
    title: "Science Mid-Term Evaluation",
    description: "Physics and Chemistry combined assessment for mid-term evaluation",
    studentName: "Bob Smith",
    studentId: "STU002",
    type: "mid_term",
    status: "in_progress",
    completionPercentage: 65,
    completedTests: 5,
    totalTests: 8,
    testTypes: ["Practical", "Theory"],
    overallScore: 72,
    totalMarks: 120,
    overallPercentage: 60,
    dueDate: "2025-06-15T14:00:00Z",
    createdAt: "2025-05-25T09:00:00Z",
    isOverdue: false
  },
  {
    id: 3,
    title: "English Literature Final",
    description: "Final examination covering Shakespeare and modern poetry analysis",
    studentName: "Carol Davis",
    studentId: "STU003",
    type: "final",
    status: "pending",
    completionPercentage: 0,
    completedTests: 0,
    totalTests: 6,
    testTypes: ["Essay", "Analysis"],
    overallScore: 0,
    totalMarks: 150,
    overallPercentage: 0,
    dueDate: "2025-06-20T16:00:00Z",
    createdAt: "2025-05-30T11:00:00Z",
    isOverdue: false
  },
  {
    id: 4,
    title: "History Monthly Test",
    description: "World War II and Cold War period assessment",
    studentName: "David Wilson",
    studentId: "STU004",
    type: "monthly",
    status: "failed",
    completionPercentage: 100,
    completedTests: 4,
    totalTests: 4,
    testTypes: ["Multiple Choice", "Essay"],
    overallScore: 28,
    totalMarks: 80,
    overallPercentage: 35,
    dueDate: "2025-05-30T12:00:00Z",
    createdAt: "2025-05-20T10:00:00Z",
    isOverdue: true
  },
  {
    id: 5,
    title: "Biology Lab Assessment",
    description: "Practical laboratory skills evaluation and report writing",
    studentName: "Eva Brown",
    studentId: "STU005",
    type: "weekly",
    status: "submitted",
    completionPercentage: 100,
    completedTests: 3,
    totalTests: 3,
    testTypes: ["Practical", "Report"],
    overallScore: 92,
    totalMarks: 100,
    overallPercentage: 92,
    dueDate: "2025-06-08T15:00:00Z",
    createdAt: "2025-06-01T08:30:00Z",
    isOverdue: false
  }
];

const TestCompilationList = () => {
  const navigate = useNavigate();
  const [compilations, setCompilations] = useState([]);
  const [filteredCompilations, setFilteredCompilations] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedCompilation, setSelectedCompilation] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const { loading, error, makeRequest } = useApi();

  useEffect(() => {
    fetchTestCompilations();
  }, []);

  useEffect(() => {
    let filtered = compilations.filter(compilation =>
      compilation.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      compilation.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      compilation.studentName.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (filterStatus !== 'all') {
      filtered = filtered.filter(compilation => compilation.status === filterStatus);
    }

    if (filterType !== 'all') {
      filtered = filtered.filter(compilation => compilation.type === filterType);
    }

    setFilteredCompilations(filtered);
  }, [compilations, searchTerm, filterStatus, filterType]);

  const fetchTestCompilations = async () => {
    try {
      await makeRequest(async () => {
        // Simulate API call with dummy data
        await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
        setCompilations(DUMMY_COMPILATIONS);
      });
    } catch (error) {
      console.error('Error fetching test compilations:', error);
    }
  };

  const handleEditClick = (compilation) => {
    setSelectedCompilation(compilation);
    setEditFormData({
      title: compilation.title,
      description: compilation.description,
      studentName: compilation.studentName,
      studentId: compilation.studentId,
      type: compilation.type,
      status: compilation.status,
      dueDate: compilation.dueDate ? new Date(compilation.dueDate).toISOString().split('T')[0] : '',
      totalTests: compilation.totalTests,
      totalMarks: compilation.totalMarks,
    });
    setEditModalOpen(true);
  };

  const handleEditSave = async () => {
    try {
      // Update the compilation in the list
      const updatedCompilations = compilations.map(comp => 
        comp.id === selectedCompilation.id 
          ? { ...comp, ...editFormData, dueDate: new Date(editFormData.dueDate).toISOString() }
          : comp
      );
      setCompilations(updatedCompilations);
      setEditModalOpen(false);
      setSelectedCompilation(null);
      
      // Here you would normally make an API call to update the data
      console.log('Updated compilation:', editFormData);
    } catch (error) {
      console.error('Error updating compilation:', error);
    }
  };

  const handleEditCancel = () => {
    setEditModalOpen(false);
    setSelectedCompilation(null);
    setEditFormData({});
  };

  const handleFormChange = (field, value) => {
    setEditFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'info';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      case 'submitted':
        return 'primary';
      default:
        return 'default';
    }
  };

  const getTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'weekly':
        return 'primary';
      case 'monthly':
        return 'secondary';
      case 'final':
        return 'success';
      case 'mid_term':
        return 'info';
      default:
        return 'default';
    }
  };

  const getProgressColor = (progress) => {
    if (progress >= 80) return 'success';
    if (progress >= 60) return 'info';
    if (progress >= 40) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Card>
        <CardHeader
          title={
            <Box display="flex" alignItems="center" gap={1}>
              <AssessmentIcon />
              <Typography variant="h6">Test Compilation</Typography>
            </Box>
          }
        />
        <CardContent>
          {/* Filters */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search compilations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} sm={3} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterStatus}
                  label="Status"
                  onChange={(e) => setFilterStatus(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="submitted">Submitted</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Type</InputLabel>
                <Select
                  value={filterType}
                  label="Type"
                  onChange={(e) => setFilterType(e.target.value)}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                  <MenuItem value="mid_term">Mid Term</MenuItem>
                  <MenuItem value="final">Final</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {error && (
            <Typography color="error" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}

          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Compilation Details</TableCell>
                  <TableCell>Student</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Tests Included</TableCell>
                  <TableCell>Overall Score</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  // Show shimmer rows while loading
                  Array.from({ length: 5 }).map((_, index) => (
                    <TableRowSkeleton key={index} />
                  ))
                ) : filteredCompilations.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      <Typography variant="body2" color="text.secondary">
                        {searchTerm || filterStatus !== 'all' || filterType !== 'all' 
                          ? 'No compilations found matching your filters.' 
                          : 'No test compilations available.'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredCompilations.map((compilation) => (
                    <TableRow key={compilation.id} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="subtitle2" fontWeight="medium">
                            {compilation.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {compilation.description?.substring(0, 50)}
                            {compilation.description?.length > 50 ? '...' : ''}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Created: {formatDate(compilation.createdAt)}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {compilation.studentName}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {compilation.studentId}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={compilation.type?.replace('_', ' ').toUpperCase()}
                          size="small"
                          color={getTypeColor(compilation.type)}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <Box display="flex" justifyContent="space-between" mb={0.5}>
                            <Typography variant="body2" fontSize="0.75rem">
                              Progress
                            </Typography>
                            <Typography variant="body2" fontSize="0.75rem">
                              {compilation.completionPercentage || 0}%
                            </Typography>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={compilation.completionPercentage || 0}
                            color={getProgressColor(compilation.completionPercentage)}
                            sx={{ height: 6, borderRadius: 3 }}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {compilation.completedTests || 0} / {compilation.totalTests || 0} tests
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {compilation.totalTests || 0} Tests
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {compilation.testTypes?.join(', ') || 'Various'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography 
                            variant="body1" 
                            fontWeight="bold"
                            color={getProgressColor(compilation.overallPercentage)}
                          >
                            {compilation.overallScore || 0} / {compilation.totalMarks || 0}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {compilation.overallPercentage?.toFixed(1) || 0}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={compilation.status}
                          size="small"
                          color={getStatusColor(compilation.status)}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(compilation.dueDate)}
                        </Typography>
                        {compilation.isOverdue && (
                          <Typography variant="caption" color="error">
                            Overdue
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/trainer/test-compilation/view/${compilation.id}`)}
                          >
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Compilation">
                          <IconButton
                            size="small"
                            onClick={() => handleEditClick(compilation)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download Report">
                          <IconButton
                            size="small"
                            onClick={() => {/* Download compilation report */}}
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Summary Statistics */}
          {!loading && filteredCompilations.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="primary">
                      {filteredCompilations.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Compilations
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="success.main">
                      {filteredCompilations.filter(c => c.status === 'completed').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Completed
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="info.main">
                      {filteredCompilations.filter(c => c.status === 'in_progress').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      In Progress
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Paper sx={{ p: 2, textAlign: 'center' }}>
                    <Typography variant="h5" color="warning.main">
                      {filteredCompilations.filter(c => c.isOverdue).length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Overdue
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              {/* Average Performance */}
              <Paper sx={{ p: 2, mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Average Performance Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <TrendingUpIcon color="primary" />
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Average Completion
                        </Typography>
                        <Typography variant="h6">
                          {(filteredCompilations.reduce((sum, c) => sum + (c.completionPercentage || 0), 0) / filteredCompilations.length).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <AssessmentIcon color="success" />
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Average Score
                        </Typography>
                        <Typography variant="h6">
                          {(filteredCompilations.reduce((sum, c) => sum + (c.overallPercentage || 0), 0) / filteredCompilations.length).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body2" color="text.secondary">
                        Success Rate
                      </Typography>
                      <Typography variant="h6" color="success.main">
                        {((filteredCompilations.filter(c => c.status === 'completed').length / filteredCompilations.length) * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Edit Modal */}
      <Dialog 
        open={editModalOpen} 
        onClose={handleEditCancel}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Edit Test Compilation
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Title"
                value={editFormData.title || ''}
                onChange={(e) => handleFormChange('title', e.target.value)}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={editFormData.description || ''}
                onChange={(e) => handleFormChange('description', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Student Name"
                value={editFormData.studentName || ''}
                onChange={(e) => handleFormChange('studentName', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Student ID"
                value={editFormData.studentId || ''}
                onChange={(e) => handleFormChange('studentId', e.target.value)}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={editFormData.type || ''}
                  label="Type"
                  onChange={(e) => handleFormChange('type', e.target.value)}
                >
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="monthly">Monthly</MenuItem>
                  <MenuItem value="mid_term">Mid Term</MenuItem>
                  <MenuItem value="final">Final</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={editFormData.status || ''}
                  label="Status"
                  onChange={(e) => handleFormChange('status', e.target.value)}
                >
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="submitted">Submitted</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Total Tests"
                type="number"
                value={editFormData.totalTests || ''}
                onChange={(e) => handleFormChange('totalTests', parseInt(e.target.value) || 0)}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Total Marks"
                type="number"
                value={editFormData.totalMarks || ''}
                onChange={(e) => handleFormChange('totalMarks', parseInt(e.target.value) || 0)}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Due Date"
                type="date"
                value={editFormData.dueDate || ''}
                onChange={(e) => handleFormChange('dueDate', e.target.value)}
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleEditCancel}>
            Cancel
          </Button>
          <Button onClick={handleEditSave} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TestCompilationList;