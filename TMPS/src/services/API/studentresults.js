// src/services/API/studentresults.js
import { apiRequest } from './index';

export const studentResultsAPI = {
  // Get all student results - GET /api/trainer/student-results/lists
  getAll: async () => {
    try {
      console.log('API: Fetching all student results');
      
      const response = await apiRequest('/api/trainer/student-results/lists', {
        method: 'GET'
      });
      
      console.log('API Response for getAll student results:', response);
      
      // Handle different response structures
      if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else if (response && response.results && Array.isArray(response.results)) {
        return response.results;
      } else if (response && response.student_results && Array.isArray(response.student_results)) {
        return response.student_results;
      } else {
        console.warn('Unexpected response structure:', response);
        return [];
      }
    } catch (error) {
      console.error('API Error in getAll:', error);
      throw new Error(`Failed to fetch student results: ${error.message}`);
    }
  },

  // Get specific student result - GET /api/trainer/student-results/list/{id}
  getById: async (id) => {
    try {
      if (!id) {
        throw new Error('Student result ID is required');
      }
      
      console.log('API: Fetching student result with ID:', id);
      
      const response = await apiRequest(`/api/trainer/student-results/list/${id}`, {
        method: 'GET'
      });
      
      console.log('API Response for getById:', response);
      
      // Handle different response structures
      if (response && response.data) {
        return response.data;
      } else if (response && response.result) {
        return response.result;
      } else if (response && response.student_result) {
        return response.student_result;
      } else {
        return response;
      }
    } catch (error) {
      console.error('API Error in getById:', error);
      throw new Error(`Failed to fetch student result: ${error.message}`);
    }
  },

  // Update student result - PUT /api/trainer/student-results/list/{id}
  update: async (id, updateData) => {
    try {
      if (!id) {
        throw new Error('Student result ID is required');
      }
      
      if (!updateData || Object.keys(updateData).length === 0) {
        throw new Error('Update data is required');
      }
      
      console.log('API: Updating student result with ID:', id);
      console.log('API: Update data:', updateData);
      
      // Validate required fields
      if (updateData.obtained_marks !== undefined && updateData.obtained_marks < 0) {
        throw new Error('Obtained marks cannot be negative');
      }
      
      if (updateData.total_marks !== undefined && updateData.total_marks <= 0) {
        throw new Error('Total marks must be greater than 0');
      }
      
      // Calculate percentage if marks are provided
      if (updateData.obtained_marks !== undefined && updateData.total_marks !== undefined) {
        updateData.percentage = (updateData.obtained_marks / updateData.total_marks) * 100;
      }
      
      const response = await apiRequest(`/api/trainer/student-results/list/${id}`, {
        method: 'PUT',
        body: JSON.stringify(updateData)
      });
      
      console.log('API Response for update:', response);
      
      if (response && response.error) {
        throw new Error(response.error);
      }
      
      return response;
    } catch (error) {
      console.error('API Error in update:', error);
      throw new Error(`Failed to update student result: ${error.message}`);
    }
  },

  // Delete student result - DELETE /api/trainer/student-results/list/{id}
  remove: async (id) => {
    try {
      if (!id) {
        throw new Error('Student result ID is required');
      }
      
      console.log('API: Deleting student result with ID:', id);
      
      const response = await apiRequest(`/api/trainer/student-results/list/${id}`, {
        method: 'DELETE'
      });
      
      console.log('API Response for remove:', response);
      return response;
    } catch (error) {
      console.error('API Error in remove:', error);
      throw new Error(`Failed to delete student result: ${error.message}`);
    }
  },

  // Search and filter student results
  search: async (searchParams) => {
    try {
      console.log('API: Searching student results with params:', searchParams);
      
      // Build query string
      const queryParams = new URLSearchParams();
      
      if (searchParams.query) queryParams.append('q', searchParams.query);
      if (searchParams.student_name) queryParams.append('student_name', searchParams.student_name);
      if (searchParams.student_email) queryParams.append('student_email', searchParams.student_email);
      if (searchParams.test_title) queryParams.append('test_title', searchParams.test_title);
      if (searchParams.test_type && searchParams.test_type !== 'all') {
        queryParams.append('test_type', searchParams.test_type);
      }
      if (searchParams.status && searchParams.status !== 'all') {
        queryParams.append('status', searchParams.status);
      }
      if (searchParams.date_from) queryParams.append('date_from', searchParams.date_from);
      if (searchParams.date_to) queryParams.append('date_to', searchParams.date_to);
      if (searchParams.min_percentage) queryParams.append('min_percentage', searchParams.min_percentage);
      if (searchParams.max_percentage) queryParams.append('max_percentage', searchParams.max_percentage);
      if (searchParams.page) queryParams.append('page', searchParams.page);
      if (searchParams.limit) queryParams.append('limit', searchParams.limit);
      if (searchParams.sort_by) queryParams.append('sort_by', searchParams.sort_by);
      if (searchParams.sort_order) queryParams.append('sort_order', searchParams.sort_order);
      
      const queryString = queryParams.toString();
      const endpoint = `/api/trainer/student-results/lists${queryString ? `?${queryString}` : ''}`;
      
      const response = await apiRequest(endpoint, {
        method: 'GET'
      });
      
      console.log('API Response for search:', response);
      
      // Handle different response structures
      if (response && response.data && Array.isArray(response.data)) {
        return {
          results: response.data,
          total: response.total || response.data.length,
          page: response.page || 1,
          limit: response.limit || response.data.length
        };
      } else if (Array.isArray(response)) {
        return {
          results: response,
          total: response.length,
          page: 1,
          limit: response.length
        };
      } else if (response && response.results && Array.isArray(response.results)) {
        return response;
      } else {
        console.warn('Unexpected search response structure:', response);
        return {
          results: [],
          total: 0,
          page: 1,
          limit: 0
        };
      }
    } catch (error) {
      console.error('API Error in search:', error);
      // Fallback to getAll if search endpoint doesn't exist
      console.log('Search failed, falling back to getAll...');
      const fallbackResults = await this.getAll();
      return {
        results: fallbackResults,
        total: fallbackResults.length,
        page: 1,
        limit: fallbackResults.length
      };
    }
  },

  // Get student results statistics
  getStats: async () => {
    try {
      console.log('API: Fetching student results statistics');
      
      const response = await apiRequest('/api/trainer/student-results/stats', {
        method: 'GET'
      });
      
      console.log('API Response for getStats:', response);
      
      // Handle different response structures
      if (response && response.data) {
        return response.data;
      } else if (response && response.stats) {
        return response.stats;
      } else {
        return response;
      }
    } catch (error) {
      console.error('API Error in getStats:', error);
      // Return default stats if endpoint doesn't exist
      console.log('Stats endpoint failed, calculating from all results...');
      
      try {
        const allResults = await this.getAll();
        return this.calculateStats(allResults);
      } catch (fallbackError) {
        console.error('Fallback stats calculation failed:', fallbackError);
        return {
          total: 0,
          passed: 0,
          failed: 0,
          pending: 0,
          in_progress: 0,
          average_percentage: 0,
          total_tests: 0,
          total_students: 0,
          test_types: {
            mock_test: 0,
            mock_interview: 0,
            daily_standup: 0,
            session: 0
          }
        };
      }
    }
  },

  // Calculate statistics from results array (helper method)
  calculateStats: (results) => {
    if (!Array.isArray(results) || results.length === 0) {
      return {
        total: 0,
        passed: 0,
        failed: 0,
        pending: 0,
        in_progress: 0,
        average_percentage: 0,
        total_tests: 0,
        total_students: 0,
        test_types: {
          mock_test: 0,
          mock_interview: 0,
          daily_standup: 0,
          session: 0
        }
      };
    }

    const stats = {
      total: results.length,
      passed: 0,
      failed: 0,
      pending: 0,
      in_progress: 0,
      average_percentage: 0,
      total_tests: 0,
      total_students: 0,
      test_types: {
        mock_test: 0,
        mock_interview: 0,
        daily_standup: 0,
        session: 0
      }
    };

    const uniqueTests = new Set();
    const uniqueStudents = new Set();
    let totalPercentage = 0;
    let validPercentageCount = 0;

    results.forEach(result => {
      // Count status
      const status = result.status?.toLowerCase();
      if (status === 'passed') stats.passed++;
      else if (status === 'failed') stats.failed++;
      else if (status === 'pending') stats.pending++;
      else if (status === 'in_progress') stats.in_progress++;

      // Track unique tests and students
      if (result.test_id || result.test_title) {
        uniqueTests.add(result.test_id || result.test_title);
      }
      if (result.student_id || result.student_email) {
        uniqueStudents.add(result.student_id || result.student_email);
      }

      // Calculate average percentage
      const percentage = result.percentage || 0;
      if (percentage > 0) {
        totalPercentage += percentage;
        validPercentageCount++;
      }

      // Count test types
      const testType = result.test_type?.toLowerCase();
      if (testType && stats.test_types.hasOwnProperty(testType)) {
        stats.test_types[testType]++;
      }
    });

    stats.total_tests = uniqueTests.size;
    stats.total_students = uniqueStudents.size;
    stats.average_percentage = validPercentageCount > 0 ? 
      (totalPercentage / validPercentageCount) : 0;

    return stats;
  },

  // Get detailed result with question answers
  getDetailedResult: async (id) => {
    try {
      if (!id) {
        throw new Error('Student result ID is required');
      }
      
      console.log('API: Fetching detailed student result with ID:', id);
      
      // Try different endpoints for detailed view
      const endpoints = [
        `/api/trainer/student-results/detailed/${id}`,
        `/api/trainer/student-results/list/${id}/details`,
        `/api/trainer/student-results/list/${id}`
      ];
      
      let lastError = null;
      
      for (const endpoint of endpoints) {
        try {
          console.log(`Trying endpoint: ${endpoint}`);
          const response = await apiRequest(endpoint, {
            method: 'GET'
          });
          
          console.log(`API Response for endpoint ${endpoint}:`, response);
          
          // If we get a response with question_answers or detailed data, return it
          if (response && (response.question_answers || response.detailed || 
              (response.data && response.data.question_answers))) {
            return response.data || response;
          } else if (response) {
            // Even if not detailed, return what we got
            return response.data || response;
          }
          
        } catch (endpointError) {
          console.warn(`Endpoint ${endpoint} failed:`, endpointError.message);
          lastError = endpointError;
          continue;
        }
      }
      
      // If all endpoints failed, throw the last error
      throw lastError || new Error('All detailed result endpoints failed');
      
    } catch (error) {
      console.error('API Error in getDetailedResult:', error);
      throw new Error(`Failed to get detailed student result: ${error.message}`);
    }
  }
};

