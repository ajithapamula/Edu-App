// src/services/API/weeklyInterviews.js
import { assessmentApiRequest } from './index2';

export const weeklyInterviewsAPI = {
  // Get all interview students - FIXED ENDPOINT
  getAll: async () => {
    try {
      console.log('API: Fetching all interview students');
      
      // Use the correct endpoint that actually returns student data
      const response = await assessmentApiRequest('/weekly_interview/api/interview-students', {
        method: 'GET'
      });
      
      console.log('API Response for getAll interview students:', response);
      
      // FIXED: Handle the case where we get health response instead of student data
      if (response && response.status === 'healthy') {
        console.warn('?? Received health response instead of student data, returning empty array');
        return [];
      }
      
      // Handle different response structures for actual student data
      if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else if (response && response.students && Array.isArray(response.students)) {
        return response.students;
      } else if (response && response.results && Array.isArray(response.results)) {
        return response.results;
      } else {
        console.warn('Unexpected response structure for getAll:', response);
        // Return empty array instead of failing
        return [];
      }
    } catch (error) {
      console.error('API Error in getAll interview students:', error);
      // Return empty array instead of throwing error to prevent UI crash
      console.warn('Returning empty array due to API error');
      return [];
    }
  },

  // Add a separate health check method
  checkHealth: async () => {
    try {
      console.log('API: Checking interview system health');
      
      const response = await assessmentApiRequest('/weekly_interview/health', {
        method: 'GET'
      });
      
      console.log('API Health Response:', response);
      return response;
    } catch (error) {
      console.error('API Health Check Error:', error);
      throw new Error(`Health check failed: ${error.message}`);
    }
  },

  // Get interviews for a specific student - GET /weekly_interview/api/interview-students/{student_id}/interviews
  getInterviewsByStudentId: async (studentId) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      console.log('API: Fetching interviews for student_id:', studentId);
      
      const response = await assessmentApiRequest(`/weekly_interview/api/interview-students/${studentId}/interviews`, {
        method: 'GET'
      });
      
      console.log('API Response for student interviews:', response);
      
      // Handle different response structures
      if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else if (response && response.interviews && Array.isArray(response.interviews)) {
        return response.interviews;
      } else if (response && response.results && Array.isArray(response.results)) {
        return response.results;
      } else {
        console.warn('Unexpected response structure for student interviews:', response);
        return [];
      }
    } catch (error) {
      console.error('API Error in getInterviewsByStudentId:', error);
      throw new Error(`Failed to fetch student interviews: ${error.message}`);
    }
  },

  // Get all interviews from all students (aggregated view)
  getAllInterviews: async () => {
    try {
      console.log('API: Fetching all interviews from all students');
      
      // First get all students - use weeklyInterviewsAPI.getAll() instead of this.getAll()
      const students = await weeklyInterviewsAPI.getAll();
      console.log('Found students:', students);
      
      if (!students || students.length === 0) {
        return [];
      }
      
      // Then get interviews for each student
      const allInterviews = [];
      
      for (const student of students) {
        try {
          const studentId = student.Student_ID || student.student_id || student.id;
          if (!studentId) {
            console.warn('Student without valid ID:', student);
            continue;
          }
          
          const interviews = await weeklyInterviewsAPI.getInterviewsByStudentId(studentId);
          
          // Add student info to each interview
          const interviewsWithStudent = interviews.map(interview => ({
            ...interview,
            student_id: studentId,
            student_name: student.name || student.student_name || 'Unknown',
            student_info: student
          }));
          
          allInterviews.push(...interviewsWithStudent);
        } catch (error) {
          console.error(`Error fetching interviews for student ${student.Student_ID}:`, error);
          // Continue with other students even if one fails
        }
      }
      
      console.log('All interviews aggregated:', allInterviews);
      return allInterviews;
      
    } catch (error) {
      console.error('API Error in getAllInterviews:', error);
      throw new Error(`Failed to fetch all interviews: ${error.message}`);
    }
  },

  // Transform API data to match component expectations
  transformInterviewData: (apiData) => {
    if (!apiData) return null;
    
    // Handle both individual interview data and student+interview data
    const interview = apiData.interview || apiData;
    const student = apiData.student_info || apiData;
    
    return {
      // Primary identifiers
      id: interview.interview_id || interview.test_id || interview.id || `${student.student_id || student.Student_ID}_${Date.now()}`,
      testId: interview.test_id || interview.interview_id || 'N/A',
      studentId: student.student_id || student.Student_ID || apiData.student_id,
      studentName: student.name || student.student_name || apiData.student_name || 'Unknown Student',
      
      // Interview details
      sessionId: interview.session_id || interview.session || 1,
      timestamp: interview.timestamp || interview.created_at || interview.date,
      
      // Scores from the API (handle different possible structures)
      scores: interview.scores || interview.assessment || {},
      overallScore: interview.scores?.overall_score || 
                   interview.overall_score || 
                   interview.assessment?.overall || null,
      technicalScore: interview.scores?.technical_score || 
                     interview.technical_score || 
                     interview.assessment?.technical || null,
      communicationScore: interview.scores?.communication_score || 
                         interview.communication_score || 
                         interview.assessment?.communication || null,
      hrScore: interview.scores?.hr_score || 
               interview.hr_score || 
               interview.assessment?.hr || null,
      
      // Status and metadata
      status: interview.status || 'completed',
      duration: interview.duration || null,
      
      // Format timestamp as date for display
      date: interview.timestamp ? 
            new Date(interview.timestamp * 1000).toLocaleDateString() : 
            (interview.created_at ? new Date(interview.created_at).toLocaleDateString() : 'N/A'),
      dateTime: interview.timestamp ? 
                new Date(interview.timestamp * 1000) : 
                (interview.created_at ? new Date(interview.created_at) : null),
      
      // Keep original data for reference
      raw: apiData
    };
  },

  // Get interview statistics (derived from getAllInterviews data)
  getStats: async () => {
    try {
      console.log('API: Getting weekly interview statistics');
      
      const allInterviews = await weeklyInterviewsAPI.getAllInterviews();
      const transformedInterviews = allInterviews.map(weeklyInterviewsAPI.transformInterviewData);
      
      const stats = {
        total: transformedInterviews.length,
        withScores: transformedInterviews.filter(i => 
          i.scores && Object.keys(i.scores).length > 0
        ).length,
        
        // Calculate average scores if available
        averageOverallScore: 0,
        averageTechnicalScore: 0,
        averageCommunicationScore: 0,
        averageHrScore: 0
      };
      
      // Calculate average scores
      const interviewsWithOverallScore = transformedInterviews.filter(i => i.overallScore !== null && !isNaN(i.overallScore));
      const interviewsWithTechnicalScore = transformedInterviews.filter(i => i.technicalScore !== null && !isNaN(i.technicalScore));
      const interviewsWithCommunicationScore = transformedInterviews.filter(i => i.communicationScore !== null && !isNaN(i.communicationScore));
      const interviewsWithHrScore = transformedInterviews.filter(i => i.hrScore !== null && !isNaN(i.hrScore));
      
      if (interviewsWithOverallScore.length > 0) {
        stats.averageOverallScore = (
          interviewsWithOverallScore.reduce((sum, i) => sum + parseFloat(i.overallScore), 0) / 
          interviewsWithOverallScore.length
        ).toFixed(1);
      }
      
      if (interviewsWithTechnicalScore.length > 0) {
        stats.averageTechnicalScore = (
          interviewsWithTechnicalScore.reduce((sum, i) => sum + parseFloat(i.technicalScore), 0) / 
          interviewsWithTechnicalScore.length
        ).toFixed(1);
      }
      
      if (interviewsWithCommunicationScore.length > 0) {
        stats.averageCommunicationScore = (
          interviewsWithCommunicationScore.reduce((sum, i) => sum + parseFloat(i.communicationScore), 0) / 
          interviewsWithCommunicationScore.length
        ).toFixed(1);
      }
      
      if (interviewsWithHrScore.length > 0) {
        stats.averageHrScore = (
          interviewsWithHrScore.reduce((sum, i) => sum + parseFloat(i.hrScore), 0) / 
          interviewsWithHrScore.length
        ).toFixed(1);
      }
      
      return stats;
    } catch (error) {
      console.error('API Error in getStats:', error);
      return {
        total: 0,
        withScores: 0,
        averageOverallScore: 0,
        averageTechnicalScore: 0,
        averageCommunicationScore: 0,
        averageHrScore: 0
      };
    }
  },

  // Search interviews by student name
  search: async (searchTerm = '') => {
    try {
      const allInterviews = await weeklyInterviewsAPI.getAllInterviews();
      const transformedInterviews = allInterviews.map(weeklyInterviewsAPI.transformInterviewData);
      
      if (!searchTerm) {
        return transformedInterviews;
      }
      
      return transformedInterviews.filter(interview => 
        interview.studentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        interview.testId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        interview.studentId.toString().toLowerCase().includes(searchTerm.toLowerCase())
      );
    } catch (error) {
      console.error('API Error in search:', error);
      return [];
    }
  },

  // Get specific interview details by student ID and interview/test ID
  getInterviewDetails: async (studentId, interviewId) => {
    try {
      if (!studentId || !interviewId) {
        throw new Error('Both Student ID and Interview ID are required');
      }
      
      console.log('API: Fetching interview details for student:', studentId, 'interview:', interviewId);
      
      // Get all interviews for the student
      const interviews = await weeklyInterviewsAPI.getInterviewsByStudentId(studentId);
      
      // Find the specific interview
      const interview = interviews.find(i => 
        i.interview_id === interviewId || 
        i.test_id === interviewId || 
        i.id === interviewId
      );
      
      if (!interview) {
        throw new Error('Interview not found');
      }
      
      return weeklyInterviewsAPI.transformInterviewData(interview);
    } catch (error) {
      console.error('API Error in getInterviewDetails:', error);
      throw new Error(`Failed to fetch interview details: ${error.message}`);
    }
  }
};