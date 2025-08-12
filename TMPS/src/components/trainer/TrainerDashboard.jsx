import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Paper,
  Button
} from '@mui/material';
import {
  People,
  Assignment,
  VideoLibrary,
  Description,
  TrendingUp,
  Quiz,
  MeetingRoom
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const TrainerDashboard = () => {
  const navigate = useNavigate();

  // ✅ Move console.log OUTSIDE the return statement
  console.log('TrainerDashboard component rendering');

  const stats = [
    {
      title: 'Total Students',
      value: '45',
      icon: <People />,
      color: '#1976d2'
    },
    {
      title: 'Active Courses',
      value: '8',
      icon: <Description />,
      color: '#388e3c'
    },
    {
      title: 'Pending Tasks',
      value: '12',
      icon: <Assignment />,
      color: '#f57c00'
    },
    {
      title: 'Sessions Completed',
      value: '156',
      icon: <VideoLibrary />,
      color: '#7b1fa2'
    }
  ];

  const quickActions = [
    {
      title: 'Add Course Document',
      description: 'Upload new course materials',
      action: () => navigate('/trainer/course-documents/add'),
      color: '#1976d2'
    },
    {
      title: 'Create New Task',
      description: 'Assign new task to students',
      action: () => navigate('/trainer/tasks/add'),
      color: '#388e3c'
    },
    {
      title: 'Upload Session Recording',
      description: 'Add new session recording',
      action: () => navigate('/trainer/session-recordings/add'),
      color: '#f57c00'
    },
    {
      title: 'View Student Results',
      description: 'Check student performance',
      action: () => navigate('/trainer/student-results'),
      color: '#7b1fa2'
    }
  ];

  const recentActivities = [
    {
      title: 'New student enrolled in Full Stack Development',
      time: '2 hours ago',
      type: 'enrollment'
    },
    {
      title: 'Task submission received from John Doe',
      time: '4 hours ago',
      type: 'submission'
    },
    {
      title: 'Session recording uploaded for React Basics',
      time: '1 day ago',
      type: 'upload'
    },
    {
      title: 'Mock interview scheduled for tomorrow',
      time: '2 days ago',
      type: 'interview'
    }
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Trainer Dashboard
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
        {/* Quick Actions */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              {quickActions.map((action, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      transition: 'transform 0.2s',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        boxShadow: 3
                      }
                    }}
                    onClick={action.action}
                  >
                    <CardContent>
                      <Typography variant="h6" sx={{ color: action.color, mb: 1 }}>
                        {action.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {action.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12} md={4}>
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

export default TrainerDashboard;