// Legacy wrapper methods to match your current component expectations
const studentResultsService = {
  // Wrapper for getAllStudentResults to match your component
  getAllStudentResults: async () => {
    try {
      const results = await studentResultsAPI.getAll();
      return {
        success: true,
        data: results,
        message: 'Student results fetched successfully'
      };
    } catch (error) {
      return {
        success: false,
        data: [],
        error: error.message
      };
    }
  },

  // Wrapper for updateStudentResult to match your component
  updateStudentResult: async (id, updateData) => {
    try {
      const result = await studentResultsAPI.update(id, updateData);
      return {
        success: true,
        data: result,
        message: 'Student result updated successfully'
      };
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error.message
      };
    }
  },

  // Wrapper for getById to match your component
  getStudentResultById: async (id) => {
    try {
      const result = await studentResultsAPI.getById(id);
      return {
        success: true,
        data: result,
        message: 'Student result fetched successfully'
      };
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error.message
      };
    }
  },

  // Additional wrapper methods
  searchStudentResults: async (searchParams) => {
    try {
      const result = await studentResultsAPI.search(searchParams);
      return {
        success: true,
        data: result.results,
        total: result.total,
        page: result.page,
        limit: result.limit,
        message: 'Search completed successfully'
      };
    } catch (error) {
      return {
        success: false,
        data: [],
        total: 0,
        error: error.message
      };
    }
  },

  getStudentResultsStats: async () => {
    try {
      const stats = await studentResultsAPI.getStats();
      return {
        success: true,
        data: stats,
        message: 'Statistics fetched successfully'
      };
    } catch (error) {
      return {
        success: false,
        data: {},
        error: error.message
      };
    }
  },

  getDetailedStudentResult: async (id) => {
    try {
      const result = await studentResultsAPI.getDetailedResult(id);
      return {
        success: true,
        data: result,
        message: 'Detailed result fetched successfully'
      };
    } catch (error) {
      return {
        success: false,
        data: null,
        error: error.message
      };
    }
  }
};

// Export both the API and the legacy service
// export { studentResultsAPI };
export default studentResultsService;