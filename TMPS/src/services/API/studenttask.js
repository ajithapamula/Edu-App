// src/services/API/studenttask.js
import { apiRequest } from './index';

export const taskSubmissionsAPI = {
  // Add new task submission - using enhanced endpoint with better error handling
  add: async (submissionData) => {
    try {
      // submissionData should be FormData with Student_ID and Task_Submit
      const response = await apiRequest('/api/student/task-submissions/add-enhanced', {
        method: 'POST',
        body: submissionData, // FormData object
        // Don't set Content-Type header for FormData - browser will set it with boundary
      });
      
      console.log('API Response for task submission add:', response);
      return response;
    } catch (error) {
      console.error('API Error in task submission add:', error);
      
      // Fallback to original endpoint if enhanced one fails
      try {
        console.log('Trying fallback to original endpoint...');
        const fallbackResponse = await apiRequest('/api/student/task-submissions/add', {
          method: 'POST',
          body: submissionData,
        });
        console.log('Fallback API Response:', fallbackResponse);
        return fallbackResponse;
      } catch (fallbackError) {
        console.error('Fallback also failed:', fallbackError);
        throw new Error(`Failed to add task submission: ${error.message}`);
      }
    }
  },

  // Get all task submissions - matching Django endpoint
  getAll: async () => {
    try {
      const response = await apiRequest('/api/student/task-submissions/lists', {
        method: 'GET'
      });
      
      console.log('API Response for task submissions getAll:', response);
      
      // Django backend returns array directly
      return Array.isArray(response) ? response : [];
    } catch (error) {
      console.error('API Error in task submissions getAll:', error);
      throw new Error(`Failed to fetch task submissions: ${error.message}`);
    }
  },

  // Get specific task submission by Student_ID (not submission ID)
  getById: async (Student_ID) => {
    try {
      if (!Student_ID) {
        throw new Error('Student ID is required');
      }
      
      const response = await apiRequest(`/api/student/task-submissions/list/${Student_ID}`, {
        method: 'GET'
      });
      
      console.log('API Response for task submission getById:', response);
      return response;
    } catch (error) {
      console.error('API Error in task submission getById:', error);
      throw new Error(`Failed to fetch task submission: ${error.message}`);
    }
  },

  // Update task submission - matching Django backend
  update: async (studentId, submissionData) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      // submissionData should be FormData with Student_ID and optionally Task_Submit
      const response = await apiRequest(`/api/student/task-submissions/update/${studentId}`, {
        method: 'PUT',
        body: submissionData, // FormData object
        // Don't set Content-Type header for FormData
      });
      
      console.log('API Response for task submission update:', response);
      return response;
    } catch (error) {
      console.error('API Error in task submission update:', error);
      throw new Error(`Failed to update task submission: ${error.message}`);
    }
  },

  // Delete task submission by Student_ID
  remove: async (studentId) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      const response = await apiRequest(`/api/student/task-submissions/remove/${studentId}`, {
        method: 'DELETE'
      });
      
      console.log('API Response for task submission delete:', response);
      return response;
    } catch (error) {
      console.error('API Error in task submission delete:', error);
      throw new Error(`Failed to delete task submission: ${error.message}`);
    }
  },

  // Simplified view submission file method
  viewSubmission: async (Student_ID) => {
    try {
      if (!Student_ID) {
        throw new Error('Student ID is required');
      }
      
      console.log(`Making request to: /api/student/task-submissions/view-submission/${Student_ID}`);
      
      const response = await fetch(`/api/student/task-submissions/view-submission/${Student_ID}`, {
        method: 'GET',
        headers: {
          'Accept': '*/*',
        }
      });
      
      console.log('Response status:', response.status);
      console.log('Response headers:', [...response.headers.entries()]);
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        
        // Try to get more detailed error info
        try {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const errorData = await response.json();
            errorMessage = errorData.error || errorMessage;
          } else if (contentType && contentType.includes('text/')) {
            const errorText = await response.text();
            if (errorText.includes('<!DOCTYPE html>')) {
              errorMessage = 'Backend returned HTML page instead of file - check Django URL configuration';
            } else {
              errorMessage = errorText.substring(0, 200); // First 200 chars
            }
          }
        } catch (parseError) {
          console.log('Could not parse error response:', parseError);
        }
        
        throw new Error(errorMessage);
      }
      
      return response;
      
    } catch (error) {
      console.error('❌ Error in viewSubmission:', error);
      throw error;
    }
  },

  // Alternative method to download file directly
  downloadSubmission: async (studentId, filename = null) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      const response = await fetch(`/api/student/task-submissions/view-submission/${studentId}`, {
        method: 'GET',
      });
      
      if (!response.ok) {
        throw new Error(`Download failed: ${response.status} ${response.statusText}`);
      }
      
      // Create blob and trigger download
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `submission_${studentId}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      return { success: true };
      
    } catch (error) {
      console.error('❌ Error in downloadSubmission:', error);
      throw error;
    }
  },

  // Method to check if the file endpoint is working
  testFileEndpoint: async (studentId) => {
    try {
      const response = await fetch(`/api/student/task-submissions/view-submission/${studentId}`, {
        method: 'HEAD', // Only get headers, not content
      });
      
      return {
        status: response.status,
        statusText: response.statusText,
        contentType: response.headers.get('content-type'),
        contentLength: response.headers.get('content-length'),
        headers: [...response.headers.entries()]
      };
    } catch (error) {
      return { error: error.message };
    }
  },

  // Get submission details (JSON data, not file)
  getSubmissionDetails: async (studentId) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      const response = await apiRequest(`/api/student/task-submissions/list/${studentId}`, {
        method: 'GET'
      });
      
      console.log('API Response for submission details:', response);
      return response;
    } catch (error) {
      console.error('API Error in get submission details:', error);
      throw new Error(`Failed to get submission details: ${error.message}`);
    }
  },

  // Debug endpoint to check database contents
  debugStudents: async () => {
    try {
      const response = await apiRequest('/api/debug/students', {
        method: 'GET'
      });
      
      console.log('API Response for debug students:', response);
      return response;
    } catch (error) {
      console.error('API Error in debug students:', error);
      throw new Error(`Failed to get debug information: ${error.message}`);
    }
  }
};

// Helper function to create a student name lookup API call
export const getStudentName = async (studentId) => {
  try {
    if (!studentId) {
      throw new Error('Student ID is required');
    }
    
    const response = await fetch(`/api/get-student-name/${studentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      // Check if it's a JSON response with error details
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Student not found');
      } else {
        throw new Error('Student not found');
      }
    }
    
    const data = await response.json();
    return data.student_name || data.name || '';
    
  } catch (error) {
    console.error('API Error in get student name:', error);
    throw new Error(`Failed to get student name: ${error.message}`);
  }
};

