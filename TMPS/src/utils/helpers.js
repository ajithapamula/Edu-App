// Helper utility functions
import { GRADE_SCALE, FILE_UPLOAD, VALIDATION } from './constants';

// String Helpers
export const stringHelpers = {
  // Capitalize first letter
  capitalize: (str) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
  },

  // Convert to title case
  toTitleCase: (str) => {
    if (!str) return '';
    return str
      .toLowerCase()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  },

  // Truncate string with ellipsis
  truncate: (str, length = 50, suffix = '...') => {
    if (!str || str.length <= length) return str;
    return str.substring(0, length) + suffix;
  },

  // Generate random string
  generateRandomString: (length = 10) => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  },

  // Convert snake_case to camelCase
  toCamelCase: (str) => {
    if (!str) return '';
    return str.replace(/_([a-z])/g, (match, letter) => letter.toUpperCase());
  },

  // Convert camelCase to snake_case
  toSnakeCase: (str) => {
    if (!str) return '';
    return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
  },

  // Remove HTML tags
  stripHtml: (str) => {
    if (!str) return '';
    return str.replace(/<[^>]*>/g, '');
  },

  // Generate slug from string
  toSlug: (str) => {
    if (!str) return '';
    return str
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/[\s_-]+/g, '-')
      .replace(/^-+|-+$/g, '');
  },
};

// Array Helpers
export const arrayHelpers = {
  // Remove duplicates from array
  unique: (arr) => {
    return [...new Set(arr)];
  },

  // Group array by property
  groupBy: (arr, key) => {
    return arr.reduce((groups, item) => {
      const group = item[key];
      groups[group] = groups[group] || [];
      groups[group].push(item);
      return groups;
    }, {});
  },

  // Sort array by property
  sortBy: (arr, key, direction = 'asc') => {
    return [...arr].sort((a, b) => {
      const aVal = a[key];
      const bVal = b[key];
      
      if (direction === 'desc') {
        return bVal > aVal ? 1 : bVal < aVal ? -1 : 0;
      }
      return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    });
  },

  // Find items by multiple criteria
  findBy: (arr, criteria) => {
    return arr.filter(item => {
      return Object.keys(criteria).every(key => item[key] === criteria[key]);
    });
  },

  // Paginate array
  paginate: (arr, page = 1, pageSize = 10) => {
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return {
      data: arr.slice(startIndex, endIndex),
      currentPage: page,
      totalPages: Math.ceil(arr.length / pageSize),
      totalItems: arr.length,
      hasNextPage: endIndex < arr.length,
      hasPrevPage: page > 1,
    };
  },

  // Chunk array into smaller arrays
  chunk: (arr, size) => {
    const chunks = [];
    for (let i = 0; i < arr.length; i += size) {
      chunks.push(arr.slice(i, i + size));
    }
    return chunks;
  },
};

// Object Helpers
export const objectHelpers = {
  // Deep clone object
  deepClone: (obj) => {
    return JSON.parse(JSON.stringify(obj));
  },

  // Merge objects deeply
  deepMerge: (target, source) => {
    const result = { ...target };
    
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    
    return result;
  },

  // Get nested property safely
  get: (obj, path, defaultValue = undefined) => {
    const keys = path.split('.');
    let result = obj;
    
    for (const key of keys) {
      if (result == null || typeof result !== 'object') {
        return defaultValue;
      }
      result = result[key];
    }
    
    return result !== undefined ? result : defaultValue;
  },

  // Set nested property
  set: (obj, path, value) => {
    const keys = path.split('.');
    const lastKey = keys.pop();
    let current = obj;
    
    for (const key of keys) {
      if (!(key in current) || typeof current[key] !== 'object') {
        current[key] = {};
      }
      current = current[key];
    }
    
    current[lastKey] = value;
    return obj;
  },

  // Pick specific properties
  pick: (obj, keys) => {
    const result = {};
    keys.forEach(key => {
      if (key in obj) {
        result[key] = obj[key];
      }
    });
    return result;
  },

  // Omit specific properties
  omit: (obj, keys) => {
    const result = { ...obj };
    keys.forEach(key => {
      delete result[key];
    });
    return result;
  },

  // Check if object is empty
  isEmpty: (obj) => {
    return Object.keys(obj).length === 0;
  },

  // Flatten nested object
  flatten: (obj, prefix = '') => {
    const result = {};
    
    for (const key in obj) {
      const newKey = prefix ? `${prefix}.${key}` : key;
      
      if (obj[key] && typeof obj[key] === 'object' && !Array.isArray(obj[key])) {
        Object.assign(result, objectHelpers.flatten(obj[key], newKey));
      } else {
        result[newKey] = obj[key];
      }
    }
    
    return result;
  },
};

