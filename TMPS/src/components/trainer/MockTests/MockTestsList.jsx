import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Avatar,
  CircularProgress,
  Alert,
  Modal,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Skeleton,
  Stack
} from '@mui/material';
import {
  Assessment,
  Schedule,
  CheckCircle,
  Cancel,
  Visibility,
  Edit,
  Close,
  Save,
  Refresh,
  Person
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Import your API service
import { mockTestsAPI } from '../../../services/API/mocktest';

// Shimmer/Skeleton components
const TestCardSkeleton = () => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center">
        <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
        <Box flex={1}>
          <Skeleton variant="text" width="40%" height={20} />
          <Skeleton variant="text" width="60%" height={32} />
        </Box>
      </Box>
    </CardContent>
  </Card>
);

const TestTableSkeleton = () => (
  <Card>
    <CardContent>
      <Skeleton variant="text" width="200px" height={32} sx={{ mb: 2 }} />
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {Array.from({ length: 6 }).map((_, index) => (
                <TableCell key={index}>
                  <Skeleton variant="text" width="100%" height={24} />
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {Array.from({ length: 3 }).map((_, rowIndex) => (
              <TableRow key={rowIndex}>
                {Array.from({ length: 6 }).map((_, cellIndex) => (
                  <TableCell key={cellIndex}>
                    <Skeleton variant="text" width="100%" height={24} />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </CardContent>
  </Card>
);

const MockTestsList = () => {
  const navigate = useNavigate();
  const [mockTests, setMockTests] = useState([]);
  const [stats, setStats] = useState({
    total_tests: 0,
    active_tests: 0,
    completed_tests: 0,
    draft_tests: 0,
    average_score: 0,
    total_students: 0,
    total_completions: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingTest, setEditingTest] = useState(null);
  const [editForm, setEditForm] = useState({
    name: '',
    Student_ID: '',
    status: 'active'
  });
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchMockTests();
  }, []);

  const fetchMockTests = async () => {
    try {
      setLoading(true);
      setError('');
      
      console.log('Fetching students from API...');
      
      // Fetch all students instead of tests
      const studentsData = await mockTestsAPI.getAllStudents();
      console.log('Raw API response:', studentsData);
      
      // Transform the data to match component expectations
      const transformedStudents = studentsData.map(student => ({
        id: student.Student_ID,
        title: student.name || 'No Name',
        subject: 'Student',
        duration: 0,
        totalQuestions: 0,
        dateCreated: new Date().toISOString(),
        dueDate: new Date().toISOString(),
        status: student.name ? 'active' : 'inactive',
        completedBy: 0,
        totalStudents: 1,
        averageScore: 0,
        Student_ID: student.Student_ID,
        studentName: student.name,
        raw: student
      }));
      console.log('Transformed students:', transformedStudents);
      
      setMockTests(transformedStudents);
      
      // Calculate stats from students
      const calculatedStats = {
        total_tests: transformedStudents.length,
        active_tests: transformedStudents.filter(s => s.status === 'active').length,
        completed_tests: 0,
        draft_tests: transformedStudents.filter(s => s.status === 'inactive').length,
        average_score: 0,
        total_students: transformedStudents.length,
        total_completions: 0
      };
      setStats(calculatedStats);
      
    } catch (err) {
      console.error('Error fetching students:', err);
      setError(`Failed to fetch students: ${err.message}`);
      
      // Set empty data on error
      setMockTests([]);
      setStats({
        total_tests: 0,
        active_tests: 0,
        completed_tests: 0,
        draft_tests: 0,
        average_score: 0,
        total_students: 0,
        total_completions: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchMockTests();
    setRefreshing(false);
  };

  const handleViewClick = (studentId) => {
    navigate(`/trainer/mock-tests/view/${studentId}`);
  };

  const handleEditClick = (student) => {
    setEditingTest(student);
    setEditForm({
      name: student.studentName || '',
      Student_ID: student.Student_ID.toString(),
      status: student.status
    });
    setEditModalOpen(true);
  };

  const handleEditFormChange = (field, value) => {
    setEditForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSaveEdit = async () => {
    try {
      setSaving(true);
      
      console.log('Edit functionality not implemented for students');
      alert('Edit functionality is not available for students with current API endpoints');
      
      setEditModalOpen(false);
      setEditingTest(null);
    } catch (err) {
      console.error('Error saving student:', err);
      setError(`Failed to update student: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleCloseModal = () => {
    setEditModalOpen(false);
    setEditingTest(null);
    setSaving(false);
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'error';
      case 'draft':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return <CheckCircle />;
      case 'inactive':
        return <Cancel />;
      case 'draft':
        return <Schedule />;
      default:
        return <Person />;
    }
  };

  const calculateCompletionPercentage = (completed, total) => {
    return total > 0 ? ((completed / total) * 100).toFixed(1) : 0;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (error) {
      console.warn('Date formatting error:', error);
      return 'N/A';
    }
  };

  const getInitials = (name) => {
    if (!name || name === 'No Name') return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  if (loading) {
    return (
      <Box>
        <Skeleton variant="text" width="200px" height={48} sx={{ mb: 4 }} />
        
        {/* Summary Cards Skeleton */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {Array.from({ length: 4 }).map((_, index) => (
            <Grid item xs={12} md={3} key={index}>
              <TestCardSkeleton />
            </Grid>
          ))}
        </Grid>

        {/* Table Skeleton */}
        <TestTableSkeleton />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={4}>
        <Typography variant="h4" gutterBottom>
          Students
        </Typography>
        <Button
          variant="outlined"
          startIcon={refreshing ? <CircularProgress size={20} /> : <Refresh />}
          onClick={handleRefresh}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <Person />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Students
                  </Typography>
                  <Typography variant="h5">
                    {stats.total_students || mockTests.length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <CheckCircle />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Students
                  </Typography>
                  <Typography variant="h5">
                    {stats.active_tests || mockTests.filter(student => student.status === 'active').length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <Cancel />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Inactive Students
                  </Typography>
                  <Typography variant="h5">
                    {stats.draft_tests || mockTests.filter(student => student.status === 'inactive').length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <Assessment />
                </Avatar>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Named Students
                  </Typography>
                  <Typography variant="h5">
                    {mockTests.filter(student => student.studentName && student.studentName !== 'No Name').length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Students Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            All Students ({mockTests.length})
          </Typography>
          
          {mockTests.length === 0 ? (
            <Box textAlign="center" py={4}>
              <Typography variant="h6" color="textSecondary" gutterBottom>
                No students found
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {error ? 'Please check your API connection and try refreshing.' : 'No students are currently enrolled.'}
              </Typography>
            </Box>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Avatar</TableCell>
                    <TableCell>Student ID</TableCell>
                    <TableCell>Student Name</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {mockTests.map((student) => (
                    <TableRow key={student.Student_ID}>
                      <TableCell>
                        <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                          <Typography variant="caption" fontWeight="bold">
                            {getInitials(student.studentName)}
                          </Typography>
                        </Avatar>
                      </TableCell>
                      <TableCell>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {student.Student_ID}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {student.studentName || 'No Name'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={student.status}
                          color={getStatusColor(student.status)}
                          icon={getStatusIcon(student.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1}>
                          <IconButton
                            size="small"
                            sx={{
                              color: 'text.secondary',
                              '&:hover': {
                                color: 'primary.main',
                                backgroundColor: 'transparent',
                              }
                            }}
                            onClick={() => handleViewClick(student.Student_ID)}
                            title="View Student Details"
                          >
                            <Visibility fontSize="small" />
                          </IconButton>
                          <IconButton
                            size="small"
                            sx={{
                              color: 'text.secondary',
                              '&:hover': {
                                color: 'success.main',
                                backgroundColor: 'transparent',
                              }
                            }}
                            onClick={() => handleEditClick(student)}
                            title="Edit Student"
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Edit Modal */}
      <Modal
        open={editModalOpen}
        onClose={handleCloseModal}
        aria-labelledby="edit-student-modal"
      >
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: { xs: '90%', sm: 600 },
            bgcolor: 'background.paper',
            boxShadow: 24,
            borderRadius: 2,
            p: 0,
            maxHeight: '90vh',
            overflow: 'auto'
          }}
        >
          {/* Modal Header */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              p: 3,
              borderBottom: 1,
              borderColor: 'divider'
            }}
          >
            <Typography variant="h6" component="h2">
              Edit Student
            </Typography>
            <IconButton onClick={handleCloseModal} disabled={saving}>
              <Close />
            </IconButton>
          </Box>

          {/* Modal Body */}
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Student Name"
                  value={editForm.name}
                  onChange={(e) => handleEditFormChange('name', e.target.value)}
                  disabled={saving}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Student ID"
                  value={editForm.Student_ID}
                  onChange={(e) => handleEditFormChange('Student_ID', e.target.value)}
                  disabled={saving}
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth disabled={saving}>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={editForm.status}
                    label="Status"
                    onChange={(e) => handleEditFormChange('status', e.target.value)}
                  >
                    <MenuItem value="active">Active</MenuItem>
                    <MenuItem value="inactive">Inactive</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>

          {/* Modal Footer */}
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 2,
              p: 3,
              borderTop: 1,
              borderColor: 'divider'
            }}
          >
            <Button
              variant="outlined"
              onClick={handleCloseModal}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={saving ? <CircularProgress size={20} /> : <Save />}
              onClick={handleSaveEdit}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </Box>
      </Modal>
    </Box>
  );
};

export default MockTestsList;