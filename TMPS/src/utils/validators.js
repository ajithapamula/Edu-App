// Validation utility functions
import { VALIDATION, FILE_UPLOAD } from './constants';

// Basic validation functions
export const basicValidators = {
  // Required field validation
  required: (value, message = 'This field is required') => {
    if (value === null || value === undefined) {
      return { isValid: false, error: message };
    }
    
    if (typeof value === 'string' && value.trim().length === 0) {
      return { isValid: false, error: message };
    }
    
    if (Array.isArray(value) && value.length === 0) {
      return { isValid: false, error: message };
    }
    
    return { isValid: true, error: null };
  },

  // Email validation
  email: (email, message = 'Please enter a valid email address') => {
    if (!email) return { isValid: true, error: null }; // Optional field
    
    const emailRegex = VALIDATION.EMAIL.PATTERN;
    const isValid = emailRegex.test(email);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Phone number validation
  phone: (phone, message = 'Please enter a valid phone number') => {
    if (!phone) return { isValid: true, error: null }; // Optional field
    
    const phoneRegex = VALIDATION.PHONE.PATTERN;
    const isValid = phoneRegex.test(phone);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // URL validation
  url: (url, message = 'Please enter a valid URL') => {
    if (!url) return { isValid: true, error: null }; // Optional field
    
    try {
      new URL(url);
      return { isValid: true, error: null };
    } catch {
      return { isValid: false, error: message };
    }
  },

  // Number validation
  number: (value, message = 'Please enter a valid number') => {
    if (!value && value !== 0) return { isValid: true, error: null }; // Optional field
    
    const num = Number(value);
    const isValid = !isNaN(num) && isFinite(num);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Integer validation
  integer: (value, message = 'Please enter a valid integer') => {
    if (!value && value !== 0) return { isValid: true, error: null }; // Optional field
    
    const num = Number(value);
    const isValid = !isNaN(num) && Number.isInteger(num);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Boolean validation
  boolean: (value) => {
    return {
      isValid: typeof value === 'boolean',
      error: typeof value === 'boolean' ? null : 'Must be true or false'
    };
  },
};

// String validation functions
export const stringValidators = {
  // Minimum length
  minLength: (value, minLength, message) => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const actualMessage = message || `Must be at least ${minLength} characters`;
    const isValid = value.length >= minLength;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Maximum length
  maxLength: (value, maxLength, message) => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const actualMessage = message || `Must be no more than ${maxLength} characters`;
    const isValid = value.length <= maxLength;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Exact length
  exactLength: (value, length, message) => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const actualMessage = message || `Must be exactly ${length} characters`;
    const isValid = value.length === length;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Pattern matching
  pattern: (value, pattern, message = 'Invalid format') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;
    const isValid = regex.test(value);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Alphanumeric
  alphanumeric: (value, message = 'Only letters and numbers are allowed') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const isValid = /^[a-zA-Z0-9]+$/.test(value);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Letters only
  lettersOnly: (value, message = 'Only letters are allowed') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const isValid = /^[a-zA-Z\s]+$/.test(value);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Numbers only
  numbersOnly: (value, message = 'Only numbers are allowed') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const isValid = /^[0-9]+$/.test(value);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // No whitespace
  noWhitespace: (value, message = 'Whitespace is not allowed') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const isValid = !/\s/.test(value);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },
};

// Number validation functions
export const numberValidators = {
  // Minimum value
  min: (value, minValue, message) => {
    if (!value && value !== 0) return { isValid: true, error: null }; // Optional field
    
    const num = Number(value);
    if (isNaN(num)) return { isValid: false, error: 'Must be a valid number' };
    
    const actualMessage = message || `Must be at least ${minValue}`;
    const isValid = num >= minValue;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Maximum value
  max: (value, maxValue, message) => {
    if (!value && value !== 0) return { isValid: true, error: null }; // Optional field
    
    const num = Number(value);
    if (isNaN(num)) return { isValid: false, error: 'Must be a valid number' };
    
    const actualMessage = message || `Must be no more than ${maxValue}`;
    const isValid = num <= maxValue;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Range validation
  range: (value, minValue, maxValue, message) => {
    if (!value && value !== 0) return { isValid: true, error: null }; // Optional field
    
    const num = Number(value);
    if (isNaN(num)) return { isValid: false, error: 'Must be a valid number' };
    
    const actualMessage = message || `Must be between ${minValue} and ${maxValue}`;
    const isValid = num >= minValue && num <= maxValue;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Positive number
  positive: (value, message = 'Must be a positive number') => {
    if (!value && value !== 0) return { isValid: true, error: null }; // Optional field
    
    const num = Number(value);
    if (isNaN(num)) return { isValid: false, error: 'Must be a valid number' };
    
    const isValid = num > 0;
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Non-negative number
  nonNegative: (value, message = 'Must be zero or positive') => {
    if (!value && value !== 0) return { isValid: true, error: null }; // Optional field
    
    const num = Number(value);
    if (isNaN(num)) return { isValid: false, error: 'Must be a valid number' };
    
    const isValid = num >= 0;
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Decimal places
  decimalPlaces: (value, maxDecimals, message) => {
    if (!value && value !== 0) return { isValid: true, error: null }; // Optional field
    
    const num = Number(value);
    if (isNaN(num)) return { isValid: false, error: 'Must be a valid number' };
    
    const actualMessage = message || `Must have no more than ${maxDecimals} decimal places`;
    const decimals = (num.toString().split('.')[1] || '').length;
    const isValid = decimals <= maxDecimals;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },
};

// Date validation functions
export const dateValidators = {
  // Valid date
  date: (value, message = 'Please enter a valid date') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const date = new Date(value);
    const isValid = !isNaN(date.getTime());
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Future date
  future: (value, message = 'Date must be in the future') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const date = new Date(value);
    if (isNaN(date.getTime())) return { isValid: false, error: 'Invalid date' };
    
    const isValid = date > new Date();
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Past date
  past: (value, message = 'Date must be in the past') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const date = new Date(value);
    if (isNaN(date.getTime())) return { isValid: false, error: 'Invalid date' };
    
    const isValid = date < new Date();
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Today or future
  todayOrFuture: (value, message = 'Date must be today or in the future') => {
    if (!value) return { isValid: true, error: null }; // Optional field
    
    const date = new Date(value);
    if (isNaN(date.getTime())) return { isValid: false, error: 'Invalid date' };
    
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    date.setHours(0, 0, 0, 0);
    
    const isValid = date >= today;
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Minimum age
  minimumAge: (birthDate, minAge, message) => {
    if (!birthDate) return { isValid: true, error: null }; // Optional field
    
    const birth = new Date(birthDate);
    if (isNaN(birth.getTime())) return { isValid: false, error: 'Invalid birth date' };
    
    const actualMessage = message || `Must be at least ${minAge} years old`;
    const today = new Date();
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    
    const isValid = age >= minAge;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Date range
  dateRange: (startDate, endDate, message = 'End date must be after start date') => {
    if (!startDate || !endDate) return { isValid: true, error: null }; // Optional fields
    
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      return { isValid: false, error: 'Invalid dates' };
    }
    
    const isValid = end >= start;
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },
};

// File validation functions
export const fileValidators = {
  // File type
  fileType: (file, allowedTypes, message) => {
    if (!file) return { isValid: true, error: null }; // Optional field
    
    const actualMessage = message || `File type must be one of: ${allowedTypes.join(', ')}`;
    const isValid = allowedTypes.includes(file.type);
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // File size
  fileSize: (file, maxSize, message) => {
    if (!file) return { isValid: true, error: null }; // Optional field
    
    const actualMessage = message || `File size must be less than ${formatFileSize(maxSize)}`;
    const isValid = file.size <= maxSize;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Image file
  image: (file, message = 'Please select a valid image file') => {
    if (!file) return { isValid: true, error: null }; // Optional field
    
    const imageTypes = FILE_UPLOAD.ALLOWED_TYPES.IMAGE;
    return fileValidators.fileType(file, imageTypes, message);
  },

  // Document file
  document: (file, message = 'Please select a valid document file') => {
    if (!file) return { isValid: true, error: null }; // Optional field
    
    const documentTypes = FILE_UPLOAD.ALLOWED_TYPES.DOCUMENT;
    return fileValidators.fileType(file, documentTypes, message);
  },

  // Video file
  video: (file, message = 'Please select a valid video file') => {
    if (!file) return { isValid: true, error: null }; // Optional field
    
    const videoTypes = FILE_UPLOAD.ALLOWED_TYPES.VIDEO;
    return fileValidators.fileType(file, videoTypes, message);
  },

  // Audio file
  audio: (file, message = 'Please select a valid audio file') => {
    if (!file) return { isValid: true, error: null }; // Optional field
    
    const audioTypes = FILE_UPLOAD.ALLOWED_TYPES.AUDIO;
    return fileValidators.fileType(file, audioTypes, message);
  },
};

// Password validation functions
export const passwordValidators = {
  // Strong password
  strong: (password) => {
    const errors = [];
    const rules = VALIDATION.PASSWORD;
    
    if (!password) {
      return { isValid: false, error: 'Password is required' };
    }
    
    if (password.length < rules.MIN_LENGTH) {
      errors.push(`At least ${rules.MIN_LENGTH} characters`);
    }
    
    if (rules.REQUIRE_UPPERCASE && !/[A-Z]/.test(password)) {
      errors.push('One uppercase letter');
    }
    
    if (rules.REQUIRE_LOWERCASE && !/[a-z]/.test(password)) {
      errors.push('One lowercase letter');
    }
    
    if (rules.REQUIRE_NUMBERS && !/\d/.test(password)) {
      errors.push('One number');
    }
    
    if (rules.REQUIRE_SPECIAL_CHARS && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      errors.push('One special character');
    }
    
    return {
      isValid: errors.length === 0,
      error: errors.length > 0 ? `Password must contain: ${errors.join(', ')}` : null
    };
  },

  // Password confirmation
  confirmation: (password, confirmPassword, message = 'Passwords do not match') => {
    const isValid = password === confirmPassword;
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Password strength level
  strength: (password) => {
    if (!password) return { level: 0, label: 'No password' };
    
    let score = 0;
    
    // Length
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Character types
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score++;
    
    // Complexity
    if (password.length >= 16) score++;
    if (/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])/.test(password)) score++;
    
    const levels = [
      { min: 0, max: 2, label: 'Very Weak', color: 'error' },
      { min: 3, max: 4, label: 'Weak', color: 'warning' },
      { min: 5, max: 6, label: 'Good', color: 'info' },
      { min: 7, max: 8, label: 'Strong', color: 'success' },
    ];
    
    const level = levels.find(l => score >= l.min && score <= l.max) || levels[0];
    
    return {
      score,
      level: Math.min(score, 4),
      label: level.label,
      color: level.color,
    };
  },
};

// Array validation functions
export const arrayValidators = {
  // Minimum length
  minLength: (array, minLength, message) => {
    if (!array) return { isValid: true, error: null }; // Optional field
    
    const actualMessage = message || `Must have at least ${minLength} items`;
    const isValid = Array.isArray(array) && array.length >= minLength;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Maximum length
  maxLength: (array, maxLength, message) => {
    if (!array) return { isValid: true, error: null }; // Optional field
    
    const actualMessage = message || `Must have no more than ${maxLength} items`;
    const isValid = Array.isArray(array) && array.length <= maxLength;
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Contains value
  contains: (array, value, message) => {
    if (!array) return { isValid: true, error: null }; // Optional field
    
    const actualMessage = message || `Must contain ${value}`;
    const isValid = Array.isArray(array) && array.includes(value);
    
    return {
      isValid,
      error: isValid ? null : actualMessage
    };
  },

  // Unique values
  unique: (array, message = 'All values must be unique') => {
    if (!array) return { isValid: true, error: null }; // Optional field
    
    if (!Array.isArray(array)) {
      return { isValid: false, error: 'Must be an array' };
    }
    
    const uniqueValues = new Set(array);
    const isValid = uniqueValues.size === array.length;
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },
};

// Custom validation functions
export const customValidators = {
  // Credit card number (Luhn algorithm)
  creditCard: (number, message = 'Please enter a valid credit card number') => {
    if (!number) return { isValid: true, error: null }; // Optional field
    
    const cleanNumber = number.toString().replace(/\D/g, '');
    
    if (cleanNumber.length < 13 || cleanNumber.length > 19) {
      return { isValid: false, error: message };
    }
    
    let sum = 0;
    let isEven = false;
    
    for (let i = cleanNumber.length - 1; i >= 0; i--) {
      let digit = parseInt(cleanNumber[i]);
      
      if (isEven) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }
      
      sum += digit;
      isEven = !isEven;
    }
    
    const isValid = sum % 10 === 0;
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Social Security Number
  ssn: (ssn, message = 'Please enter a valid SSN') => {
    if (!ssn) return { isValid: true, error: null }; // Optional field
    
    const ssnRegex = /^\d{3}-?\d{2}-?\d{4}$/;
    const isValid = ssnRegex.test(ssn);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Postal code
  postalCode: (code, country = 'US', message = 'Please enter a valid postal code') => {
    if (!code) return { isValid: true, error: null }; // Optional field
    
    const patterns = {
      US: /^\d{5}(-\d{4})?$/,
      CA: /^[A-Za-z]\d[A-Za-z] ?\d[A-Za-z]\d$/,
      UK: /^[A-Za-z]{1,2}\d[A-Za-z\d]? ?\d[A-Za-z]{2}$/,
      DE: /^\d{5}$/,
      FR: /^\d{5}$/,
    };
    
    const pattern = patterns[country] || patterns.US;
    const isValid = pattern.test(code);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Username
  username: (username, message = 'Username must be 3-20 characters, letters, numbers, and underscores only') => {
    if (!username) return { isValid: false, error: 'Username is required' };
    
    const isValid = /^[a-zA-Z0-9_]{3,20}$/.test(username);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },

  // Slug (URL-friendly string)
  slug: (slug, message = 'Must be lowercase letters, numbers, and hyphens only') => {
    if (!slug) return { isValid: true, error: null }; // Optional field
    
    const isValid = /^[a-z0-9-]+$/.test(slug);
    
    return {
      isValid,
      error: isValid ? null : message
    };
  },
};

// Composite validation function
export const validate = (value, validators) => {
  const errors = [];
  
  for (const validator of validators) {
    const result = validator(value);
    if (!result.isValid) {
      errors.push(result.error);
    }
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    error: errors[0] || null, // Return first error for compatibility
  };
};

// Form validation function
export const validateForm = (data, rules) => {
  const errors = {};
  let isValid = true;
  
  for (const [field, validators] of Object.entries(rules)) {
    const value = data[field];
    const result = validate(value, validators);
    
    if (!result.isValid) {
      errors[field] = result.error;
      isValid = false;
    }
  }
  
  return {
    isValid,
    errors,
  };
};

// Helper function to format file size
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Export all validators
export default {
  basic: basicValidators,
  string: stringValidators,
  number: numberValidators,
  date: dateValidators,
  file: fileValidators,
  password: passwordValidators,
  array: arrayValidators,
  custom: customValidators,
  validate,
  validateForm,
};