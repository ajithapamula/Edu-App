// src/services/API/mocktest.js
// Note: Make sure this import path is correct for your project structure
import { assessmentApiRequest } from './index2';

const apiService = {
  // Get all students - GET /weekend_mocktest/api/students
  getAllStudents: async () => {
    try {
      console.log('API: Fetching all students');
      
      const response = await assessmentApiRequest('/weekend_mocktest/api/students', {
        method: 'GET'
      });
      
      console.log('API Response for getAllStudents:', response);
      
      // Handle the actual API response structure: {count: 5, students: Array(5)}
      if (response && response.students && Array.isArray(response.students)) {
        return response.students;
      } else if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else {
        console.warn('Unexpected response structure for getAllStudents:', response);
        return [];
      }
    } catch (error) {
      console.error('API Error in getAllStudents:', error);
      throw new Error(`Failed to fetch students: ${error.message}`);
    }
  },

  // Get tests for a specific student - GET /weekend_mocktest/api/students/{student_id}/tests
  getStudentTests: async (studentId) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      console.log('API: Fetching tests for student_id:', studentId);
      
      const response = await assessmentApiRequest(`/weekend_mocktest/api/students/${studentId}/tests`, {
        method: 'GET'
      });
      
      console.log('API Response for getStudentTests:', response);
      
      // Handle different response structures
      if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else if (response && response.tests && Array.isArray(response.tests)) {
        return response.tests;
      } else {
        console.warn('Unexpected response structure for getStudentTests:', response);
        return [];
      }
    } catch (error) {
      console.error('API Error in getStudentTests:', error);
      throw new Error(`Failed to fetch student tests: ${error.message}`);
    }
  },

  // Get student by ID - this will extract from getAllStudents since no direct endpoint exists
  getStudentById: async (studentId) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      console.log('API: Fetching student details for student_id:', studentId);
      
      // Since there's no direct endpoint, get all students and find the one we need
      const allStudents = await apiService.getAllStudents();
      const student = allStudents.find(s => 
        (s.Student_ID && s.Student_ID.toString() === studentId.toString()) || 
        (s.student_id && s.student_id.toString() === studentId.toString()) ||
        (s.id && s.id.toString() === studentId.toString())
      );
      
      if (!student) {
        throw new Error(`Student with ID ${studentId} not found`);
      }
      
      console.log('Found student:', student);
      return student;
      
    } catch (error) {
      console.error('API Error in getStudentById:', error);
      throw new Error(`Failed to fetch student details: ${error.message}`);
    }
  },

  // Get all tests - this will aggregate from all students since no direct endpoint exists
  getAllTests: async () => {
    try {
      console.log('API: Fetching all mock tests by aggregating from students');
      
      // Get all students first
      const allStudents = await apiService.getAllStudents();
      
      if (!allStudents || allStudents.length === 0) {
        console.warn('No students found, returning empty tests array');
        return [];
      }
      
      // Get tests for each student and aggregate
      const allTestsPromises = allStudents.map(student => {
        const studentId = student.Student_ID || student.student_id || student.id;
        if (studentId) {
          return apiService.getStudentTests(studentId).catch(error => {
            console.warn(`Failed to fetch tests for student ${studentId}:`, error);
            return [];
          });
        }
        return Promise.resolve([]);
      });
      
      const allTestsArrays = await Promise.all(allTestsPromises);
      
      // Flatten and deduplicate tests
      const allTests = allTestsArrays.flat();
      const uniqueTests = [];
      const testIds = new Set();
      
      allTests.forEach(test => {
        const testId = test.test_id || test.id;
        if (testId && !testIds.has(testId)) {
          testIds.add(testId);
          uniqueTests.push(test);
        }
      });
      
      console.log('API Response for getAllTests (aggregated):', uniqueTests);
      return uniqueTests;
      
    } catch (error) {
      console.error('API Error in getAllTests:', error);
      throw new Error(`Failed to fetch mock tests: ${error.message}`);
    }
  },

  // Get mock test by ID - this will search through student tests
  getTestById: async (testId) => {
    try {
      if (!testId) {
        throw new Error('Test ID is required');
      }
      
      console.log('API: Fetching test details for test_id:', testId);
      
      // Get all tests and find the specific one
      const allTests = await apiService.getAllTests();
      const test = allTests.find(t => 
        (t.test_id && t.test_id.toString() === testId.toString()) || 
        (t.id && t.id.toString() === testId.toString())
      );
      
      if (!test) {
        throw new Error(`Test with ID ${testId} not found`);
      }
      
      console.log('API Response for getTestById:', test);
      return test;
      
    } catch (error) {
      console.error('API Error in getTestById:', error);
      throw new Error(`Failed to fetch test details: ${error.message}`);
    }
  },

  // These methods are not available with current endpoints but kept for compatibility
  updateTest: async (testId, testData) => {
    console.warn('updateTest: No endpoint available for updating tests');
    throw new Error('Update test functionality not available with current API endpoints');
  },

  createTest: async (testData) => {
    console.warn('createTest: No endpoint available for creating tests');
    throw new Error('Create test functionality not available with current API endpoints');
  },

  deleteTest: async (testId) => {
    console.warn('deleteTest: No endpoint available for deleting tests');
    throw new Error('Delete test functionality not available with current API endpoints');
  },

  // Get test statistics - calculate from available data
  getTestStats: async () => {
    try {
      console.log('API: Getting test statistics from available data');
      
      const allTests = await apiService.getAllTests();
      const allStudents = await apiService.getAllStudents();
      
      return apiService.calculateStats(allTests, allStudents);
      
    } catch (error) {
      console.error('API Error in getTestStats:', error);
      // Return default stats on error
      return {
        total_tests: 0,
        active_tests: 0,
        completed_tests: 0,
        draft_tests: 0,
        average_score: 0,
        total_students: 0,
        total_completions: 0
      };
    }
  },

  // Helper function to calculate stats from tests and students arrays
  calculateStats: (tests, students = []) => {
    if (!Array.isArray(tests) || tests.length === 0) {
      return {
        total_tests: 0,
        active_tests: 0,
        completed_tests: 0,
        draft_tests: 0,
        average_score: 0,
        total_students: students ? students.length : 0,
        total_completions: 0
      };
    }

    const stats = {
      total_tests: tests.length,
      active_tests: tests.filter(t => t.status === 'active' || t.status === 'published').length,
      completed_tests: tests.filter(t => t.status === 'completed').length,
      draft_tests: tests.filter(t => t.status === 'draft').length,
      total_students: students ? students.length : 0,
      total_completions: tests.reduce((sum, test) => sum + (test.completed_by || test.completedBy || test.submissions || 0), 0)
    };

    // Calculate average score
    const testsWithScores = tests.filter(t => (t.average_score || t.averageScore || t.score) !== undefined && (t.average_score || t.averageScore || t.score) !== null);
    if (testsWithScores.length > 0) {
      const totalScore = testsWithScores.reduce((sum, test) => {
        return sum + (test.average_score || test.averageScore || test.score || 0);
      }, 0);
      stats.average_score = parseFloat((totalScore / testsWithScores.length).toFixed(1));
    } else {
      stats.average_score = 0;
    }

    return stats;
  },

  // Transform test data to match component expectations
  transformTestData: (apiData) => {
    if (!apiData) return null;
    
    return {
      id: apiData.test_id || apiData.id,
      testId: apiData.test_id || apiData.id, // For ViewMockTest compatibility
      title: apiData.test_title || apiData.title || apiData.name || 'Untitled Test',
      subject: apiData.subject || apiData.course || apiData.category || 'General',
      duration: apiData.duration || apiData.time_limit || apiData.time_allowed || 60,
      totalQuestions: apiData.total_questions || apiData.question_count || apiData.questions_count || 0,
      maxScore: apiData.max_score || apiData.total_marks || apiData.total_points || 100,
      dateCreated: apiData.created_at || apiData.date_created || apiData.created_date || new Date().toISOString(),
      dueDate: apiData.due_date || apiData.end_date || apiData.deadline || new Date().toISOString(),
      status: apiData.status || 'draft',
      difficulty: apiData.difficulty || apiData.level || 'medium',
      totalStudents: apiData.total_students || apiData.enrolled_count || apiData.student_count || 0,
      completedBy: apiData.completed_by || apiData.completed_count || apiData.submissions || 0,
      averageScore: apiData.average_score || apiData.avg_score || apiData.score || 0,
      createdBy: apiData.created_by || apiData.instructor_name || apiData.teacher || 'Unknown',
      
      // Additional fields that might be useful
      description: apiData.description || apiData.details || '',
      instructions: apiData.instructions || apiData.description || '',
      passingScore: apiData.passing_score || apiData.pass_percentage || apiData.pass_marks || 60,
      maxAttempts: apiData.max_attempts || apiData.attempt_limit || apiData.attempts_allowed || 1,
      
      // Timestamps
      createdAt: apiData.created_at || apiData.created_date,
      updatedAt: apiData.updated_at || apiData.modified_date,
      
      // Keep original data for reference
      raw: apiData
    };
  },

  // Transform student data to match component expectations
  transformStudentData: (apiData) => {
    if (!apiData) return null;
    
    return {
      id: apiData.Student_ID || apiData.student_id || apiData.id,
      studentId: apiData.Student_ID || apiData.student_id || apiData.id, // For compatibility
      name: apiData.name || apiData.student_name || apiData.full_name || 'Unknown Student',
      email: apiData.email || apiData.email_address || '',
      phone: apiData.phone || apiData.phone_number || apiData.mobile || '',
      enrollmentDate: apiData.enrollment_date || apiData.created_at || apiData.joined_date || new Date().toISOString(),
      status: apiData.status || apiData.active_status || 'active',
      testsCompleted: apiData.tests_completed || apiData.completed_tests || apiData.total_completed || 0,
      averageScore: apiData.average_score || apiData.avg_score || apiData.overall_score || 0,
      totalTests: apiData.total_tests || apiData.assigned_tests || 0,
      lastTestDate: apiData.last_test_date || apiData.last_activity || null,
      
      // Store the actual student ID from API
      Student_ID: apiData.Student_ID,
      
      // Keep original data for reference
      raw: apiData
    };
  },

  // Methods specifically for ViewMockTest component
  getById: async (testId) => {
    // This is an alias for getTestById for compatibility
    return apiService.getTestById(testId);
  },

  downloadPdf: async (testId, filename) => {
    try {
      console.log('API: PDF download not available with current endpoints');
      
      // Since we don't have a PDF download endpoint, we'll create a placeholder
      alert(`PDF download for ${filename || `test-${testId}.pdf`} is not available with current API endpoints. Please contact your administrator to add PDF download functionality.`);
      
      return false;
      
    } catch (error) {
      console.error('API Error in downloadPdf:', error);
      throw new Error(`Failed to download PDF: ${error.message}`);
    }
  }
};

// Export with both names for compatibility
export const mockTestsAPI = apiService;
export const weekendMockTestAPI = apiService;

// Default export
export default apiService;