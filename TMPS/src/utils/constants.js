// Application constants
export const APP_NAME = 'Training Management System';
export const APP_VERSION = '1.0.0';

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:3001/api',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// Authentication
export const AUTH_CONFIG = {
  TOKEN_KEY: 'auth_token',
  REFRESH_TOKEN_KEY: 'refresh_token',
  USER_KEY: 'user_data',
  TOKEN_REFRESH_BUFFER: 5 * 60 * 1000, // 5 minutes before expiry
};

// User Roles
export const USER_ROLES = {
  TRAINER: 'trainer',
  MENTOR: 'mentor',
  STUDENT: 'student',
  ADMIN: 'admin',
};

// User Permissions
export const PERMISSIONS = {
  // Course Documents
  CREATE_DOCUMENTS: 'create_documents',
  VIEW_DOCUMENTS: 'view_documents',
  EDIT_DOCUMENTS: 'edit_documents',
  DELETE_DOCUMENTS: 'delete_documents',

  // Session Recordings
  CREATE_RECORDINGS: 'create_recordings',
  VIEW_RECORDINGS: 'view_recordings',
  EDIT_RECORDINGS: 'edit_recordings',
  DELETE_RECORDINGS: 'delete_recordings',

  // Tasks
  CREATE_TASKS: 'create_tasks',
  VIEW_TASKS: 'view_tasks',
  EDIT_TASKS: 'edit_tasks',
  DELETE_TASKS: 'delete_tasks',
  GRADE_TASKS: 'grade_tasks',

  // Submissions
  CREATE_SUBMISSIONS: 'create_submissions',
  VIEW_SUBMISSIONS: 'view_submissions',
  EDIT_SUBMISSIONS: 'edit_submissions',
  DELETE_SUBMISSIONS: 'delete_submissions',

  // Students
  VIEW_STUDENT_RESULTS: 'view_student_results',
  MANAGE_STUDENTS: 'manage_students',

  // Analytics
  VIEW_ANALYTICS: 'view_analytics',
  VIEW_REPORTS: 'view_reports',
};

// Task Status
export const TASK_STATUS = {
  DRAFT: 'draft',
  ACTIVE: 'active',
  COMPLETED: 'completed',
  OVERDUE: 'overdue',
  CANCELLED: 'cancelled',
};

// Task Priority
export const TASK_PRIORITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent',
};

// Task Types
export const TASK_TYPES = {
  ASSIGNMENT: 'assignment',
  PROJECT: 'project',
  QUIZ: 'quiz',
  WORKSHOP: 'workshop',
  READING: 'reading',
  PRACTICE: 'practice',
  EXAM: 'exam',
};

// Submission Status
export const SUBMISSION_STATUS = {
  PENDING: 'pending',
  SUBMITTED: 'submitted',
  GRADED: 'graded',
  RETURNED: 'returned',
  LATE: 'late',
  REJECTED: 'rejected',
};

// Interview Status
export const INTERVIEW_STATUS = {
  SCHEDULED: 'scheduled',
  IN_PROGRESS: 'in-progress',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
  RESCHEDULED: 'rescheduled',
};

// Recording Status
export const RECORDING_STATUS = {
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  ACTIVE: 'active',
  FAILED: 'failed',
  ARCHIVED: 'archived',
};

// Document Types
export const DOCUMENT_TYPES = {
  PDF: 'pdf',
  DOC: 'doc',
  DOCX: 'docx',
  PPT: 'ppt',
  PPTX: 'pptx',
  XLS: 'xls',
  XLSX: 'xlsx',
  TXT: 'txt',
  MD: 'md',
};

