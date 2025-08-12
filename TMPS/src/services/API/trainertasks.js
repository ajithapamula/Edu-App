// src/services/API/trainerTasks.js
import { apiRequest } from './index.js';

const BASE_URL = '/api/org/trainer/trainer-task';

export const trainerTasksAPI = {
  // Get all trainer tasks
  getAllTasks: async () => {
    try {
      const response = await apiRequest(`${BASE_URL}/lists`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error('Error fetching trainer tasks:', error);
      throw error;
    }
  },

  // Get single trainer task by ID
  getTaskById: async (id) => {
    try {
      const response = await apiRequest(`${BASE_URL}/list/${id}`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error(`Error fetching trainer task ${id}:`, error);
      throw error;
    }
  },

  // Add new trainer task
  addTask: async (taskData) => {
    try {
      const response = await apiRequest(`${BASE_URL}/add`, {
        method: 'POST',
        body: JSON.stringify(taskData)
      });
      return response;
    } catch (error) {
      console.error('Error adding trainer task:', error);
      throw error;
    }
  },

  // Update trainer task
  updateTask: async (id, taskData) => {
    try {
      const response = await apiRequest(`${BASE_URL}/update/${id}`, {
        method: 'PUT',
        body: JSON.stringify(taskData)
      });
      return response;
    } catch (error) {
      console.error(`Error updating trainer task ${id}:`, error);
      throw error;
    }
  },

  // Delete trainer task
  deleteTask: async (id) => {
    try {
      const response = await apiRequest(`${BASE_URL}/remove/${id}`, {
        method: 'DELETE'
      });
      return response;
    } catch (error) {
      console.error(`Error deleting trainer task ${id}:`, error);
      throw error;
    }
  },

  // Additional utility methods for trainer tasks

  // Get tasks by status
  getTasksByStatus: async (status) => {
    try {
      const response = await apiRequest(`${BASE_URL}/lists?status=${status}`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error(`Error fetching tasks by status ${status}:`, error);
      throw error;
    }
  },

  // Get tasks by course
  getTasksByCourse: async (course) => {
    try {
      const response = await apiRequest(`${BASE_URL}/lists?course=${encodeURIComponent(course)}`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error(`Error fetching tasks by course ${course}:`, error);
      throw error;
    }
  },

  // Search tasks
  searchTasks: async (searchTerm) => {
    try {
      const response = await apiRequest(`${BASE_URL}/lists?search=${encodeURIComponent(searchTerm)}`, {
        method: 'GET'
      });
      return response;
    } catch (error) {
      console.error(`Error searching tasks with term ${searchTerm}:`, error);
      throw error;
    }
  },

  // Update task status only
  updateTaskStatus: async (id, status) => {
    try {
      const response = await apiRequest(`${BASE_URL}/update/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status })
      });
      return response;
    } catch (error) {
      console.error(`Error updating task status for ${id}:`, error);
      throw error;
    }
  },

  // Bulk delete tasks
  bulkDeleteTasks: async (taskIds) => {
    try {
      const deletePromises = taskIds.map(id => 
        apiRequest(`${BASE_URL}/remove/${id}`, {
          method: 'DELETE'
        })
      );
      const responses = await Promise.all(deletePromises);
      return responses;
    } catch (error) {
      console.error('Error bulk deleting tasks:', error);
      throw error;
    }
  }
};

export default trainerTasksAPI;