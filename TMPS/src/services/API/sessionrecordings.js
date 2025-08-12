// src/services/API/sessionRecordings.js
import { apiRequest } from './index';

export const sessionRecordingsAPI = {
  // Add new session recording - POST /api/trainer/video/add
  add: async (recordingData) => {
    try {
      console.log('API: Adding session recording with data:', recordingData);
      
      // Validate required fields based on backend requirements
      if (!recordingData.file) {
        throw new Error('No video file provided for upload');
      }
      
      if (!recordingData.Video_Name) {
        throw new Error('Video name is required');
      }
      
      if (!recordingData.Session_ID) {
        throw new Error('Session ID is required');
      }
      
      if (!recordingData.Batch_ID) {
        throw new Error('Batch ID is required');
      }

      if (!recordingData.Org_ID) {
        throw new Error('Organization ID is required');
      }
      
      // Create FormData for file upload
      const formData = new FormData();
      
      // Add the video file (backend expects 'file' key)
      formData.append('file', recordingData.file, recordingData.file.name);
      
      // Prepare metadata object that matches backend requirements
      const metadata = {
        Video_Name: recordingData.Video_Name,
        Session_ID: recordingData.Session_ID,
        Batch_ID: recordingData.Batch_ID,
        Org_ID: recordingData.Org_ID
      };
      
      // Add metadata as JSON string (backend expects 'metadata' key)
      formData.append('metadata', JSON.stringify(metadata));
      
      // Log FormData contents for debugging
      console.log('FormData contents being sent to backend:');
      for (let [key, value] of formData.entries()) {
        if (value instanceof File) {
          console.log(`${key}:`, `File(${value.name}, ${value.size} bytes, ${value.type})`);
        } else {
          console.log(`${key}:`, value);
        }
      }
      
      return await apiRequest('/api/trainer/video/add', {
        method: 'POST',
        body: formData
        // Note: Don't set Content-Type header for FormData, let browser set it with boundary
      });
    } catch (error) {
      console.error('API Error in add:', error);
      throw new Error(`Failed to add session recording: ${error.message}`);
    }
  },

  // Get all session recordings - GET /api/trainer/video/lists
  getAll: async () => {
    try {
      const response = await apiRequest('/api/trainer/video/lists', {
        method: 'GET'
      });
      
      console.log('API Response for getAll session recordings:', response);
      
      // Handle different response structures
      if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else if (response && response.recordings && Array.isArray(response.recordings)) {
        return response.recordings;
      } else {
        console.warn('Unexpected response structure:', response);
        return [];
      }
    } catch (error) {
      console.error('API Error in getAll:', error);
      throw new Error(`Failed to fetch session recordings: ${error.message}`);
    }
  },

  // Get specific session recording - GET /api/trainer/video/list/{id}
  getById: async (id) => {
    try {
      if (!id) {
        throw new Error('Recording ID is required');
      }
      
      const response = await apiRequest(`/api/trainer/video/list/${id}`, {
        method: 'GET'
      });
      
      console.log('API Response for getById:', response);
      return response;
    } catch (error) {
      console.error('API Error in getById:', error);
      throw new Error(`Failed to fetch session recording: ${error.message}`);
    }
  },

  // Update session recording - PUT /api/trainer/video/update/{id}
  // This matches your backend expectation for FormData with metadata
 
// In sessionRecordingsAPI.js
update: async (id, formData) => {
  try {
    console.log('API: Updating recording with ID:', id);
    console.log('API: Sending FormData to backend');
    
    const url = `http://192.168.48.33:8000/api/trainer/video/update/${id}`;
    
    const response = await fetch(url, {
      method: 'PUT',
      body: formData, // Send FormData directly - don't set Content-Type header
    });
    
    console.log('API: Response status:', response.status);
    
    const responseData = await response.json();
    console.log('API: Response data:', responseData);
    
    if (!response.ok) {
      const errorMessage = responseData.Error || responseData.error || 'Update failed';
      throw new Error(errorMessage);
    }
    
    return responseData;
  } catch (error) {
    console.error('API Error in update:', error);
    throw error;
  }
},
  // Delete session recording - DELETE /api/trainer/video/remove/{id}
  remove: async (id) => {
    try {
      if (!id) {
        throw new Error('Recording ID is required');
      }
      
      console.log('API: Deleting session recording with ID:', id);
      
      return await apiRequest(`/api/trainer/video/remove/${id}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.error('API Error in remove:', error);
      throw new Error(`Failed to delete session recording: ${error.message}`);
    }
  },

  // Get video stream URL - Multiple endpoint attempts for better compatibility
  getStreamUrl: async (id) => {
    try {
      if (!id) {
        throw new Error('Recording ID is required');
      }
      
      console.log('API: Getting stream URL for recording ID:', id);
      
      // Try multiple endpoints to find the working one
      const endpoints = [
        `/api/trainer/video/stream-direct/${id}`,
        `/api/trainer/video/stream/${id}`,
        `/api/trainer/video/url/${id}`,
        `/api/trainer/video/play/${id}`
      ];
      
      let lastError = null;
      
      for (const endpoint of endpoints) {
        try {
          console.log(`Trying endpoint: ${endpoint}`);
          const response = await apiRequest(endpoint, {
            method: 'GET'
          });
          
          console.log(`API Response for endpoint ${endpoint}:`, response);
          
          // Handle different response structures for stream URL
          if (response && response.streamUrl) {
            console.log('Found streamUrl in response:', response.streamUrl);
            return { streamUrl: response.streamUrl };
          } else if (response && response.url) {
            console.log('Found url in response:', response.url);
            return { streamUrl: response.url };
          } else if (response && response.videoUrl) {
            console.log('Found videoUrl in response:', response.videoUrl);
            return { streamUrl: response.videoUrl };
          } else if (response && response.data && response.data.url) {
            console.log('Found url in response.data:', response.data.url);
            return { streamUrl: response.data.url };
          } else if (response && response.data && response.data.streamUrl) {
            console.log('Found streamUrl in response.data:', response.data.streamUrl);
            return { streamUrl: response.data.streamUrl };
          } else if (typeof response === 'string' && response.length > 0) {
            console.log('Response is a string URL:', response);
            return { streamUrl: response };
          }
          
          // If we get here, this endpoint didn't return a usable URL
          console.warn(`Endpoint ${endpoint} returned unexpected structure:`, response);
          
        } catch (endpointError) {
          console.warn(`Endpoint ${endpoint} failed:`, endpointError.message);
          lastError = endpointError;
          continue; // Try next endpoint
        }
      }
      
      // If all endpoints failed, throw the last error
      throw lastError || new Error('All stream URL endpoints failed');
      
    } catch (error) {
      console.error('API Error in getStreamUrl:', error);
      throw new Error(`Failed to get video stream URL: ${error.message}`);
    }
  },

  // Alternative method to construct video URL from video path
  constructVideoUrl: (recording) => {
    try {
      if (!recording || !recording.file_path) {
        throw new Error('Invalid recording or missing file_path');
      }
      
      console.log('Constructing video URL from file_path:', recording.file_path);
      
      // Handle Windows network path format: \\AISERVER\Users\Administrator\Desktop\...
      let cleanPath = recording.file_path;
      
      // Convert Windows path separators to forward slashes
      cleanPath = cleanPath.replace(/\\/g, '/');
      
      // Remove leading slashes if present
      cleanPath = cleanPath.replace(/^\/+/, '');
      
      // Get the base URL for your server
      const baseUrl = process.env.REACT_APP_API_BASE_URL || window.location.origin;
      
      // Extract filename from path
      const pathParts = cleanPath.split('/');
      const fileName = pathParts[pathParts.length - 1];
      
      // Try different URL construction methods
      const possibleUrls = [
        `${baseUrl}/api/trainer/video/stream/${recording.id}`,
        `${baseUrl}/api/trainer/video/file/${recording.id}`,
        `${baseUrl}/videos/${fileName}`,
        `${baseUrl}/uploads/${fileName}`,
        `${baseUrl}/static/videos/${fileName}`
      ];
      
      console.log('Possible video URLs:', possibleUrls);
      
      // Return the first constructed URL (you can modify this logic)
      return possibleUrls[0];
      
    } catch (error) {
      console.error('Error constructing video URL:', error);
      return null;
    }
  },

  // Search session recordings
  search: async (searchParams) => {
    try {
      console.log('API: Searching session recordings with params:', searchParams);
      
      // Build query string
      const queryParams = new URLSearchParams();
      
      if (searchParams.query) queryParams.append('q', searchParams.query);
      if (searchParams.status && searchParams.status !== 'all') {
        queryParams.append('status', searchParams.status);
      }
      if (searchParams.course) queryParams.append('course', searchParams.course);
      if (searchParams.page) queryParams.append('page', searchParams.page);
      if (searchParams.limit) queryParams.append('limit', searchParams.limit);
      
      const queryString = queryParams.toString();
      const url = `/api/trainer/video/lists${queryString ? `?${queryString}` : ''}`;
      
      const response = await apiRequest(url, {
        method: 'GET'
      });
      
      console.log('API Response for search:', response);
      
      // Handle different response structures
      if (response && response.data && Array.isArray(response.data)) {
        return response.data;
      } else if (Array.isArray(response)) {
        return response;
      } else if (response && response.recordings && Array.isArray(response.recordings)) {
        return response.recordings;
      } else {
        console.warn('Unexpected search response structure:', response);
        return [];
      }
    } catch (error) {
      console.error('API Error in search:', error);
      // Fallback to getAll if search endpoint doesn't exist
      console.log('Search failed, falling back to getAll...');
      return await this.getAll();
    }
  },

  // Get recording statistics
  getStats: async () => {
    try {
      const response = await apiRequest('/api/trainer/video/stats', {
        method: 'GET'
      });
      
      console.log('API Response for getStats:', response);
      return response;
    } catch (error) {
      console.error('API Error in getStats:', error);
      // Return default stats if endpoint doesn't exist
      return {
        total: 0,
        active: 0,
        processing: 0,
        error: 0,
        draft: 0
      };
    }
  }
};