// Date Helpers
export const dateHelpers = {
  // Format date to string
  format: (date, format = 'MM/dd/yyyy') => {
    if (!date) return '';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return '';
    
    const formatMap = {
      'yyyy': d.getFullYear(),
      'MM': String(d.getMonth() + 1).padStart(2, '0'),
      'dd': String(d.getDate()).padStart(2, '0'),
      'HH': String(d.getHours()).padStart(2, '0'),
      'mm': String(d.getMinutes()).padStart(2, '0'),
      'ss': String(d.getSeconds()).padStart(2, '0'),
    };
    
    return format.replace(/yyyy|MM|dd|HH|mm|ss/g, match => formatMap[match]);
  },

  // Get relative time (e.g., "2 hours ago")
  getRelativeTime: (date) => {
    if (!date) return '';
    
    const now = new Date();
    const then = new Date(date);
    const diffMs = now - then;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
    if (diffDay < 7) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
    
    return dateHelpers.format(date);
  },

  // Check if date is today
  isToday: (date) => {
    const today = new Date();
    const checkDate = new Date(date);
    
    return checkDate.toDateString() === today.toDateString();
  },

  // Check if date is this week
  isThisWeek: (date) => {
    const now = new Date();
    const weekAgo = new Date(now);
    weekAgo.setDate(now.getDate() - 7);
    
    const checkDate = new Date(date);
    return checkDate >= weekAgo && checkDate <= now;
  },

  // Add days to date
  addDays: (date, days) => {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  },

  // Get start of day
  startOfDay: (date) => {
    const result = new Date(date);
    result.setHours(0, 0, 0, 0);
    return result;
  },

  // Get end of day
  endOfDay: (date) => {
    const result = new Date(date);
    result.setHours(23, 59, 59, 999);
    return result;
  },

  // Calculate age
  calculateAge: (birthDate) => {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    return age;
  },
};

// File Helpers
export const fileHelpers = {
  // Format file size
  formatSize: (bytes) => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  // Get file extension
  getExtension: (filename) => {
    if (!filename) return '';
    return filename.split('.').pop().toLowerCase();
  },

  // Check if file type is allowed
  isAllowedType: (file, category) => {
    const allowedTypes = FILE_UPLOAD.ALLOWED_TYPES[category.toUpperCase()];
    return allowedTypes && allowedTypes.includes(file.type);
  },

  // Check if file size is within limit
  isWithinSizeLimit: (file, category) => {
    const maxSize = FILE_UPLOAD.MAX_SIZE[category.toUpperCase()];
    return maxSize && file.size <= maxSize;
  },

  // Validate file
  validateFile: (file, category) => {
    const errors = [];
    
    if (!fileHelpers.isAllowedType(file, category)) {
      errors.push('File type not allowed');
    }
    
    if (!fileHelpers.isWithinSizeLimit(file, category)) {
      errors.push('File size exceeds limit');
    }
    
    return {
      isValid: errors.length === 0,
      errors,
    };
  },

  // Generate file preview URL
  getPreviewUrl: (file) => {
    if (file && file.type.startsWith('image/')) {
      return URL.createObjectURL(file);
    }
    return null;
  },

  // Download file
  downloadFile: (url, filename) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
};

// Validation Helpers
export const validationHelpers = {
  // Validate email
  isValidEmail: (email) => {
    return VALIDATION.EMAIL.PATTERN.test(email);
  },

  // Validate password
  isValidPassword: (password) => {
    const rules = VALIDATION.PASSWORD;
    const errors = [];
    
    if (password.length < rules.MIN_LENGTH) {
      errors.push(`Password must be at least ${rules.MIN_LENGTH} characters`);
    }
    
    if (rules.REQUIRE_UPPERCASE && !/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    
    if (rules.REQUIRE_LOWERCASE && !/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }
    
    if (rules.REQUIRE_NUMBERS && !/\d/.test(password)) {
      errors.push('Password must contain at least one number');
    }
    
    if (rules.REQUIRE_SPECIAL_CHARS && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }
    
    return {
      isValid: errors.length === 0,
      errors,
    };
  },

  // Validate phone number
  isValidPhone: (phone) => {
    return VALIDATION.PHONE.PATTERN.test(phone);
  },

  // Validate required field
  isRequired: (value) => {
    if (typeof value === 'string') {
      return value.trim().length > 0;
    }
    return value !== null && value !== undefined;
  },

  // Validate min length
  hasMinLength: (value, minLength) => {
    return value && value.length >= minLength;
  },

  // Validate max length
  hasMaxLength: (value, maxLength) => {
    return !value || value.length <= maxLength;
  },

  // Validate URL
  isValidUrl: (url) => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  },
};

