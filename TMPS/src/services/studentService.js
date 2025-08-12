import api from './api';

const studentResultsService = {
  // Get all student results (for trainer)
  getAllStudentResults: async () => {
    try {
      const response = await api.get('/trainer/student-results/lists');
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Student results fetched successfully'
      };
    } catch (error) {
      console.error('Error fetching all student results:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Failed to fetch student results',
        data: []
      };
    }
  },

  // Get specific student result by ID
  getStudentResult: async (resultId) => {
    try {
      const response = await api.get(`/trainer/student-results/list/${resultId}`);
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Student result fetched successfully'
      };
    } catch (error) {
      console.error('Error fetching student result:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Failed to fetch student result',
        data: null
      };
    }
  },

  // Update student result (if you have update functionality)
  updateStudentResult: async (resultId, updateData) => {
    try {
      const response = await api.put(`/trainer/student-results/list/${resultId}`, updateData);
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Student result updated successfully'
      };
    } catch (error) {
      console.error('Error updating student result:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Failed to update student result',
        data: null
      };
    }
  },

  // Delete student result (if you have delete functionality)
  deleteStudentResult: async (resultId) => {
    try {
      const response = await api.delete(`/trainer/student-results/list/${resultId}`);
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Student result deleted successfully'
      };
    } catch (error) {
      console.error('Error deleting student result:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Failed to delete student result',
        data: null
      };
    }
  },

  // Get student results with filters
  getFilteredStudentResults: async (filters = {}) => {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters.testType) queryParams.append('test_type', filters.testType);
      if (filters.status) queryParams.append('status', filters.status);
      if (filters.studentId) queryParams.append('student_id', filters.studentId);
      if (filters.dateFrom) queryParams.append('date_from', filters.dateFrom);
      if (filters.dateTo) queryParams.append('date_to', filters.dateTo);
      if (filters.search) queryParams.append('search', filters.search);
      
      const url = `/trainer/student-results/lists${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const response = await api.get(url);
      
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Filtered student results fetched successfully'
      };
    } catch (error) {
      console.error('Error fetching filtered student results:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Failed to fetch filtered student results',
        data: []
      };
    }
  },

  // Get student results statistics
  getStudentResultsStats: async () => {
    try {
      const response = await api.get('/trainer/student-results/stats');
      return {
        success: true,
        data: response.data.data || response.data,
        message: response.data.message || 'Statistics fetched successfully'
      };
    } catch (error) {
      console.error('Error fetching student results stats:', error);
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Failed to fetch statistics',
        data: null
      };
    }
  }
};

export default studentResultsService;