// File Upload
export const FILE_UPLOAD = {
  MAX_SIZE: {
    DOCUMENT: 10 * 1024 * 1024, // 10MB
    VIDEO: 2 * 1024 * 1024 * 1024, // 2GB
    IMAGE: 5 * 1024 * 1024, // 5MB
    AUDIO: 100 * 1024 * 1024, // 100MB
  },
  ALLOWED_TYPES: {
    DOCUMENT: [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
      'text/markdown',
    ],
    VIDEO: [
      'video/mp4',
      'video/webm',
      'video/ogg',
      'video/avi',
      'video/mov',
      'video/wmv',
    ],
    IMAGE: [
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/gif',
      'image/webp',
      'image/svg+xml',
    ],
    AUDIO: [
      'audio/mp3',
      'audio/wav',
      'audio/ogg',
      'audio/aac',
      'audio/m4a',
    ],
  },
};

// Notification Types
export const NOTIFICATION_TYPES = {
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error',
  ASSIGNMENT: 'assignment',
  GRADE: 'grade',
  INTERVIEW: 'interview',
  ANNOUNCEMENT: 'announcement',
};

// Courses
export const COURSES = [
  'Full Stack Development',
  'Frontend Development',
  'Backend Development',
  'Mobile App Development',
  'Data Science',
  'Machine Learning',
  'DevOps',
  'Cloud Computing',
  'Cybersecurity',
  'UI/UX Design',
];

// Programming Languages
export const PROGRAMMING_LANGUAGES = [
  'JavaScript',
  'Python',
  'Java',
  'C#',
  'C++',
  'Go',
  'Rust',
  'PHP',
  'Ruby',
  'Swift',
  'Kotlin',
  'TypeScript',
];

// Technologies
export const TECHNOLOGIES = [
  'React',
  'Vue.js',
  'Angular',
  'Node.js',
  'Express.js',
  'Django',
  'Flask',
  'Spring Boot',
  'Laravel',
  'Ruby on Rails',
  'MongoDB',
  'PostgreSQL',
  'MySQL',
  'Redis',
  'Docker',
  'Kubernetes',
  'AWS',
  'Azure',
  'Google Cloud',
];

// Grade Scales
export const GRADE_SCALE = {
  A_PLUS: { min: 97, max: 100, label: 'A+' },
  A: { min: 93, max: 96, label: 'A' },
  A_MINUS: { min: 90, max: 92, label: 'A-' },
  B_PLUS: { min: 87, max: 89, label: 'B+' },
  B: { min: 83, max: 86, label: 'B' },
  B_MINUS: { min: 80, max: 82, label: 'B-' },
  C_PLUS: { min: 77, max: 79, label: 'C+' },
  C: { min: 73, max: 76, label: 'C' },
  C_MINUS: { min: 70, max: 72, label: 'C-' },
  D: { min: 60, max: 69, label: 'D' },
  F: { min: 0, max: 59, label: 'F' },
};

// Date Formats
export const DATE_FORMATS = {
  SHORT: 'MM/DD/YYYY',
  LONG: 'MMMM DD, YYYY',
  WITH_TIME: 'MM/DD/YYYY HH:mm',
  TIME_ONLY: 'HH:mm',
  ISO: 'YYYY-MM-DDTHH:mm:ss.sssZ',
};

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [5, 10, 25, 50, 100],
  MAX_PAGE_SIZE: 100,
};

// Chart Colors
export const CHART_COLORS = {
  PRIMARY: '#1976d2',
  SECONDARY: '#dc004e',
  SUCCESS: '#2e7d32',
  WARNING: '#ed6c02',
  ERROR: '#d32f2f',
  INFO: '#0288d1',
  PALETTE: [
    '#1976d2',
    '#dc004e',
    '#2e7d32',
    '#ed6c02',
    '#d32f2f',
    '#0288d1',
    '#7b1fa2',
    '#689f38',
    '#f57c00',
    '#5d4037',
  ],
};

// Animation Durations
export const ANIMATION = {
  SHORT: 200,
  MEDIUM: 300,
  LONG: 500,
  EXTRA_LONG: 800,
};

