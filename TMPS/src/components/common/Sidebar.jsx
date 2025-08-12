import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider
} from '@mui/material';
import {
  Dashboard,
  School,
  People,
  Assignment,
  VideoLibrary,
  Description,
  Quiz,
  Analytics,
  MeetingRoom,
  PendingActions,
  VideoCall
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const drawerWidth = 240;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const getMenuItems = () => {
    const baseItems = [
      {
        text: 'Dashboard',
        icon: <Dashboard />,
        path: `/${user?.role}/dashboard`
      }
    ];

    switch (user?.role) {
      case 'trainer':
        return [
          ...baseItems,
          {
            text: 'Course Documents',
            icon: <Description />,
            path: '/trainer/course-documents'
          },
          {
            text: 'Session Recordings',
            icon: <VideoLibrary />,
            path: '/trainer/session-recordings'
          },
          {
            text: 'Trainer Tasks',
            icon: <Assignment />,
            path: '/trainer/tasks'
          },
          {
            text: 'Sessions',
            icon: <MeetingRoom />,
            path: '/trainer/sessions'
          },
          {
            text: 'Mock Interviews',
            icon: <People />,
            path: '/trainer/mock-interviews'
          },
          {
            text: 'Daily Standups',
            icon: <PendingActions />,
            path: '/trainer/daily-standups'
          },
          {
            text: 'Mock Tests',
            icon: <Quiz />,
            path: '/trainer/mock-tests'
          },
          {
            text: 'Student Results',
            icon: <Analytics />,
            path: '/trainer/student-results'
          },
          {
            text: 'Test Compilation',
            icon: <School />,
            path: '/trainer/test-compilation'
          }
        ];

      case 'mentor':
        return [
          ...baseItems,
          {
            text: 'Course Documents',
            icon: <Description />,
            path: '/mentor/course-documents'
          },
          {
            text: 'Session Recordings',
            icon: <VideoLibrary />,
            path: '/mentor/session-recordings'
          },
          {
            text: 'Trainer Tasks',
            icon: <Assignment />,
            path: '/mentor/tasks'
          },
          {
            text: 'Task Submissions',
            icon: <PendingActions />,
            path: '/mentor/task-submissions'
          },
          {
            text: 'Student Results',
            icon: <Analytics />,
            path: '/mentor/student-results'
          },
          {
            text: 'Mock Interviews',
            icon: <People />,
            path: '/mentor/mock-interviews'
          },
          {
            text: 'Daily Standups',
            icon: <PendingActions />,
            path: '/mentor/daily-standups'
          },
          {
            text: 'Mock Tests',
            icon: <Quiz />,
            path: '/mentor/mock-tests'
          }
        ];

      case 'student':
        return [
          ...baseItems,
          {
            text: 'Course Documents',
            icon: <Description />,
            path: '/student/course-documents'
          },
          {
            text: 'Session Recordings',
            icon: <VideoLibrary />,
            path: '/student/session-recordings'
          },
          {
            text: 'Trainer Tasks',
            icon: <Assignment />,
            path: '/student/tasks'
          },
          {
            text: 'Task Submissions',
            icon: <PendingActions />,
            path: '/student/task-submissions'
          },
          {
            text: 'Mock Interviews',
            icon: <People />,
            path: '/student/mock-interviews'
          },
          {
            text: 'Daily Standups',
            icon: <VideoCall />,
            path: '/student/daily-standups'
          },
          {
            text: 'Mock Tests',
            icon: <Quiz />,
            path: '/student/mock-tests'
          }
        ];

      default:
        return baseItems;
    }
  };

  const menuItems = getMenuItems();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <List sx={{ mt: 1 }}>
        {menuItems.map((item, index) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: '#e3f2fd',
                  '&:hover': {
                    backgroundColor: '#bbdefb',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ color: location.pathname === item.path ? '#1976d2' : 'inherit' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                sx={{ 
                  '& .MuiListItemText-primary': {
                    color: location.pathname === item.path ? '#1976d2' : 'inherit',
                    fontWeight: location.pathname === item.path ? 600 : 400
                  }
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Sidebar;