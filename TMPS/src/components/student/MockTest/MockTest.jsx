// src/components/student/MockTest/StudentMockTestsList.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Container,
  Grid,
  useTheme
} from '@mui/material';
import {
  Quiz as QuizIcon,
  Timer as TimerIcon,
  TrendingUp as TrendingUpIcon,
  School as SchoolIcon
} from '@mui/icons-material';

const StudentMockTestsList = () => {
  const navigate = useNavigate();
  const theme = useTheme();

  const handleStartMockTest = () => {
    navigate('/student/mock-tests/start');
  };

  const mockTestStats = [
    {
      icon: <QuizIcon sx={{ fontSize: 40, color: theme.palette.primary.main }} />,
      title: 'Total Tests',
      value: '25+',
      description: 'Available mock tests'
    },
    {
      icon: <TimerIcon sx={{ fontSize: 40, color: theme.palette.success.main }} />,
      title: 'Average Duration',
      value: '30 min',
      description: 'Per test session'
    },
    {
      icon: <TrendingUpIcon sx={{ fontSize: 40, color: theme.palette.warning.main }} />,
      title: 'Success Rate',
      value: '78%',
      description: 'Student average'
    },
    {
      icon: <SchoolIcon sx={{ fontSize: 40, color: theme.palette.info.main }} />,
      title: 'Skill Level',
      value: 'All Levels',
      description: 'Beginner to Expert'
    }
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header Section */}
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography 
          variant="h3" 
          component="h1" 
          gutterBottom
          sx={{ 
            fontWeight: 'bold',
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 2
          }}
        >
          Mock Test
        </Typography>
        <Typography 
          variant="h6" 
          color="text.secondary" 
          sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}
        >
          Test your knowledge with AI-generated questions tailored to your skill level and expertise
        </Typography>
      </Box>

      {/* Stats Section */}
      <Grid container spacing={3} sx={{ mb: 6 }}>
        {mockTestStats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              elevation={2}
              sx={{ 
                height: '100%',
                textAlign: 'center',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: theme.shadows[8]
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box sx={{ mb: 2 }}>
                  {stat.icon}
                </Box>
                <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
                  {stat.value}
                </Typography>
                <Typography variant="h6" color="text.primary" sx={{ mb: 1 }}>
                  {stat.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {stat.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Start Test Button */}
      <Box sx={{ textAlign: 'center' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleStartMockTest}
          startIcon={<QuizIcon />}
          sx={{
            py: 2,
            px: 6,
            fontSize: '1.2rem',
            fontWeight: 'bold',
            borderRadius: 3,
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
            '&:hover': {
              background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.secondary.dark})`,
              transform: 'translateY(-2px)',
              boxShadow: theme.shadows[8]
            },
            transition: 'all 0.2s ease-in-out'
          }}
        >
          Start Mock Test
        </Button>
      </Box>
    </Container>
  );
};

export default StudentMockTestsList;