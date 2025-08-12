import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  ButtonGroup
} from '@mui/material';
import TrainerRegisterForm from '../../components/auth/TrainerRegisterForm';
import StudentRegisterForm from '../../components/auth/StudentRegisterForm';
import { useNavigate } from 'react-router-dom';

const RegisterPage = () => {
  const [selectedRole, setSelectedRole] = useState('trainer');
  const navigate = useNavigate();

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="#f5f5f5"
      py={4}
    >
      <Box sx={{ maxWidth: 800, width: '100%', mx: 2 }}>
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ textAlign: 'center', p: 3 }}>
            <Typography variant="h4" component="h1" gutterBottom>
              Join TMS Platform
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Choose your role to get started
            </Typography>
            
            <ButtonGroup variant="outlined" size="large" sx={{ mb: 2 }}>
              <Button
                variant={selectedRole === 'trainer' ? 'contained' : 'outlined'}
                onClick={() => setSelectedRole('trainer')}
              >
                Register as Trainer
              </Button>
              <Button
                variant={selectedRole === 'student' ? 'contained' : 'outlined'}
                onClick={() => setSelectedRole('student')}
              >
                Register as Student
              </Button>
            </ButtonGroup>

            <Typography variant="body2" color="text.secondary">
              Already have an account?{' '}
              <Button variant="text" onClick={() => navigate('/login')}>
                Login here
              </Button>
            </Typography>
          </CardContent>
        </Card>

        {selectedRole === 'trainer' ? <TrainerRegisterForm /> : <StudentRegisterForm />}
      </Box>
    </Box>
  );
};

export default RegisterPage;