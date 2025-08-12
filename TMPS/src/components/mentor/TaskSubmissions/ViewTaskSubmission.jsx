import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  IconButton,
  Avatar,
  Divider,
  Paper,
  LinearProgress,
  Alert,
  Rating,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from '@mui/lab';
import {
  ArrowBack,
  Assignment,
  Person,
  CalendarToday,
  Schedule,
  AttachFile,
  Grade,
  CheckCircle,
  Warning,
  Error,
  Feedback,
  Download,
  Edit
} from '@mui/icons-material';

const MentorViewTaskSubmission = ({ submissionId, onBack, onEdit }) => {
  const [submission, setSubmission] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data - replace with actual API call
    const mockSubmission = {
      id: submissionId,
      task: {
        id: 1,
        title: 'React Components Tutorial',
        description: 'Develop a comprehensive tutorial on creating reusable React components',
        dueDate: '2024-12-20T23:59:59Z',
        estimatedHours: 8,
        maxScore: 100,
        requirements: [
          'Cover basic component creation',
          'Explain props and state',
          'Include code examples',
          'Add interactive exercises',
          'Provide best practices section'
        ]
      },
      submitter: {
        name: 'Current Student', // This would be the logged-in student
        avatar: '/avatars/student.jpg',
        email: 'student@example.com'
      },
      submissionDate: '2024-12-15T16:30:00Z',
      status: 'graded',
      grade: 88,
      feedback: 'Excellent work on the tutorial! Your explanations are clear and the code examples are well-structured. The interactive exercises add great value. For future submissions, consider adding more real-world use cases and perhaps a section on performance optimization.',
      submissionText: `I have completed the React Components Tutorial as requested. The tutorial covers all the essential concepts including:

1. Basic component creation and structure
2. Understanding and using props effectively
3. State management with hooks
4. Component composition patterns
5. Best practices for reusable components

The tutorial includes 15 interactive code examples, 5 hands-on exercises, and a comprehensive quiz at the end. I've also created a companion GitHub repository with all the code examples organized by difficulty level.

Key Features:
- Step-by-step explanations with visual diagrams
- Interactive code playground integration
- Real-world examples from popular libraries
- Performance optimization tips
- Common pitfalls and how to avoid them

This project took approximately 12 hours to complete, including research, writing, coding examples, and testing. The most challenging part was creating engaging interactive examples that demonstrate real-world use cases while keeping them simple enough for beginners.

I believe this tutorial will serve as a valuable resource for students learning React components and will help bridge the gap between basic concepts and practical application.`,
      attachments: [
        {
          id: 1,
          name: 'react-components-tutorial.pdf',
          size: '2.5 MB',
          type: 'application/pdf',
          uploadedDate: '2024-12-15T16:30:00Z'
        },
        {
          id: 2,
          name: 'code-examples.zip',
          size: '1.8 MB',
          type: 'application/zip',
          uploadedDate: '2024-12-15T16:30:00Z'
        },
        {
          id: 3,
          name: 'interactive-exercises.zip',
          size: '950 KB',
          type: 'application/zip',
          uploadedDate: '2024-12-15T16:30:00Z'
        },
        {
          id: 4,
          name: 'tutorial-demo-video.mp4',
          size: '45 MB',
          type: 'video/mp4',
          uploadedDate: '2024-12-15T16:30:00Z'
        }
      ],
      reviewedBy: {
        name: 'Sarah Mentor',
        avatar: '/avatars/sarah.jpg'
      },
      reviewedDate: '2024-12-16T14:20:00Z',
      timeSpent: '12 hours',
      isLate: false,
      rubric: {
        criteria: [
          {
            name: 'Content Quality',
            score: 90,
            maxScore: 100,
            feedback: 'Excellent content coverage with clear explanations'
          },
          {
            name: 'Code Examples',
            score: 92,
            maxScore: 100,
            feedback: 'Well-structured examples with good variety'
          },
          {
            name: 'Interactive Elements',
            score: 85,
            maxScore: 100,
            feedback: 'Good interactive exercises, could use more complexity'
          },
          {
            name: 'Organization',
            score: 88,
            maxScore: 100,
            feedback: 'Well-organized structure, easy to follow'
          },
          {
            name: 'Best Practices',
            score: 82,
            maxScore: 100,
            feedback: 'Good coverage of best practices, missing some advanced patterns'
          }
        ]
      },
      submissionHistory: [
        {
          id: 1,
          date: '2024-12-15T16:30:00Z',
          action: 'Submission created',
          user: 'Current Student',
          type: 'submitted'
        },
        {
          id: 2,
          date: '2024-12-16T10:15:00Z',
          action: 'Review started',
          user: 'Sarah Mentor',
          type: 'review_started'
        },
        {
          id: 3,
          date: '2024-12-16T14:20:00Z',
          action: 'Review completed and graded',
          user: 'Sarah Mentor',
          type: 'graded'
        }
      ],
      allowedActions: {
        canEdit: false, // Usually false after grading
        canResubmit: false,
        canViewFeedback: true
      }
    };

    setTimeout(() => {
      setSubmission(mockSubmission);
      setLoading(false);
    }, 1000);
  }, [submissionId]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'graded': return 'success';
      case 'submitted': return 'info';
      case 'pending_review': return 'warning';
      case 'needs_revision': return 'error';
      case 'draft': return 'default';
      default: return 'default';
    }
  };

  const getGradeColor = (score, maxScore) => {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 90) return 'success';
    if (percentage >= 80) return 'info';
    if (percentage >= 70) return 'warning';
    return 'error';
  };

  const getTimelineIcon = (type) => {
    switch (type) {
      case 'submitted': return <Assignment />;
      case 'review_started': return <Person />;
      case 'graded': return <Grade />;
      default: return <Schedule />;
    }
  };

  const getTimelineColor = (type) => {
    switch (type) {
      case 'submitted': return 'primary';
      case 'review_started': return 'info';
      case 'graded': return 'success';
      default: return 'grey';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('zip')) return '📦';
    if (type.includes('video')) return '🎥';
    if (type.includes('image')) return '🖼️';
    return '📎';
  };

  const handleDownload = (attachment) => {
    console.log('Downloading:', attachment.name);
  };

  const isOverdue = () => {
    return submission.isLate;
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
          Loading submission details...
        </Typography>
      </Box>
    );
  }

  if (!submission) {
    return (
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography variant="h6" color="error">
          Submission not found
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton onClick={onBack} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h4" component="h1">
            My Submission
          </Typography>
        </Box>
        
        {submission.allowedActions.canEdit && (
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton
              onClick={() => onEdit && onEdit(submission)}
              color="primary"
            >
              <Edit />
            </IconButton>
          </Box>
        )}
      </Box>

      {/* Status Alert */}
      {isOverdue() && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          This submission was submitted after the due date.
        </Alert>
      )}

      {submission.status === 'graded' && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Your submission has been graded and feedback is available below.
        </Alert>
      )}

      {/* Task & Submission Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assignment sx={{ mr: 1, fontSize: 32 }} />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h5" component="h2">
                    {submission.task.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {submission.task.description}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    <Chip
                      label={submission.status.replace('_', ' ').toUpperCase()}
                      color={getStatusColor(submission.status)}
                      size="small"
                    />
                    {submission.isLate && (
                      <Chip
                        label="LATE SUBMISSION"
                        color="error"
                        size="small"
                      />
                    )}
                  </Box>
                </Box>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Due Date:
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(submission.task.dueDate)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Submitted:
                  </Typography>
                  <Typography variant="body1">
                    {formatDate(submission.submissionDate)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Time Spent:
                  </Typography>
                  <Typography variant="body1">
                    {submission.timeSpent}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Estimated Time:
                  </Typography>
                  <Typography variant="body1">
                    {submission.task.estimatedHours} hours
                  </Typography>
                </Grid>
              </Grid>
            </Grid>

            <Grid item xs={12} md={4}>
              {submission.status === 'graded' ? (
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h3" color={getGradeColor(submission.grade, submission.task.maxScore)}>
                    {submission.grade}/{submission.task.maxScore}
                  </Typography>
                  <Typography variant="body1" color="text.secondary" gutterBottom>
                    Final Grade
                  </Typography>
                  <Rating
                    value={submission.grade / 20}
                    readOnly
                    precision={0.1}
                    size="large"
                  />
                  <Typography variant="body2" color="text.secondary">
                    {Math.round((submission.grade / submission.task.maxScore) * 100)}%
                  </Typography>
                  
                  {submission.reviewedBy && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Reviewed by:
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 0.5 }}>
                        <Avatar src={submission.reviewedBy.avatar} sx={{ width: 24, height: 24, mr: 1 }}>
                          {submission.reviewedBy.name.charAt(0)}
                        </Avatar>
                        <Typography variant="body2">
                          {submission.reviewedBy.name}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(submission.reviewedDate)}
                      </Typography>
                    </Box>
                  )}
                </Box>
              ) : (
                <Box sx={{ textAlign: 'center' }}>
                  <Warning sx={{ fontSize: 48, color: 'warning.main', mb: 1 }} />
                  <Typography variant="h6" color="warning.main">
                    Pending Review
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Your submission is waiting to be reviewed
                  </Typography>
                </Box>
              )}
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Submission Content */}
        <Grid item xs={12} lg={8}>
          {/* Requirements Checklist */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Task Requirements
              </Typography>
              <List>
                {submission.task.requirements.map((requirement, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <CheckCircle color="success" />
                    </ListItemIcon>
                    <ListItemText primary={requirement} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Submission Text */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Submission Details
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                  {submission.submissionText}
                </Typography>
              </Paper>
            </CardContent>
          </Card>

          {/* Attachments */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Attachments ({submission.attachments.length})
              </Typography>
              
              <Grid container spacing={2}>
                {submission.attachments.map((attachment) => (
                  <Grid item xs={12} sm={6} md={4} key={attachment.id}>
                    <Paper
                      sx={{
                        p: 2,
                        border: '1px solid',
                        borderColor: 'divider',
                        cursor: 'pointer',
                        '&:hover': {
                          backgroundColor: 'action.hover'
                        }
                      }}
                      onClick={() => handleDownload(attachment)}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Typography sx={{ fontSize: 24, mr: 1 }}>
                          {getFileIcon(attachment.type)}
                        </Typography>
                        <Typography variant="subtitle2" noWrap>
                          {attachment.name}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {formatFileSize(attachment.size)}
                      </Typography>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(attachment.uploadedDate)}
                        </Typography>
                        <IconButton size="small">
                          <Download />
                        </IconButton>
                      </Box>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>

          {/* Feedback */}
          {submission.status === 'graded' && submission.feedback && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom color="primary">
                  Instructor Feedback
                </Typography>
                <Paper sx={{ p: 2, backgroundColor: 'primary.50' }}>
                  <Typography variant="body1">
                    {submission.feedback}
                  </Typography>
                </Paper>
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          {/* Grading Rubric */}
          {submission.status === 'graded' && submission.rubric && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Grading Breakdown
                </Typography>
                
                {submission.rubric.criteria.map((criterion, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2" fontWeight="bold">
                        {criterion.name}
                      </Typography>
                      <Typography variant="body2">
                        {criterion.score}/{criterion.maxScore}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(criterion.score / criterion.maxScore) * 100}
                      color={getGradeColor(criterion.score, criterion.maxScore)}
                      sx={{ mb: 0.5 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {criterion.feedback}
                    </Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Submission Timeline */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Submission Timeline
              </Typography>
              
              <Timeline>
                {submission.submissionHistory.map((event, index) => (
                  <TimelineItem key={event.id}>
                    <TimelineSeparator>
                      <TimelineDot color={getTimelineColor(event.type)}>
                        {getTimelineIcon(event.type)}
                      </TimelineDot>
                      {index < submission.submissionHistory.length - 1 && <TimelineConnector />}
                    </TimelineSeparator>
                    <TimelineContent>
                      <Typography variant="body2" fontWeight="bold">
                        {event.action}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        by {event.user}
                      </Typography>
                      <Typography variant="caption" display="block" color="text.secondary">
                        {formatDate(event.date)}
                      </Typography>
                    </TimelineContent>
                  </TimelineItem>
                ))}
              </Timeline>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MentorViewTaskSubmission;