// Breakpoints (Material-UI)
export const BREAKPOINTS = {
  XS: 0,
  SM: 600,
  MD: 900,
  LG: 1200,
  XL: 1536,
};

// Local Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  THEME_MODE: 'theme_mode',
  LANGUAGE: 'language',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  TABLE_PREFERENCES: 'table_preferences',
  NOTIFICATION_PREFERENCES: 'notification_preferences',
};

// Error Messages
export const ERROR_MESSAGES = {
  GENERIC: 'An unexpected error occurred. Please try again.',
  NETWORK: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied. You do not have permission.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION: 'Please check your input and try again.',
  FILE_TOO_LARGE: 'File size exceeds the maximum allowed limit.',
  INVALID_FILE_TYPE: 'Invalid file type. Please select a supported file.',
  SESSION_EXPIRED: 'Your session has expired. Please login again.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  SAVED: 'Changes saved successfully.',
  CREATED: 'Created successfully.',
  UPDATED: 'Updated successfully.',
  DELETED: 'Deleted successfully.',
  UPLOADED: 'File uploaded successfully.',
  SENT: 'Sent successfully.',
  LOGIN: 'Login successful.',
  LOGOUT: 'Logout successful.',
  REGISTER: 'Registration successful.',
  PASSWORD_CHANGED: 'Password changed successfully.',
  EMAIL_SENT: 'Email sent successfully.',
};

// Validation Rules
export const VALIDATION = {
  PASSWORD: {
    MIN_LENGTH: 8,
    REQUIRE_UPPERCASE: true,
    REQUIRE_LOWERCASE: true,
    REQUIRE_NUMBERS: true,
    REQUIRE_SPECIAL_CHARS: true,
  },
  EMAIL: {
    PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  },
  PHONE: {
    PATTERN: /^\+?[\d\s\-\(\)]+$/,
  },
  NAME: {
    MIN_LENGTH: 2,
    MAX_LENGTH: 50,
  },
  TITLE: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 100,
  },
  DESCRIPTION: {
    MAX_LENGTH: 1000,
  },
};

// Theme Colors
export const THEME_COLORS = {
  LIGHT: {
    PRIMARY: '#1976d2',
    SECONDARY: '#dc004e',
    BACKGROUND: '#ffffff',
    SURFACE: '#f5f5f5',
    TEXT_PRIMARY: '#000000',
    TEXT_SECONDARY: '#666666',
  },
  DARK: {
    PRIMARY: '#90caf9',
    SECONDARY: '#f48fb1',
    BACKGROUND: '#121212',
    SURFACE: '#1e1e1e',
    TEXT_PRIMARY: '#ffffff',
    TEXT_SECONDARY: '#aaaaaa',
  },
};

// Default Settings
export const DEFAULT_SETTINGS = {
  THEME_MODE: 'light',
  LANGUAGE: 'en',
  SIDEBAR_COLLAPSED: false,
  NOTIFICATIONS_ENABLED: true,
  EMAIL_NOTIFICATIONS: true,
  PUSH_NOTIFICATIONS: false,
  AUTO_SAVE: true,
  PAGE_SIZE: 10,
};

export default {
  APP_NAME,
  APP_VERSION,
  API_CONFIG,
  AUTH_CONFIG,
  USER_ROLES,
  PERMISSIONS,
  TASK_STATUS,
  TASK_PRIORITY,
  TASK_TYPES,
  SUBMISSION_STATUS,
  INTERVIEW_STATUS,
  RECORDING_STATUS,
  DOCUMENT_TYPES,
  FILE_UPLOAD,
  NOTIFICATION_TYPES,
  COURSES,
  PROGRAMMING_LANGUAGES,
  TECHNOLOGIES,
  GRADE_SCALE,
  DATE_FORMATS,
  PAGINATION,
  CHART_COLORS,
  ANIMATION,
  BREAKPOINTS,
  STORAGE_KEYS,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  VALIDATION,
  THEME_COLORS,
  DEFAULT_SETTINGS,
};