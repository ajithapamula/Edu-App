export const mockUsers = [
  {
    id: 1,
    email: 'trainer@tms.com',
    password: 'trainer123',
    role: 'trainer',
    name: 'John Trainer',
    token: 'mock_trainer_token_123'
  },
  {
    id: 2,
    email: 'mentor@tms.com',
    password: 'mentor123',
    role: 'mentor',
    name: 'Jane Mentor',
    token: 'mock_mentor_token_456'
  },
  {
    id: 3,
    email: 'student@tms.com',
    password: 'student123',
    role: 'student',
    name: 'Mike Student',
    token: 'mock_student_token_789'
  }
];

// Mock API delay simulation
export const mockDelay = (ms = 800) => new Promise(resolve => setTimeout(resolve, ms));