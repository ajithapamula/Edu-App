// src/services/API/dailystandup.js
import { assessmentApiRequest } from './index2';

const dailyStandupApiService = {
  // Get all standup students - GET /daily_standup/api/standup-students
  getAllStandupStudents: async () => {
    try {
      console.log('API: Fetching all standup students');
      
      const response = await assessmentApiRequest('/daily_standup/api/standup-students', {
        method: 'GET'
      });
      
      console.log('API Response for getAllStandupStudents:', response);
      
      // Handle response based on actual API structure
      if (response && response.students && Array.isArray(response.students)) {
        return response.students;
      } else if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else {
        console.warn('Unexpected response structure for getAllStandupStudents:', response);
        return [];
      }
    } catch (error) {
      console.error('API Error in getAllStandupStudents:', error);
      throw new Error(`Failed to fetch standup students: ${error.message}`);
    }
  },

  // Get standup tests for a specific student - GET /daily_standup/api/standup-students/{student_id}/tests
  getStudentStandupTests: async (studentId) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      console.log('API: Fetching standup tests for student_id:', studentId);
      
      const response = await assessmentApiRequest(`/daily_standup/api/standup-students/${studentId}/tests`, {
        method: 'GET'
      });
      
      console.log('API Response for getStudentStandupTests:', response);
      
      // Handle the exact response structure from your API
      if (response && response.tests && Array.isArray(response.tests)) {
        return response.tests;
      } else if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else {
        console.warn('Unexpected response structure for getStudentStandupTests:', response);
        return [];
      }
    } catch (error) {
      console.error('API Error in getStudentStandupTests:', error);
      throw new Error(`Failed to fetch student standup tests: ${error.message}`);
    }
  },

  // Get standup student by ID - extract from getAllStandupStudents
  getStandupStudentById: async (studentId) => {
    try {
      if (!studentId) {
        throw new Error('Student ID is required');
      }
      
      console.log('API: Fetching standup student details for student_id:', studentId);
      
      const allStudents = await dailyStandupApiService.getAllStandupStudents();
      const student = allStudents.find(s => 
        (s.Student_ID && s.Student_ID.toString() === studentId.toString()) || 
        (s.student_id && s.student_id.toString() === studentId.toString()) ||
        (s.id && s.id.toString() === studentId.toString())
      );
      
      if (!student) {
        throw new Error(`Standup student with ID ${studentId} not found`);
      }
      
      console.log('Found standup student:', student);
      return student;
      
    } catch (error) {
      console.error('API Error in getStandupStudentById:', error);
      throw new Error(`Failed to fetch standup student details: ${error.message}`);
    }
  },

  // Get all daily standups - aggregate ONLY from actual API data
  getAllDailyStandups: async () => {
    try {
      console.log('API: Fetching all daily standups from actual API data only');
      
      // Get all standup students first
      const allStudents = await dailyStandupApiService.getAllStandupStudents();
      
      if (!allStudents || allStudents.length === 0) {
        console.warn('No standup students found');
        return [];
      }
      
      // Get tests for each student
      const studentTestsPromises = allStudents.map(async (student) => {
        const studentId = student.Student_ID || student.student_id || student.id;
        if (!studentId) {
          return { student, tests: [] };
        }
        
        try {
          const tests = await dailyStandupApiService.getStudentStandupTests(studentId);
          return { student, tests: tests || [] };
        } catch (error) {
          console.warn(`Failed to fetch tests for student ${studentId}:`, error.message);
          return { student, tests: [] };
        }
      });
      
      const allStudentData = await Promise.all(studentTestsPromises);
      
      // Only create standups from actual test data - NO MOCK DATA
      const standups = [];
      let standupIdCounter = 1;
      
      // Group tests by session_id to create meaningful standups
      const testsBySession = new Map();
      
      allStudentData.forEach(({ student, tests }) => {
        if (!tests || tests.length === 0) {
          // Skip students without test data - don't create mock standups
          return;
        }
        
        tests.forEach(test => {
          const sessionId = test.session_id;
          if (!sessionId) return; // Skip tests without session_id
          
          const sessionKey = `session_${sessionId}`;
          
          if (!testsBySession.has(sessionKey)) {
            testsBySession.set(sessionKey, {
              id: standupIdCounter++,
              sessionId: sessionId,
              tests: [],
              participants: []
            });
          }
          
          const sessionData = testsBySession.get(sessionKey);
          sessionData.tests.push(test);
          
          // Add participant data from actual test
          sessionData.participants.push({
            id: test.Student_ID,
            name: test.name,
            avatar: `/avatars/student${test.Student_ID}.jpg`,
            status: 'present', // Since they took the test
            testId: test.test_id,
            sessionId: test.session_id,
            score: test.score,
            // Only include API data, no mock yesterday/today/blockers
            hasTestData: true
          });
        });
      });
      
      // Convert session groups to standup format using ONLY API data
      testsBySession.forEach((sessionData) => {
        const { id, sessionId, tests, participants } = sessionData;
        
        if (tests.length === 0) return; // Skip empty sessions
        
        // Calculate metrics from actual test data
        const totalTests = tests.length;
        const averageScore = tests.reduce((sum, test) => sum + (test.score || 0), 0) / totalTests;
        const maxScore = Math.max(...tests.map(t => t.score || 0));
        const minScore = Math.min(...tests.map(t => t.score || 0));
        
        standups.push({
          id: id,
          sessionId: sessionId,
          course: `Session ${sessionId}`, // Only use session_id from API
          totalParticipants: participants.length,
          presentParticipants: participants.length,
          participants: participants,
          status: 'completed', // Since tests are completed
          
          // Summary based ONLY on actual test data
          summary: {
            totalTests: totalTests,
            averageScore: parseFloat(averageScore.toFixed(1)),
            maxScore: maxScore,
            minScore: minScore,
            attendanceRate: 100, // 100% since all participants have test data
            
            // Generate achievements from actual data only
            keyAchievements: [
              `${totalTests} test(s) completed in Session ${sessionId}`,
              `Average score: ${averageScore.toFixed(1)}/10`,
              `Highest score: ${maxScore}/10`,
              ...(averageScore >= 8 ? [`Excellent session performance (avg ${averageScore.toFixed(1)}/10)`] : []),
              ...(averageScore >= 6 ? [`Good session performance`] : [])
            ],
            
            // No mock blockers - only indicate no blocker data available
            blockersAvailable: false,
            
            // Team morale based on actual scores
            teamMorale: averageScore >= 8 ? 'Excellent' : 
                       averageScore >= 6 ? 'Good' : 
                       averageScore >= 4 ? 'Average' : 'Needs Improvement',
            
            overallProductivity: Math.round(Math.min(averageScore * 10, 100))
          },
          
          // Include raw API data for debugging
          rawApiData: {
            tests: tests,
            sessionId: sessionId
          }
        });
      });
      
      console.log('Created standups from actual API data:', standups);
      return standups.sort((a, b) => b.sessionId - a.sessionId); // Sort by session ID desc
      
    } catch (error) {
      console.error('API Error in getAllDailyStandups:', error);
      throw new Error(`Failed to fetch daily standups: ${error.message}`);
    }
  },

  // Get daily standup by ID - using only actual API data
  getDailyStandupById: async (standupId) => {
    try {
      if (!standupId) {
        throw new Error('Standup ID is required');
      }
      
      console.log('API: Fetching daily standup details for standup_id:', standupId);
      
      // First try to find in aggregated standups
      const allStandups = await dailyStandupApiService.getAllDailyStandups();
      let standup = allStandups.find(s => 
        (s.id && s.id.toString() === standupId.toString()) || 
        (s.sessionId && s.sessionId.toString() === standupId.toString())
      );
      
      if (standup) {
        console.log('Found standup in aggregated data:', standup);
        return standup;
      }
      
      // If not found, try to get student tests directly (treating ID as student ID)
      try {
        console.log('Trying to fetch as student ID:', standupId);
        const studentTests = await dailyStandupApiService.getStudentStandupTests(standupId);
        
        if (studentTests && studentTests.length > 0) {
          // Create standup from actual student test data only
          const standup = await dailyStandupApiService.createStandupFromStudentTests(studentTests, standupId);
          console.log('Created standup from student tests:', standup);
          return standup;
        }
      } catch (studentError) {
        console.warn('Could not fetch as student ID:', studentError.message);
      }
      
      throw new Error(`No data found for ID ${standupId}. This could be a standup ID, session ID, or student ID.`);
      
    } catch (error) {
      console.error('API Error in getDailyStandupById:', error);
      throw new Error(`Failed to fetch daily standup details: ${error.message}`);
    }
  },

  // Create standup from actual student test data only
  createStandupFromStudentTests: async (testsArray, studentId) => {
    if (!Array.isArray(testsArray) || testsArray.length === 0) {
      throw new Error('No test data available for this student');
    }
    
    console.log('Creating standup from actual test data:', testsArray);
    
    // Use actual test data
    const firstTest = testsArray[0];
    const sessionId = firstTest.session_id;
    const studentName = firstTest.name;
    const studentID = firstTest.Student_ID;
    
    // Calculate actual metrics
    const totalTests = testsArray.length;
    const scores = testsArray.map(t => t.score || 0);
    const averageScore = scores.reduce((a, b) => a + b, 0) / totalTests;
    const maxScore = Math.max(...scores);
    const minScore = Math.min(...scores);
    
    return {
      id: parseInt(studentId),
      sessionId: sessionId,
      course: `Session ${sessionId}`,
      totalParticipants: 1,
      presentParticipants: 1,
      participants: [{
        id: studentID,
        name: studentName,
        avatar: `/avatars/student${studentID}.jpg`,
        status: 'present',
        testId: firstTest.test_id,
        sessionId: sessionId,
        score: firstTest.score,
        totalTests: totalTests,
        averageScore: averageScore,
        hasTestData: true
      }],
      status: 'completed',
      summary: {
        totalTests: totalTests,
        averageScore: parseFloat(averageScore.toFixed(1)),
        maxScore: maxScore,
        minScore: minScore,
        attendanceRate: 100,
        keyAchievements: [
          `${totalTests} test(s) completed by ${studentName}`,
          `Session ${sessionId} participation`,
          `Score range: ${minScore}-${maxScore}/10`,
          `Average performance: ${averageScore.toFixed(1)}/10`
        ],
        blockersAvailable: false,
        teamMorale: averageScore >= 8 ? 'Excellent' : 
                   averageScore >= 6 ? 'Good' : 
                   averageScore >= 4 ? 'Average' : 'Needs Improvement',
        overallProductivity: Math.round(Math.min(averageScore * 10, 100))
      },
      rawApiData: {
        tests: testsArray,
        studentId: studentId
      }
    };
  },

  // Get standup statistics - based only on actual API data
  getStandupStats: async () => {
    try {
      console.log('API: Getting standup statistics from actual API data only');
      
      const [allStandups, allStudents] = await Promise.all([
        dailyStandupApiService.getAllDailyStandups(),
        dailyStandupApiService.getAllStandupStudents()
      ]);
      
      return dailyStandupApiService.calculateStandupStats(allStandups, allStudents);
      
    } catch (error) {
      console.error('API Error in getStandupStats:', error);
      return {
        total_standups: 0,
        active_standups: 0,
        completed_standups: 0,
        average_attendance: 0,
        total_students: 0,
        total_tests: 0,
        average_score: 0
      };
    }
  },

  // Calculate stats based only on actual API data
  calculateStandupStats: (standups, students = []) => {
    const totalStudents = students.length;
    
    if (!Array.isArray(standups) || standups.length === 0) {
      return {
        total_standups: 0,
        active_standups: 0,
        completed_standups: 0,
        average_attendance: 0,
        total_students: totalStudents,
        total_tests: 0,
        average_score: 0
      };
    }

    // Calculate from actual test data only
    const totalTests = standups.reduce((sum, standup) => 
      sum + (standup.summary?.totalTests || 0), 0
    );
    
    const allScores = standups.flatMap(standup => 
      standup.participants?.map(p => p.score || 0) || []
    );
    
    const averageScore = allScores.length > 0 
      ? allScores.reduce((a, b) => a + b, 0) / allScores.length 
      : 0;

    return {
      total_standups: standups.length,
      active_standups: 0, // No status field in API
      completed_standups: standups.length, // All are completed since tests are done
      average_attendance: standups.length > 0 ? 100 : 0, // 100% for test participants
      total_students: totalStudents,
      total_tests: totalTests,
      average_score: parseFloat(averageScore.toFixed(1)),
      sessions_covered: [...new Set(standups.map(s => s.sessionId))].length
    };
  },

  // Get standup metrics for dashboard - using only API data
  getStandupMetrics: async (dateRange = 'all') => {
    try {
      console.log('API: Getting standup metrics from actual API data for range:', dateRange);
      
      const [allStandups, allStudents] = await Promise.all([
        dailyStandupApiService.getAllDailyStandups(),
        dailyStandupApiService.getAllStandupStudents()
      ]);
      
      // Since API doesn't provide dates, we can't filter by date range
      // Return all available data
      return dailyStandupApiService.calculateStandupStats(allStandups, allStudents);
      
    } catch (error) {
      console.error('API Error in getStandupMetrics:', error);
      throw new Error(`Failed to fetch standup metrics: ${error.message}`);
    }
  },

  // Transform functions - removed all mock data
  transformToStandupFormat: async (testsData, studentsData = []) => {
    // This method is now handled by getAllDailyStandups
    // Keeping for compatibility but directing to main method
    console.log('transformToStandupFormat called - redirecting to getAllDailyStandups for consistency');
    return [];
  },

  // Legacy compatibility methods
  getById: async (standupId) => {
    return dailyStandupApiService.getDailyStandupById(standupId);
  },

  // Unsupported operations - clearly state API limitations
  updateStandup: async (standupId, standupData) => {
    throw new Error('Update standup functionality not available - API only provides read access to test data');
  },

  createStandup: async (standupData) => {
    throw new Error('Create standup functionality not available - API only provides read access to test data');
  },

  deleteStandup: async (standupId) => {
    throw new Error('Delete standup functionality not available - API only provides read access to test data');
  },

  exportStandupData: async (standupId, format = 'csv') => {
    throw new Error('Export functionality not available - API only provides read access to test data');
  }
};

// Export with multiple names for compatibility
export const dailyStandupAPI = dailyStandupApiService;
export const standupAPI = dailyStandupApiService;
export default dailyStandupApiService;