// Enhanced helper function with better error handling
export const getStudentNameEnhanced = async (studentId) => {
  try {
    if (!studentId) {
      return { success: false, error: 'Student ID is required' };
    }
    
    const response = await fetch(`/api/get-student-name/${studentId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      return { 
        success: false, 
        error: 'Student name endpoint not available (returns HTML instead of JSON)' 
      };
    }
    
    const data = await response.json();
    
    if (response.ok) {
      const studentName = data.student_name || data.name || '';
      return { 
        success: true, 
        studentName: studentName,
        data: data 
      };
    } else {
      return { 
        success: false, 
        error: data.error || 'Student not found' 
      };
    }
    
  } catch (error) {
    console.error('API Error in enhanced get student name:', error);
    return { 
      success: false, 
      error: error.message.includes('Unexpected token') 
        ? 'Student name endpoint not available (HTML response)' 
        : error.message 
    };
  }
};

// Function to check if debug endpoint is available
export const checkDebugEndpoint = async () => {
  try {
    const response = await fetch('/api/debug/students', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return { success: true, data };
    } else {
      return { success: false, error: 'Debug endpoint not available' };
    }
  } catch (error) {
    return { 
      success: false, 
      error: error.message.includes('Unexpected token') 
        ? 'Debug endpoint not implemented' 
        : error.message 
    };
  }
};

// Enhanced error handler utility function
export const handleAPIError = (error, context = 'API operation') => {
  console.error(`❌ Error in ${context}:`, error);
  
  // Common error patterns and user-friendly messages
  const errorPatterns = {
    'Failed to fetch': 'Unable to connect to the server. Please check your internet connection and try again.',
    'NetworkError': 'Network connection failed. Please check your internet connection.',
    '404': 'The requested resource was not found. Please contact your administrator.',
    '403': 'You do not have permission to perform this action.',
    '401': 'Your session has expired. Please log in again.',
    '500': 'Internal server error. Please try again later or contact support.',
    'HTML page instead of file': 'Server configuration issue. The API is returning a webpage instead of the expected file.',
    'Unexpected token': 'Server response format error. Please contact your administrator.',
    'Student ID is required': 'Student ID is missing. Please provide a valid Student ID.',
    'cors': 'Cross-origin request blocked. Please contact your administrator.',
  };
  
  // Find matching error pattern
  const errorMessage = error.message || error.toString();
  const matchedPattern = Object.keys(errorPatterns).find(pattern => 
    errorMessage.toLowerCase().includes(pattern.toLowerCase())
  );
  
  if (matchedPattern) {
    return {
      userMessage: errorPatterns[matchedPattern],
      technicalMessage: errorMessage,
      errorCode: matchedPattern
    };
  }
  
  // Generic fallback
  return {
    userMessage: 'An unexpected error occurred. Please try again or contact support if the problem persists.',
    technicalMessage: errorMessage,
    errorCode: 'UNKNOWN_ERROR'
  };
};