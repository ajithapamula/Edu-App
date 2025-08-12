import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  TextField,
  InputAdornment,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  Avatar,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Rating
} from '@mui/material';
import {
  Search,
  Visibility,
  Download,
  Grade,
  Comment,
  Assignment,
  Person,
  Schedule,
  CheckCircle,
  Pending,
  Error,
  FilterList,
  AttachFile
} from '@mui/icons-material';

const MentorTaskSubmissionsList = () => {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterTask, setFilterTask] = useState('all');
  const [filterTrainer, setFilterTrainer] = useState('all');
  const [gradeDialogOpen, setGradeDialogOpen] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [grade, setGrade] = useState(0);
  const [feedback, setFeedback] = useState('');

  useEffect(() => {
    // Mock data - replace with actual API call
    const mockSubmissions = [
      {
        id: 1,
        taskTitle: 'React Components Tutorial',
        taskId: 1,
        submitter: 'John Trainer',
        submitterAvatar: '/avatars/john.jpg',
        submissionDate: '2024-12-15T16:30:00Z',
        status: 'submitted',
        grade: null,
        maxGrade: 100,
        submissionText: 'Completed the React components tutorial with all required sections and interactive examples.',
        attachments: [
          { name: 'react-tutorial.pdf', size: '2.5 MB' },
          { name: 'code-examples.zip', size: '1.8 MB' }
        ],
        feedback: null,
        reviewedBy: null,
        reviewedDate: null,
        timeSpent: '12 hours',
        isLate: false
      },
      {
        id: 2,
        taskTitle: 'Database Design Review',
        taskId: 2,
        submitter: 'Mike Trainer',
        submitterAvatar: '/avatars/mike.jpg',
        submissionDate: '2024-12-14T14:20:00Z',
        status: 'graded',
        grade: 85,
        maxGrade: 100,
        submissionText: 'Reviewed 15 student database assignments and provided detailed feedback on normalization and design patterns.',
        attachments: [
          { name: 'review-summary.docx', size: '450 KB' },
          { name: 'student-feedback.xlsx', size: '780 KB' }
        ],
        feedback: 'Excellent work on the reviews. Your feedback was constructive and detailed.',
        reviewedBy: 'Sarah Mentor',
        reviewedDate: '2024-12-14T18:45:00Z',
        timeSpent: '6 hours',
        isLate: false
      },
      {
        id: 3,
        taskTitle: 'API Workshop Materials',
        taskId: 3,
        submitter: 'Lisa Trainer',
        submitterAvatar: '/avatars/lisa.jpg',
        submissionDate: '2024-12-13T11:15:00Z',
        status: 'graded',
        grade: 92,
        maxGrade: 100,
        submissionText: 'Created comprehensive workshop materials including slides, hands-on exercises, and assessment quiz.',
        attachments: [
          { name: 'api-workshop-slides.pptx', size: '3.2 MB' },
          { name: 'exercises.zip', size: '2.1 MB' },
          { name: 'assessment-quiz.pdf', size: '890 KB' }
        ],
        feedback: 'Outstanding work! The materials are well-structured and engaging.',
        reviewedBy: 'John Mentor',
        reviewedDate: '2024-12-13T15:30:00Z',
        timeSpent: '18 hours',
        isLate: false
      },
      {
        id: 4,
        taskTitle: 'Course Documentation Update',
        taskId: 4,
        submitter: 'Tom Trainer',
        submitterAvatar: '/avatars/tom.jpg',
        submissionDate: '2024-12-16T20:45:00Z',
        status: 'pending_review',
        grade: null,
        maxGrade: 100,
        submissionText: 'Updated documentation for React, Node.js, and database courses with latest framework versions.',
        attachments: [
          { name: 'updated-docs.zip', size: '5.1 MB' }
        ],
        feedback: null,
        reviewedBy: null,
        reviewedDate: null,
        timeSpent: '8 hours',
        isLate: true
      },
      {
        id: 5,
        taskTitle: 'Mock Interview Sessions',
        taskId: 5,
        submitter: 'Emma Trainer',
        submitterAvatar: '/avatars/emma.jpg',
        submissionDate: '2024-12-12T09:30:00Z',
        status: 'needs_revision',
        grade: 65,
        maxGrade: 100,
        submissionText: 'Conducted 8 mock interview sessions. Some sessions were shorter than expected.',
        attachments: [
          { name: 'interview-reports.pdf', size: '1.5 MB' }
        ],
        feedback: 'Good effort, but please provide more detailed feedback reports for each session.',
        reviewedBy: 'Mike Mentor',
        reviewedDate: '2024-12-12T14:20:00Z',
        timeSpent: '10 hours',
        isLate: true
      }
    ];

    setTimeout(() => {
      setSubmissions(mockSubmissions);
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'graded': return 'success';
      case 'submitted': return 'info';
      case 'pending_review': return 'warning';
      case 'needs_revision': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'graded': return <CheckCircle />;
      case 'submitted': return <Assignment />;
      case 'pending_review': return <Pending />;
      case 'needs_revision': return <Error />;
      default: return <Assignment />;
    }
  };

  const getGradeColor = (grade, maxGrade) => {
    const percentage = (grade / maxGrade) * 100;
    if (percentage >= 90) return 'success';
    if (percentage >= 70) return 'info';
    if (percentage >= 50) return 'warning';
    return 'error';
  };

  const filteredSubmissions = submissions.filter(submission => {
    const matchesSearch = submission.taskTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         submission.submitter.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         submission.submissionText.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || submission.status === filterStatus;
    const matchesTask = filterTask === 'all' || submission.taskId.toString() === filterTask;
    const matchesTrainer = filterTrainer === 'all' || submission.submitter === filterTrainer;
    
    return matchesSearch && matchesStatus && matchesTask && matchesTrainer;
  });

  const handleViewSubmission = (submission) => {
    console.log('View submission:', submission.id);
  };

  const handleGradeSubmission = (submission) => {
    setSelectedSubmission(submission);
    setGrade(submission.grade || 0);
    setFeedback(submission.feedback || '');
    setGradeDialogOpen(true);
  };

  const handleSaveGrade = () => {
    const updatedSubmissions = submissions.map(submission => 
      submission.id === selectedSubmission.id 
        ? {
            ...submission,
            grade: grade,
            feedback: feedback,
            status: 'graded',
            reviewedBy: 'Current Mentor',
            reviewedDate: new Date().toISOString()
          }
        : submission
    );
    setSubmissions(updatedSubmissions);
    setGradeDialogOpen(false);
    setSelectedSubmission(null);
    setGrade(0);
    setFeedback('');
  };

  const handleDownload = (attachment, submissionId) => {
    console.log('Download:', attachment.name, 'from submission:', submissionId);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const uniqueTasks = [...new Set(submissions.map(s => ({ id: s.taskId, title: s.taskTitle })))];
  const uniqueTrainers = [...new Set(submissions.map(s => s.submitter))];

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
          Loading task submissions...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Task Submissions
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Assignment color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{submissions.length}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Submissions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Pending color="warning" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">
                    {submissions.filter(s => s.status === 'submitted' || s.status === 'pending_review').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Pending Review
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircle color="success" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">
                    {submissions.filter(s => s.status === 'graded').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Graded
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Schedule color="error" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">
                    {submissions.filter(s => s.isLate).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Late Submissions
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters and Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                placeholder="Search submissions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterStatus}
                  label="Status"
                  onChange={(e) => setFilterStatus(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="submitted">Submitted</MenuItem>
                  <MenuItem value="pending_review">Pending Review</MenuItem>
                  <MenuItem value="graded">Graded</MenuItem>
                  <MenuItem value="needs_revision">Needs Revision</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Task</InputLabel>
                <Select
                  value={filterTask}
                  label="Task"
                  onChange={(e) => setFilterTask(e.target.value)}
                >
                  <MenuItem value="all">All Tasks</MenuItem>
                  {uniqueTasks.map((task) => (
                    <MenuItem key={task.id} value={task.id.toString()}>
                      {task.title}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Trainer</InputLabel>
                <Select
                  value={filterTrainer}
                  label="Trainer"
                  onChange={(e) => setFilterTrainer(e.target.value)}
                >
                  <MenuItem value="all">All Trainers</MenuItem>
                  {uniqueTrainers.map((trainer) => (
                    <MenuItem key={trainer} value={trainer}>
                      {trainer}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<FilterList />}
                onClick={() => {
                  setSearchTerm('');
                  setFilterStatus('all');
                  setFilterTask('all');
                  setFilterTrainer('all');
                }}
              >
                Clear
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Submissions Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Task & Submission</TableCell>
                  <TableCell>Submitter</TableCell>
                  <TableCell>Submission Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Grade</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredSubmissions.map((submission) => (
                  <TableRow 
                    key={submission.id} 
                    hover
                    sx={{ 
                      backgroundColor: submission.isLate ? 'warning.light' : 'inherit',
                      opacity: submission.isLate ? 0.9 : 1
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ mr: 2 }}>
                          {getStatusIcon(submission.status)}
                        </Box>
                        <Box>
                          <Typography variant="subtitle2" fontWeight="bold">
                            {submission.taskTitle}
                            {submission.isLate && (
                              <Chip 
                                label="LATE" 
                                color="error" 
                                size="small" 
                                sx={{ ml: 1 }}
                              />
                            )}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300 }}>
                            {submission.submissionText.substring(0, 100)}...
                          </Typography>
                          <Box sx={{ mt: 0.5, display: 'flex', alignItems: 'center' }}>
                            <AttachFile sx={{ fontSize: 16, mr: 0.5 }} />
                            <Typography variant="caption" color="text.secondary">
                              {submission.attachments.length} attachment(s)
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                              Time spent: {submission.timeSpent}
                            </Typography>
                          </Box>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar src={submission.submitterAvatar} sx={{ width: 24, height: 24, mr: 1 }}>
                          {submission.submitter.charAt(0)}
                        </Avatar>
                        <Typography variant="body2">
                          {submission.submitter}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(submission.submissionDate)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={submission.status.replace('_', ' ').toUpperCase()}
                        color={getStatusColor(submission.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      {submission.grade !== null ? (
                        <Box>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography variant="body2" fontWeight="bold">
                              {submission.grade}/{submission.maxGrade}
                            </Typography>
                            <Chip
                              label={`${Math.round((submission.grade / submission.maxGrade) * 100)}%`}
                              color={getGradeColor(submission.grade, submission.maxGrade)}
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          </Box>
                          {submission.reviewedBy && (
                            <Typography variant="caption" color="text.secondary">
                              by {submission.reviewedBy}
                            </Typography>
                          )}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Not graded
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => handleViewSubmission(submission)}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Grade/Review">
                          <IconButton
                            size="small"
                            onClick={() => handleGradeSubmission(submission)}
                            color="primary"
                          >
                            <Grade />
                          </IconButton>
                        </Tooltip>
                        {submission.attachments.map((attachment, index) => (
                          <Tooltip key={index} title={`Download ${attachment.name}`}>
                            <IconButton
                              size="small"
                              onClick={() => handleDownload(attachment, submission.id)}
                            >
                              <Download />
                            </IconButton>
                          </Tooltip>
                        ))}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {filteredSubmissions.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h6" color="text.secondary">
                No submissions found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try adjusting your search criteria
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Grade Submission Dialog */}
      <Dialog
        open={gradeDialogOpen}
        onClose={() => setGradeDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Grade Submission: {selectedSubmission?.taskTitle}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Submitted by: {selectedSubmission?.submitter}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {selectedSubmission?.submissionText}
            </Typography>
          </Box>
          
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Grade (out of {selectedSubmission?.maxGrade})
            </Typography>
            <TextField
              type="number"
              value={grade}
              onChange={(e) => setGrade(Number(e.target.value))}
              inputProps={{ min: 0, max: selectedSubmission?.maxGrade }}
              fullWidth
              sx={{ mb: 2 }}
            />
            <Rating
              value={grade / 20}
              onChange={(event, newValue) => setGrade(newValue * 20)}
              max={5}
              precision={0.5}
            />
          </Box>
          
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Feedback
            </Typography>
            <TextField
              multiline
              rows={4}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Provide feedback to the trainer..."
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGradeDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveGrade} variant="contained">
            Save Grade & Feedback
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MentorTaskSubmissionsList;