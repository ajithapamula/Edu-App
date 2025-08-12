import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  LinearProgress,
  Avatar,
  Button,
  Divider,
  Alert,
  Badge,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Assignment,
  VideoLibrary,
  Schedule,
  TrendingUp,
  CheckCircle,
  Pending,
  Warning,
  Notifications,
  Download,
  PlayArrow,
  Star,
  AccessTime,
  School,
  Assignment as TaskIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { Grid } from '@mui/material'; // Alternative import for MUI v5

const StudentDashboard = () => {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Mock data - replace with API call
  useEffect(() => {
    const mockData = {
      student: {
        name: 'Alice Johnson',
        email: 'alice.johnson@email.com',
        course: 'Full Stack Development',
        enrollmentDate: '2024-01-01',
        avatar: '/avatars/alice.jpg',
        progress: 68,
        level: 'Intermediate',
        totalHours: 156
      },
      stats: {
        tasksCompleted: 12,
        totalTasks: 18,
        documentsViewed: 24,
        recordingsWatched: 15,
        averageGrade: 85
      },
      recentTasks: [
        {
          id: 1,
          title: 'Build React To-Do App',
          course: 'Full Stack Development',
          dueDate: '2024-01-25',
          status: 'submitted',
          grade: 88,
          priority: 'high'
        },
        {
          id: 2,
          title: 'JavaScript ES6 Features Quiz',
          course: 'Full Stack Development',
          dueDate: '2024-01-20',
          status: 'graded',
          grade: 92,
          priority: 'medium'
        },
        {
          id: 3,
          title: 'CSS Grid Layout Assignment',
          course: 'Full Stack Development',
          dueDate: '2024-01-30',
          status: 'pending',
          grade: null,
          priority: 'high'
        }
      ],
      recentDocuments: [
        {
          id: 1,
          title: 'React Hooks Guide',
          type: 'PDF',
          uploadedAt: '2024-01-15',
          size: '2.4 MB',
          views: 156
        },
        {
          id: 2,
          title: 'JavaScript Best Practices',
          type: 'PDF',
          uploadedAt: '2024-01-12',
          size: '1.8 MB',
          views: 203
        },
        {
          id: 3,
          title: 'API Design Principles',
          type: 'DOC',
          uploadedAt: '2024-01-10',
          size: '856 KB',
          views: 98
        }
      ],
      recentRecordings: [
        {
          id: 1,
          title: 'React Fundamentals - Session 1',
          duration: '2:30:45',
          uploadedAt: '2024-01-15',
          watched: true,
          progress: 100
        },
        {
          id: 2,
          title: 'JavaScript Advanced Concepts',
          duration: '1:45:30',
          uploadedAt: '2024-01-12',
          watched: false,
          progress: 0
        },
        {
          id: 3,
          title: 'API Integration Workshop',
          duration: '3:15:20',
          uploadedAt: '2024-01-10',
          watched: true,
          progress: 65
        }
      ],
      announcements: [
        {
          id: 1,
          title: 'New Assignment: Database Design',
          message: 'A new assignment has been posted for Backend Development course.',
          date: '2024-01-22',
          type: 'assignment',
          read: false
        },
        {
          id: 2,
          title: 'Mock Interview Scheduled',
          message: 'Your mock interview is scheduled for January 25th at 2:00 PM.',
          date: '2024-01-20',
          type: 'interview',
          read: true
        }
      ],
      upcomingEvents: [
        {
          id: 1,
          title: 'React Advanced Patterns',
          type: 'Live Session',
          date: '2024-01-25',
          time: '10:00 AM',
          instructor: 'John Trainer'
        },
        {
          id: 2,
          title: 'Project Review Meeting',
          type: 'Meeting',
          date: '2024-01-26',
          time: '2:00 PM',
          instructor: 'Sarah Mentor'
        }
      ]
    };

    setTimeout(() => {
      setDashboardData(mockData);
      setLoading(false);
    }, 1000);
  }, []);

  const getTaskStatusColor = (status) => {
    switch (status) {
      case 'completed':
      case 'graded': return 'success';
      case 'submitted': return 'info';
      case 'pending': return 'warning';
      case 'overdue': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const getGradeColor = (grade) => {
    if (grade >= 90) return 'success';
    if (grade >= 80) return 'info';
    if (grade >= 70) return 'warning';
    return 'error';
  };

  const handleViewTask = (taskId) => {
    navigate(`/student/tasks/view/${taskId}`);
  };

  const handleViewDocument = (docId) => {
    navigate(`/student/documents/view/${docId}`);
  };

  const handleViewRecording = (recordingId) => {
    navigate(`/student/recordings/view/${recordingId}`);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading dashboard...</Typography>
      </Box>
    );
  }

  const { student, stats, recentTasks, recentDocuments, recentRecordings, announcements, upcomingEvents } = dashboardData;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Welcome back, {student.name}!
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" component="div">
            {student.course} • {student.level} Level
          </Typography>
        </Box>
        <Box display="flex" alignItems="center" gap={2}>
          <Tooltip title="Notifications">
            <IconButton>
              <Badge badgeContent={announcements.filter(a => !a.read).length} color="primary">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>
          <Avatar src={student.avatar} sx={{ width: 48, height: 48 }}>
            {student.name.charAt(0)}
          </Avatar>
        </Box>
      </Box>

      <Grid container spacing={3}>
        <Grid xs={12} lg={8}>
          {/* Progress Overview */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" component="div" gutterBottom>
                Course Progress
              </Typography>
              <Box display="flex" alignItems="center" gap={2} mb={2}>
                <LinearProgress 
                  variant="determinate" 
                  value={student.progress} 
                  sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                />
                <Typography variant="h6" color="primary" component="div">
                  {student.progress}%
                </Typography>
              </Box>
              <Grid container spacing={2}>
                <Grid xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="success.main" component="div">
                      {stats.tasksCompleted}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" component="div">
                      Tasks Completed
                    </Typography>
                  </Box>
                </Grid>
                <Grid xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="info.main" component="div">
                      {stats.averageGrade}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary" component="div">
                      Average Grade
                    </Typography>
                  </Box>
                </Grid>
                <Grid xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="primary" component="div">
                      {stats.recordingsWatched}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" component="div">
                      Videos Watched
                    </Typography>
                  </Box>
                </Grid>
                <Grid xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h5" color="warning.main" component="div">
                      {student.totalHours}h
                    </Typography>
                    <Typography variant="caption" color="text.secondary" component="div">
                      Study Hours
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Recent Tasks */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" component="div">
                  Recent Tasks ({stats.totalTasks - stats.tasksCompleted} Pending)
                </Typography>
                <Button size="small" onClick={() => navigate('/student/tasks')}>
                  View All
                </Button>
              </Box>
              <List>
                {recentTasks.map((task, index) => (
                  <React.Fragment key={task.id}>
                    <ListItem 
                      sx={{ px: 0, cursor: 'pointer' }}
                      onClick={() => handleViewTask(task.id)}
                    >
                      <ListItemIcon>
                        <TaskIcon color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={task.title}
                        secondary={
                          <Box component="span">
                            <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                              <Chip
                                label={task.status.toUpperCase()}
                                color={getTaskStatusColor(task.status)}
                                size="small"
                              />
                              <Chip
                                label={task.priority.toUpperCase()}
                                color={getPriorityColor(task.priority)}
                                size="small"
                                variant="outlined"
                              />
                              <Typography variant="caption" component="span">
                                Due: {new Date(task.dueDate).toLocaleDateString()}
                              </Typography>
                            </Box>
                          </Box>
                        }
                      />
                      {task.grade && (
                        <Chip
                          label={`${task.grade}%`}
                          color={getGradeColor(task.grade)}
                          size="small"
                          icon={<Star />}
                        />
                      )}
                    </ListItem>
                    {index < recentTasks.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Recent Session Recordings */}
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" component="div">
                  Recent Session Recordings
                </Typography>
                <Button size="small" onClick={() => navigate('/student/recordings')}>
                  View All
                </Button>
              </Box>
              <List>
                {recentRecordings.map((recording, index) => (
                  <React.Fragment key={recording.id}>
                    <ListItem>
                      <ListItemText
                        primary={recording.title}
                        secondary={
                          <Box component="span">
                            <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                              <AccessTime fontSize="small" />
                              <Typography variant="caption" component="span">
                                {recording.duration}
                              </Typography>
                              {recording.watched ? (
                                <Chip
                                  label={`${recording.progress}% Watched`}
                                  color="success"
                                  size="small"
                                  icon={<CheckCircle />}
                                />
                              ) : (
                                <Chip
                                  label="Not Watched"
                                  color="warning"
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < recentRecordings.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid xs={12} lg={4}>
          {/* Announcements */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" component="div" gutterBottom>
                Announcements
              </Typography>
              {announcements.length === 0 ? (
                <Alert severity="info">No new announcements</Alert>
              ) : (
                <List dense>
                  {announcements.map((announcement) => (
                    <ListItem key={announcement.id} sx={{ px: 0 }}>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography 
                              variant="subtitle2" 
                              component="span"
                              sx={{ 
                                fontWeight: announcement.read ? 'normal' : 'bold',
                                flexGrow: 1
                              }}
                            >
                              {announcement.title}
                            </Typography>
                            {!announcement.read && (
                              <Box 
                                sx={{ 
                                  width: 8, 
                                  height: 8, 
                                  borderRadius: '50%', 
                                  bgcolor: 'primary.main' 
                                }} 
                              />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box component="span">
                            <Typography variant="body2" color="text.secondary" component="span">
                              {announcement.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" component="div">
                              {new Date(announcement.date).toLocaleDateString()}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>

          {/* Upcoming Events */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" component="div" gutterBottom>
                Upcoming Events
              </Typography>
              {upcomingEvents.length === 0 ? (
                <Alert severity="info">No upcoming events</Alert>
              ) : (
                <List dense>
                  {upcomingEvents.map((event) => (
                    <ListItem key={event.id} sx={{ px: 0 }}>
                      <ListItemIcon>
                        <Schedule color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary={event.title}
                        secondary={
                          <Box component="span">
                            <Typography variant="body2" color="text.secondary" component="span">
                              {event.type} • {event.instructor}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" component="div">
                              {new Date(event.date).toLocaleDateString()} at {event.time}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>

          {/* Recent Documents */}
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" component="div">
                  Recent Documents
                </Typography>
                <Button size="small" onClick={() => navigate('/student/documents')}>
                  View All
                </Button>
              </Box>
              <List dense>
                {recentDocuments.map((doc) => (
                  <ListItem 
                    key={doc.id} 
                    sx={{ px: 0, cursor: 'pointer' }}
                    onClick={() => handleViewDocument(doc.id)}
                  >
                    <ListItemIcon>
                      <Assignment color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={doc.title}
                      secondary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="caption">
                            {doc.type} • {doc.size}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {doc.views} views
                          </Typography>
                        </Box>
                      }
                    />
                    <IconButton 
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        // Handle download
                      }}
                    >
                      <Download />
                    </IconButton>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StudentDashboard;