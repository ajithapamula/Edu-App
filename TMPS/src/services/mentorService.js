import api from './api';

const mentorService = {
  // Course Documents
  getCourseDocuments: async () => {
    const response = await api.get('/mentor/course-documents');
    return response.data;
  },

  addCourseDocument: async (documentData) => {
    const response = await api.post('/mentor/course-documents', documentData);
    return response.data;
  },

  deleteCourseDocument: async (documentId) => {
    const response = await api.delete(`/mentor/course-documents/${documentId}`);
    return response.data;
  },

  // Session Recordings
  getSessionRecordings: async () => {
    const response = await api.get('/mentor/session-recordings');
    return response.data;
  },

  addSessionRecording: async (recordingData) => {
    const response = await api.post('/mentor/session-recordings', recordingData);
    return response.data;
  },

  deleteSessionRecording: async (recordingId) => {
    const response = await api.delete(`/mentor/session-recordings/${recordingId}`);
    return response.data;
  },

  // Trainer Tasks
  getTrainerTasks: async () => {
    const response = await api.get('/mentor/trainer-tasks');
    return response.data;
  },

  addTrainerTask: async (taskData) => {
    const response = await api.post('/mentor/trainer-tasks', taskData);
    return response.data;
  },

  deleteTrainerTask: async (taskId) => {
    const response = await api.delete(`/mentor/trainer-tasks/${taskId}`);
    return response.data;
  },

  // Task Submissions
  getTaskSubmissions: async () => {
    const response = await api.get('/mentor/task-submissions');
    return response.data;
  },

  reviewTaskSubmission: async (submissionId, reviewData) => {
    const response = await api.put(`/mentor/task-submissions/${submissionId}/review`, reviewData);
    return response.data;
  },

  // Mock Interviews
  getMockInterviews: async () => {
    const response = await api.get('/mentor/mock-interviews');
    return response.data;
  },

  // Daily Standups
  getDailyStandups: async () => {
    const response = await api.get('/mentor/daily-standups');
    return response.data;
  },

  // Mock Tests
  getMockTests: async () => {
    const response = await api.get('/mentor/mock-tests');
    return response.data;
  },

  // Student Results
  getStudentResults: async () => {
    const response = await api.get('/mentor/student-results');
    return response.data;
  },

  // Sessions
  getSessions: async () => {
    const response = await api.get('/mentor/sessions');
    return response.data;
  },

  // Test Compilation
  getTestCompilation: async () => {
    const response = await api.get('/mentor/test-compilation');
    return response.data;
  },

  // Dashboard Data
  getDashboardData: async () => {
    const response = await api.get('/mentor/dashboard');
    return response.data;
  },
};

export default mentorService;