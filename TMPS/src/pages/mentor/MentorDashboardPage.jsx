import { Container } from '@mui/material';
import MentorDashboard from '../../components/mentor/MentorDashboard';

const MentorDashboardPage = () => {
  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <MentorDashboard />
    </Container>
  );
};

export default MentorDashboardPage;
