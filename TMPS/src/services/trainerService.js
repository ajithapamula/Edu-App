// Import the default export from api.js
import api from './api.js';

// Or you can alias it if you prefer the name 'apiService'
// import api as apiService from './api.js';

const trainerService = {
  // Get all trainer tasks
  getTasks: async () => {
    try {
      const response = await api.get('/trainer/tasks');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get specific task by ID
  getTask: async (taskId) => {
    try {
      const response = await api.get(`/trainer/tasks/${taskId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Submit task
  submitTask: async (taskId, submission) => {
    try {
      const response = await api.post(`/trainer/tasks/${taskId}/submit`, submission);
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get course documents
  getCourseDocuments: async () => {
    try {
      const response = await api.get('/trainer/documents');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get session recordings
  getSessionRecordings: async () => {
    try {
      const response = await api.get('/trainer/recordings');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get mock interview results
  getMockInterviewResults: async () => {
    try {
      const response = await api.get('/trainer/mock-interviews');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get daily standup results
  getDailyStandupResults: async () => {
    try {
      const response = await api.get('/trainer/daily-standups');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get mock test results
  getMockTestResults: async () => {
    try {
      const response = await api.get('/trainer/mock-tests');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get student results
  getStudentResults: async () => {
    try {
      const response = await api.get('/trainer/student-results');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get sessions
  getSessions: async () => {
    try {
      const response = await api.get('/trainer/sessions');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  },

  // Get test compilation
  getTestCompilation: async () => {
    try {
      const response = await api.get('/trainer/test-compilation');
      return response.data;
    } catch (error) {
      throw error.response?.data || error;
    }
  }
};

export default trainerService;