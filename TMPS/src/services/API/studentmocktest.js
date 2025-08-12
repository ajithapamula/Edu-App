// src/services/API/studentmocktest.js
import { assessmentApiRequest } from './index2';

export const mockTestAPI = {
  // Start a new mock test - POST /weekend_mocktest/api/test/start
  startTest: async (testConfig = {}) => {
    try {
      console.log('API: Starting mock test with config:', testConfig);
      
      const response = await assessmentApiRequest('/weekend_mocktest/api/test/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testConfig)
      });
      
      console.log('API Response for start test:', response);
      return response;
    } catch (error) {
      console.error('API Error in startTest:', error);
      throw new Error(`Failed to start test: ${error.message}`);
    }
  },

  // Submit a single answer - POST /weekend_mocktest/api/test/submit
  submitAnswer: async (answerData) => {
    try {
      if (!answerData) {
        throw new Error('Answer data is required');
      }
      
      console.log('API: Submitting answer:', answerData);
      
      const response = await assessmentApiRequest('/weekend_mocktest/api/test/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(answerData)
      });
      
      console.log('API Response for submit answer:', response);
      return response;
    } catch (error) {
      console.error('API Error in submitAnswer:', error);
      throw new Error(`Failed to submit answer: ${error.message}`);
    }
  },

  // Get test results - GET /weekend_mocktest/api/test/results/{test_id}
  getTestResults: async (testId) => {
    try {
      if (!testId) {
        throw new Error('Test ID is required');
      }
      
      console.log('API: Getting test results for:', testId);
      
      const response = await assessmentApiRequest(`/weekend_mocktest/api/test/results/${testId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('API Response for test results:', response);
      return response;
    } catch (error) {
      console.error('API Error in getTestResults:', error);
      throw new Error(`Failed to get test results: ${error.message}`);
    }
  },

  // Download PDF results - GET /weekend_mocktest/api/test/pdf/{test_id}
  downloadResultsPDF: async (testId) => {
    try {
      if (!testId) {
        throw new Error('Test ID is required');
      }
      
      console.log('API: Downloading PDF for test:', testId);
      
      // Get base URL from environment or fallback
      const baseUrl = import.meta.env.VITE_ASSESSMENT_API_URL || 'https://192.168.48.201:8070';
      const url = `${baseUrl}/weekend_mocktest/api/test/pdf/${testId}`;
      
      console.log('PDF download URL:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/pdf',
          // Add auth headers if needed
          ...(localStorage.getItem('token') && {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          })
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response.blob();
    } catch (error) {
      console.error('API Error in downloadResultsPDF:', error);
      throw new Error(`Failed to download PDF: ${error.message}`);
    }
  },

  // Helper method to prepare test start request with proper validation
  prepareStartTestRequest: (options = {}) => {
    // Set default user type
    let userType = options.user_type || options.userType || 'dev';
    
    // Normalize user type mapping
    if (userType === 'developer') {
      userType = 'dev';
    } else if (userType === 'non-developer') {
      userType = 'non_dev';
    }
    
    // Validate user type
    if (!['dev', 'non_dev'].includes(userType)) {
      console.warn(`Invalid user_type: ${userType}, defaulting to 'dev'`);
      userType = 'dev';
    }
    
    return {
      user_type: userType,
      // Add any additional config if needed
      timestamp: Date.now()
    };
  },

  // Start test with prepared configuration
  startTestWithConfig: async (options = {}) => {
    try {
      const config = mockTestAPI.prepareStartTestRequest(options);
      console.log('Prepared config for API:', config);
      
      const response = await mockTestAPI.startTest(config);
      
      // Transform response to ensure consistent structure for frontend
      const transformedResponse = {
        testId: response.testId || response.test_id,
        sessionId: response.sessionId || response.session_id,
        userType: response.userType || response.user_type,
        totalQuestions: response.totalQuestions || response.total_questions,
        timeLimit: response.timeLimit || response.time_limit,
        duration: response.duration || (response.timeLimit || response.time_limit) / 60,
        
        // Current question data
        currentQuestion: {
          questionNumber: response.questionNumber || response.question_number,
          questionHtml: response.questionHtml || response.question_html,
          options: response.options,
          timeLimit: response.timeLimit || response.time_limit
        },
        
        // Keep raw response for compatibility
        raw: response.raw || response
      };
      
      console.log('Transformed response:', transformedResponse);
      return transformedResponse;
    } catch (error) {
      console.error('Error starting test with config:', error);
      throw error;
    }
  },

  // Submit answer with proper formatting and error handling
  submitAnswerWithData: async (testId, questionNumber, answer) => {
    try {
      if (!testId || !questionNumber) {
        throw new Error('Test ID and question number are required');
      }
      
      const answerData = {
        test_id: testId,
        question_number: parseInt(questionNumber),
        answer: answer || ''
      };
      
      console.log('Sending answer data:', answerData);
      
      const response = await mockTestAPI.submitAnswer(answerData);
      
      // Transform response for frontend consistency
      if (response.testCompleted || response.test_completed) {
        return {
          testCompleted: true,
          score: response.score,
          totalQuestions: response.totalQuestions || response.total_questions,
          analytics: response.analytics || 'Test completed successfully',
          pdfAvailable: response.pdfAvailable !== false
        };
      } else {
        const nextQuestion = response.nextQuestion || response.next_question;
        return {
          testCompleted: false,
          nextQuestion: {
            questionNumber: nextQuestion.questionNumber || nextQuestion.question_number,
            totalQuestions: nextQuestion.totalQuestions || nextQuestion.total_questions,
            questionHtml: nextQuestion.questionHtml || nextQuestion.question_html,
            options: nextQuestion.options,
            timeLimit: nextQuestion.timeLimit || nextQuestion.time_limit
          }
        };
      }
    } catch (error) {
      console.error('Error submitting answer with data:', error);
      throw error;
    }
  },

  // Validate test configuration before starting
  validateTestConfig: (config) => {
    const errors = [];
    
    const userType = config.user_type || config.userType;
    if (!userType) {
      errors.push('User type is required');
    } else if (!['dev', 'non_dev', 'developer', 'non-developer'].includes(userType)) {
      errors.push('User type must be "dev", "non_dev", "developer", or "non-developer"');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Validate answer submission data
  validateAnswerData: (testId, questionNumber, answer) => {
    const errors = [];
    
    if (!testId || typeof testId !== 'string') {
      errors.push('Valid test ID is required');
    }
    
    if (!questionNumber || questionNumber < 1) {
      errors.push('Valid question number is required');
    }
    
    // Allow empty answers for auto-submit scenarios
    if (answer === undefined || answer === null) {
      errors.push('Answer is required');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await assessmentApiRequest('/weekend_mocktest/api/health', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      return response;
    } catch (error) {
      console.error('API Error in healthCheck:', error);
      throw new Error(`Health check failed: ${error.message}`);
    }
  },

  // Debug method to test API connection
  testAPIConnection: async () => {
    try {
      console.log('Testing API connection...');
      const health = await mockTestAPI.healthCheck();
      console.log('API Health Check Response:', health);
      return { status: 'success', health };
    } catch (error) {
      console.error('API Connection Test Failed:', error);
      return { status: 'failed', error: error.message };
    }
  },

  // Get all tests (for admin/debugging)
  getAllTests: async () => {
    try {
      console.log('API: Getting all tests');
      
      const response = await assessmentApiRequest('/weekend_mocktest/api/tests', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('API Response for all tests:', response);
      return response;
    } catch (error) {
      console.error('API Error in getAllTests:', error);
      throw new Error(`Failed to get all tests: ${error.message}`);
    }
  },

  // Error handling helper
  handleAPIError: (error, context = 'API call') => {
    console.error(`${context} failed:`, error);
    
    if (error.message.includes('Failed to fetch')) {
      return new Error('Network connection failed. Please check your internet connection and try again.');
    } else if (error.message.includes('404')) {
      return new Error('Test not found. Please start a new test.');
    } else if (error.message.includes('500')) {
      return new Error('Server error. Please try again later.');
    } else {
      return error;
    }
  },

  // Utility method to get user-friendly error messages
  getErrorMessage: (error) => {
    if (typeof error === 'string') {
      return error;
    }
    
    if (error?.response?.data?.detail) {
      return error.response.data.detail;
    }
    
    if (error?.message) {
      return error.message;
    }
    
    return 'An unexpected error occurred. Please try again.';
  }
};