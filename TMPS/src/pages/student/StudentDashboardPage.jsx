// src/pages/student/StudentDashboardPage.jsx
import React from 'react';
import { Container } from '@mui/material';
import StudentDashboard from '../../components/student/StudentDashboard';

const StudentDashboardPage = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <StudentDashboard />
    </Container>
  );
};

export default StudentDashboardPage;