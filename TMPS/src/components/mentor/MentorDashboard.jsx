import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Avatar
} from '@mui/material';
import {
  People,
  Assignment,
  CheckCircle,
  Pending,
  TrendingUp,
  Schedule
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const MentorDashboard = () => {
  const navigate = useNavigate();

  const stats = [
    {
      title: 'Students Assigned',
      value: '12',
      icon: <People />,
      color: '#1976d2'
    },
    {
      title: 'Pending Reviews',
      value: '8',
      icon: <Pending />,
      color: '#f57c00'
    },
    {
      title: 'Completed Reviews',
      value: '45',
      icon: <CheckCircle />,
      color: '#388e3c'
    },
    {
      title: 'Average Score',
      value: '8.5',
      icon: <TrendingUp />,
      color: '#7b1fa2'
    }
  ];

  const pendingSubmissions = [
    {
      id: 1,
      student: 'Alice Johnson',
      task: 'React Component Design',
      course: 'Full Stack Development',
      submittedDate: '2024-01-20',
      dueDate: '2024-01-22',
      priority: 'High'
    },
    {
      id: 2,
      student: 'Bob Smith',
      task: 'Database Schema',
      course: 'Backend Development',
      submittedDate: '2024-01-19',
      dueDate: '2024-01-21',
      priority: 'Medium'
    },
    {
      id: 3,
      student: 'Charlie Brown',
      task: 'API Integration',
      course: 'Full Stack Development',
      submittedDate: '2024-01-18',
      dueDate: '2024-01-20',
      priority: 'High'
    }
  ];

  const studentProgress = [
    {
      student: 'Alice Johnson',
      course: 'Full Stack Development',
      progress: 85,
      tasksCompleted: 15,
      totalTasks: 18,
      lastActivity: '2 hours ago'
    },
    {
      student: 'Bob Smith',
      course: 'Backend Development',
      progress: 72,
      tasksCompleted: 12,
      totalTasks: 16,
      lastActivity: '1 day ago'
    },
    {
      student: 'Charlie Brown',
      course: 'Full Stack Development',
      progress: 91,
      tasksCompleted: 16,
      totalTasks: 18,
      lastActivity: '4 hours ago'
    },
    {
      student: 'Diana Prince',
      course: 'Frontend Development',
      progress: 68,
      tasksCompleted: 10,
      totalTasks: 14,
      lastActivity: '3 hours ago'
    }
  ];

  const recentActivities = [
    {
      title: 'Reviewed submission from Alice Johnson',
      time: '1 hour ago',
      type: 'review'
    },
    {
      title: 'Added feedback for React Components task',
      time: '3 hours ago',
      type: 'feedback'
    },
    {
      title: 'Scheduled mock interview with Bob Smith',
      time: '5 hours ago',
      type: 'interview'
    },
    {
      title: 'Updated task rubric for Database Design',
      time: '1 day ago',
      type: 'update'
    }
  ];

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'High': return 'error';
      case 'Medium': return 'warning';
      case 'Low': return 'success';
      default: return 'default';
    }
  };

  const getInitials = (name) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Mentor Dashboard
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      {stat.title}
                    </Typography>
                    <Typography variant="h4" component="div" sx={{ color: stat.color }}>
                      {stat.value}
                    </Typography>
                  </Box>
                  <Box sx={{ color: stat.color }}>
                    {React.cloneElement(stat.icon, { fontSize: 'large' })}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Pending Submissions */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Pending Task Reviews
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/mentor/task-submissions')}
              >
                View All
              </Button>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Student</TableCell>
                    <TableCell>Task</TableCell>
                    <TableCell>Course</TableCell>
                    <TableCell>Submitted</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {pendingSubmissions.map((submission) => (
                    <TableRow key={submission.id}>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Avatar sx={{ width: 32, height: 32, fontSize: '14px' }}>
                            {getInitials(submission.student)}
                          </Avatar>
                          {submission.student}
                        </Box>
                      </TableCell>
                      <TableCell>{submission.task}</TableCell>
                      <TableCell>{submission.course}</TableCell>
                      <TableCell>{submission.submittedDate}</TableCell>
                      <TableCell>
                        <Chip
                          label={submission.priority}
                          size="small"
                          color={getPriorityColor(submission.priority)}
                        />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => navigate(`/mentor/task-submissions/view/${submission.id}`)}
                        >
                          Review
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          {/* Student Progress */}
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Student Progress Overview
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/mentor/student-results')}
              >
                View Details
              </Button>
            </Box>
            {studentProgress.map((student, index) => (
              <Box
                key={index}
                sx={{
                  p: 2,
                  border: '1px solid #e0e0e0',
                  borderRadius: 1,
                  mb: 2,
                  '&:last-child': { mb: 0 }
                }}
              >
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Avatar sx={{ width: 40, height: 40 }}>
                      {getInitials(student.student)}
                    </Avatar>
                    <Box>
                      <Typography variant="subtitle2" fontWeight="medium">
                        {student.student}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {student.course}
                      </Typography>
                    </Box>
                  </Box>
                  <Box textAlign="right">
                    <Typography variant="h6" color="primary">
                      {student.progress}%
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {student.tasksCompleted}/{student.totalTasks} tasks
                    </Typography>
                  </Box>
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2" color="text.secondary">
                    Last activity: {student.lastActivity}
                  </Typography>
                  <Button
                    size="small"
                    variant="text"
                    onClick={() => navigate(`/mentor/student-results/view/${student.student}`)}
                  >
                    View Details
                  </Button>
                </Box>
              </Box>
            ))}
          </Paper>
        </Grid>

        {/* Quick Actions & Recent Activities */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box display="flex" flexDirection="column" gap={2}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Assignment />}
                onClick={() => navigate('/mentor/task-submissions')}
              >
                Review Submissions
              </Button>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Schedule />}
                onClick={() => navigate('/mentor/mock-interviews')}
              >
                Schedule Interview
              </Button>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<People />}
                onClick={() => navigate('/mentor/student-results')}
              >
                Student Analytics
              </Button>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<CheckCircle />}
                onClick={() => navigate('/mentor/course-documents/add')}
              >
                Add Resource
              </Button>
            </Box>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activities
            </Typography>
            <Box>
              {recentActivities.map((activity, index) => (
                <Box
                  key={index}
                  sx={{
                    py: 2,
                    borderBottom: index !== recentActivities.length - 1 ? '1px solid #e0e0e0' : 'none'
                  }}
                >
                  <Typography variant="body2" sx={{ mb: 0.5 }}>
                    {activity.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {activity.time}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MentorDashboard;