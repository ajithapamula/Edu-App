// src/services/API/sessions.js
import { apiRequest } from './index';

export const sessionsAPI = {
  // Get all sessions - GET /api/trainer/session/lists
  getAll: async () => {
    try {
      console.log('API: Fetching all sessions');
      
      const response = await apiRequest('/api/trainer/session/lists', {
        method: 'GET'
      });
      
      console.log('API Response for getAll sessions:', response);
      
      // Handle different response structures
      let sessions = [];
      
      if (response && response.data && Array.isArray(response.data)) {
        sessions = response.data;
      } else if (Array.isArray(response)) {
        sessions = response;
      } else if (response && response.sessions && Array.isArray(response.sessions)) {
        sessions = response.sessions;
      } else {
        console.warn('Unexpected response structure:', response);
        sessions = [];
      }
      
      // Return the sessions as-is since the API structure is different from expected
      // No normalization needed - keep the original field names
      console.log('Sessions data:', sessions);
      return sessions;
      
    } catch (error) {
      console.error('API Error in getAll sessions:', error);
      throw new Error(`Failed to fetch sessions: ${error.message}`);
    }
  },

  // Get specific session - GET /api/trainer/session/list/{id}
  getById: async (sessionId) => {
    try {
      if (!sessionId) {
        throw new Error('Session ID is required');
      }
      
      console.log('API: Fetching session with ID:', sessionId);
      
      const response = await apiRequest(`/api/trainer/session/list/${sessionId}`, {
        method: 'GET'
      });
      
      console.log('API Response for getById session:', response);
      
      // Handle different response structures
      let sessionData = null;
      
      if (response && response.data) {
        sessionData = response.data;
      } else if (response && response.session) {
        sessionData = response.session;
      } else if (Array.isArray(response)) {
        // If API returns array, find the session by ID
        sessionData = response.find(session => 
          session.Session_ID === parseInt(sessionId) || 
          session.id === parseInt(sessionId)
        );
      } else {
        sessionData = response;
      }
      
      console.log('Processed session data:', sessionData);
      return sessionData;
    } catch (error) {
      console.error('API Error in getById session:', error);
      throw new Error(`Failed to fetch session: ${error.message}`);
    }
  },

  // Create new session - POST /api/trainer/session/create
  create: async (sessionData) => {
    try {
      console.log('API: Creating session with data:', sessionData);
      
      // Validate required fields (as per backend requirements)
      if (!sessionData.Batch_ID) {
        throw new Error('Batch ID is required');
      }
      
      if (!sessionData.Student_ID) {
        throw new Error('Student ID is required');
      }
      
      if (!sessionData.Start_DateTime) {
        throw new Error('Start Date Time is required');
      }

      console.log('API: Sending session payload:', sessionData);
      
      const response = await apiRequest('/api/trainer/session/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(sessionData)
      });
      
      console.log('API Response for create session:', response);
      return response;
    } catch (error) {
      console.error('API Error in create session:', error);
      throw new Error(`Failed to create session: ${error.message}`);
    }
  },

  // Update session - PUT /api/trainer/session/update/{id}
  update: async (sessionId, sessionData) => {
    try {
      if (!sessionId) {
        throw new Error('Session ID is required');
      }
      
      console.log('API: Updating session with ID:', sessionId);
      console.log('API: Update data:', sessionData);
      
      // Prepare update payload - only include fields that have values
      const payload = {};
      
      if (sessionData.Batch_ID !== undefined) payload.Batch_ID = sessionData.Batch_ID;
      if (sessionData.Student_ID !== undefined) payload.Student_ID = sessionData.Student_ID;
      if (sessionData.Student_Name !== undefined) payload.Student_Name = sessionData.Student_Name;
      if (sessionData.Session_Link !== undefined) payload.Session_Link = sessionData.Session_Link;
      if (sessionData.Status !== undefined) payload.Status = sessionData.Status;
      if (sessionData.Start_DateTime !== undefined) payload.Start_DateTime = sessionData.Start_DateTime;
      if (sessionData.End_DateTime !== undefined) payload.End_DateTime = sessionData.End_DateTime;
      if (sessionData.Attended !== undefined) payload.Attended = sessionData.Attended;
      if (sessionData.Percentage !== undefined) payload.Percentage = sessionData.Percentage;
      
      console.log('API: Sending update payload:', payload);
      
      const response = await apiRequest(`/api/trainer/session/update/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
      
      console.log('API Response for update session:', response);
      return response;
    } catch (error) {
      console.error('API Error in update session:', error);
      throw new Error(`Failed to update session: ${error.message}`);
    }
  },

  // Delete session - DELETE /api/trainer/session/remove/{id}
  remove: async (sessionId) => {
    try {
      if (!sessionId) {
        throw new Error('Session ID is required');
      }
      
      console.log('API: Deleting session with ID:', sessionId);
      
      const response = await apiRequest(`/api/trainer/session/remove/${sessionId}`, {
        method: 'DELETE'
      });
      
      console.log('API Response for remove session:', response);
      return response;
    } catch (error) {
      console.error('API Error in remove session:', error);
      throw new Error(`Failed to delete session: ${error.message}`);
    }
  },

  // Search sessions with filters
  search: async (searchParams) => {
    try {
      console.log('API: Searching sessions with params:', searchParams);
      
      // Build query string
      const queryParams = new URLSearchParams();
      
      if (searchParams.query) queryParams.append('q', searchParams.query);
      if (searchParams.status && searchParams.status !== 'all') {
        queryParams.append('status', searchParams.status);
      }
      if (searchParams.instructor) queryParams.append('instructor', searchParams.instructor);
      if (searchParams.topic) queryParams.append('topic', searchParams.topic);
      if (searchParams.dateFrom) queryParams.append('dateFrom', searchParams.dateFrom);
      if (searchParams.dateTo) queryParams.append('dateTo', searchParams.dateTo);
      if (searchParams.batchId) queryParams.append('batchId', searchParams.batchId);
      if (searchParams.page) queryParams.append('page', searchParams.page);
      if (searchParams.limit) queryParams.append('limit', searchParams.limit);
      
      const queryString = queryParams.toString();
      const url = `/api/trainer/session/lists${queryString ? `?${queryString}` : ''}`;
      
      const response = await apiRequest(url, {
        method: 'GET'
      });
      
      console.log('API Response for search sessions:', response);
      
      // Handle different response structures
      let sessions = [];
      
      if (response && response.data && Array.isArray(response.data)) {
        sessions = response.data;
      } else if (Array.isArray(response)) {
        sessions = response;
      } else if (response && response.sessions && Array.isArray(response.sessions)) {
        sessions = response.sessions;
      } else {
        console.warn('Unexpected search response structure:', response);
        sessions = [];
      }
      
      return sessions;
    } catch (error) {
      console.error('API Error in search sessions:', error);
      // Fallback to getAll if search endpoint doesn't exist
      console.log('Search failed, falling back to getAll...');
      return await this.getAll();
    }
  },

  // Get session statistics
  getStats: async () => {
    try {
      console.log('API: Fetching session statistics');
      
      const response = await apiRequest('/api/trainer/session/stats', {
        method: 'GET'
      });
      
      console.log('API Response for getStats sessions:', response);
      return response;
    } catch (error) {
      console.error('API Error in getStats sessions:', error);
      // Return default stats if endpoint doesn't exist
      return {
        total: 0,
        completed: 0,
        scheduled: 0,
        cancelled: 0,
        inProgress: 0,
        avgAttendance: 0
      };
    }
  },

  // Get sessions by status
  getByStatus: async (status) => {
    try {
      if (!status) {
        throw new Error('Status is required');
      }
      
      console.log('API: Fetching sessions by status:', status);
      
      const response = await apiRequest(`/api/trainer/session/lists?status=${status}`, {
        method: 'GET'
      });
      
      console.log('API Response for getByStatus sessions:', response);
      
      // Handle different response structures
      let sessions = [];
      
      if (response && response.data && Array.isArray(response.data)) {
        sessions = response.data;
      } else if (Array.isArray(response)) {
        sessions = response;
      } else if (response && response.sessions && Array.isArray(response.sessions)) {
        sessions = response.sessions;
      } else {
        console.warn('Unexpected response structure:', response);
        sessions = [];
      }
      
      return sessions;
    } catch (error) {
      console.error('API Error in getByStatus sessions:', error);
      throw new Error(`Failed to fetch sessions by status: ${error.message}`);
    }
  },

  // Get upcoming sessions
  getUpcoming: async (limit = 10) => {
    try {
      console.log('API: Fetching upcoming sessions with limit:', limit);
      
      const response = await apiRequest(`/api/trainer/session/lists?upcoming=true&limit=${limit}`, {
        method: 'GET'
      });
      
      console.log('API Response for getUpcoming sessions:', response);
      
      // Handle different response structures
      let sessions = [];
      
      if (response && response.data && Array.isArray(response.data)) {
        sessions = response.data;
      } else if (Array.isArray(response)) {
        sessions = response;
      } else if (response && response.sessions && Array.isArray(response.sessions)) {
        sessions = response.sessions;
      } else {
        console.warn('Unexpected response structure:', response);
        sessions = [];
      }
      
      return sessions;
    } catch (error) {
      console.error('API Error in getUpcoming sessions:', error);
      // Fallback to getAll and filter on frontend
      try {
        const allSessions = await this.getAll();
        const now = new Date();
        return allSessions
          .filter(session => {
            // Use the correct field names from your backend
            const sessionDate = new Date(session.Start_DateTime || session.Start_DateTime);
            return sessionDate > now && (session.Status === 'Active' || session.Status === 'Scheduled');
          })
          .sort((a, b) => new Date(a.Start_DateTime) - new Date(b.Start_DateTime))
          .slice(0, limit);
      } catch (fallbackError) {
        console.error('Fallback error in getUpcoming:', fallbackError);
        return [];
      }
    }
  },

  // Update session status
  updateStatus: async (sessionId, status) => {
    try {
      if (!sessionId) {
        throw new Error('Session ID is required');
      }
      
      if (!status) {
        throw new Error('Status is required');
      }
      
      console.log('API: Updating session status:', { sessionId, status });
      
      const response = await apiRequest(`/api/trainer/session/update/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ Status: status }) // Use capital S to match backend
      });
      
      console.log('API Response for updateStatus session:', response);
      return response;
    } catch (error) {
      console.error('API Error in updateStatus session:', error);
      throw new Error(`Failed to update session status: ${error.message}`);
    }
  },

  // Bulk operations
  bulkUpdate: async (sessionIds, updateData) => {
    try {
      if (!sessionIds || !Array.isArray(sessionIds) || sessionIds.length === 0) {
        throw new Error('Session IDs array is required');
      }
      
      console.log('API: Bulk updating sessions:', { sessionIds, updateData });
      
      const response = await apiRequest('/api/trainer/session/bulk-update', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sessionIds,
          updateData
        })
      });
      
      console.log('API Response for bulkUpdate sessions:', response);
      return response;
    } catch (error) {
      console.error('API Error in bulkUpdate sessions:', error);
      // Fallback to individual updates if bulk endpoint doesn't exist
      console.log('Bulk update failed, falling back to individual updates...');
      const results = [];
      for (const sessionId of sessionIds) {
        try {
          const result = await this.update(sessionId, updateData);
          results.push({ sessionId, success: true, data: result });
        } catch (updateError) {
          results.push({ sessionId, success: false, error: updateError.message });
        }
      }
      return { results };
    }
  },

  // Bulk delete
  bulkDelete: async (sessionIds) => {
    try {
      if (!sessionIds || !Array.isArray(sessionIds) || sessionIds.length === 0) {
        throw new Error('Session IDs array is required');
      }
      
      console.log('API: Bulk deleting sessions:', sessionIds);
      
      const response = await apiRequest('/api/trainer/session/bulk-delete', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ sessionIds })
      });
      
      console.log('API Response for bulkDelete sessions:', response);
      return response;
    } catch (error) {
      console.error('API Error in bulkDelete sessions:', error);
      // Fallback to individual deletes if bulk endpoint doesn't exist
      console.log('Bulk delete failed, falling back to individual deletes...');
      const results = [];
      for (const sessionId of sessionIds) {
        try {
          const result = await this.remove(sessionId);
          results.push({ sessionId, success: true, data: result });
        } catch (deleteError) {
          results.push({ sessionId, success: false, error: deleteError.message });
        }
      }
      return { results };
    }
  }
};