// Grade Helpers
export const gradeHelpers = {
  // Get letter grade from percentage
  getLetterGrade: (percentage) => {
    const grades = Object.values(GRADE_SCALE);
    const grade = grades.find(g => percentage >= g.min && percentage <= g.max);
    return grade ? grade.label : 'F';
  },

  // Get grade color based on percentage
  getGradeColor: (percentage) => {
    if (percentage >= 90) return 'success';
    if (percentage >= 80) return 'info';
    if (percentage >= 70) return 'warning';
    return 'error';
  },

  // Calculate GPA from grades
  calculateGPA: (grades) => {
    const gradePoints = {
      'A+': 4.0, 'A': 4.0, 'A-': 3.7,
      'B+': 3.3, 'B': 3.0, 'B-': 2.7,
      'C+': 2.3, 'C': 2.0, 'C-': 1.7,
      'D': 1.0, 'F': 0.0,
    };
    
    const validGrades = grades.filter(grade => gradePoints.hasOwnProperty(grade));
    if (validGrades.length === 0) return 0;
    
    const totalPoints = validGrades.reduce((sum, grade) => sum + gradePoints[grade], 0);
    return (totalPoints / validGrades.length).toFixed(2);
  },
};

// UI Helpers
export const uiHelpers = {
  // Generate random color
  getRandomColor: () => {
    const colors = [
      '#f44336', '#e91e63', '#9c27b0', '#673ab7',
      '#3f51b5', '#2196f3', '#03a9f4', '#00bcd4',
      '#009688', '#4caf50', '#8bc34a', '#cddc39',
      '#ffeb3b', '#ffc107', '#ff9800', '#ff5722',
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  },

  // Get initials from name
  getInitials: (name) => {
    if (!name) return '';
    return name
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  },

  // Generate avatar background color from string
  getAvatarColor: (str) => {
    if (!str) return '#757575';
    
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    const colors = [
      '#f44336', '#e91e63', '#9c27b0', '#673ab7',
      '#3f51b5', '#2196f3', '#03a9f4', '#00bcd4',
      '#009688', '#4caf50', '#8bc34a', '#cddc39',
    ];
    
    return colors[Math.abs(hash) % colors.length];
  },

  // Debounce function
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // Throttle function
  throttle: (func, limit) => {
    let inThrottle;
    return function executedFunction(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  // Copy to clipboard
  copyToClipboard: async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    }
  },
};

// Math Helpers
export const mathHelpers = {
  // Calculate percentage
  percentage: (value, total) => {
    if (total === 0) return 0;
    return Math.round((value / total) * 100);
  },

  // Round to decimal places
  round: (number, decimals = 2) => {
    return Math.round(number * Math.pow(10, decimals)) / Math.pow(10, decimals);
  },

  // Generate random number between min and max
  randomBetween: (min, max) => {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  },

  // Calculate average
  average: (numbers) => {
    if (numbers.length === 0) return 0;
    const sum = numbers.reduce((acc, num) => acc + num, 0);
    return sum / numbers.length;
  },

  // Find median
  median: (numbers) => {
    const sorted = [...numbers].sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    
    if (sorted.length % 2 === 0) {
      return (sorted[middle - 1] + sorted[middle]) / 2;
    }
    
    return sorted[middle];
  },

  // Clamp number between min and max
  clamp: (number, min, max) => {
    return Math.min(Math.max(number, min), max);
  },
};

// Local Storage Helpers
export const storageHelpers = {
  // Set item with expiration
  setWithExpiry: (key, value, ttl) => {
    const now = new Date();
    const item = {
      value: value,
      expiry: now.getTime() + ttl,
    };
    localStorage.setItem(key, JSON.stringify(item));
  },

  // Get item with expiration check
  getWithExpiry: (key) => {
    const itemStr = localStorage.getItem(key);
    if (!itemStr) return null;
    
    try {
      const item = JSON.parse(itemStr);
      const now = new Date();
      
      if (now.getTime() > item.expiry) {
        localStorage.removeItem(key);
        return null;
      }
      
      return item.value;
    } catch {
      return null;
    }
  },

  // Safe JSON parse
  safeGetJSON: (key, defaultValue = null) => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch {
      return defaultValue;
    }
  },

  // Safe JSON stringify and set
  safeSetJSON: (key, value) => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  },
};

// Export all helpers
export default {
  string: stringHelpers,
  array: arrayHelpers,
  object: objectHelpers,
  date: dateHelpers,
  file: fileHelpers,
  validation: validationHelpers,
  grade: gradeHelpers,
  ui: uiHelpers,
  math: mathHelpers,
  storage: storageHelpers,
};