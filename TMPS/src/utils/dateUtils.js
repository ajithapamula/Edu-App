// Date utility functions
import { format, parseISO, differenceInDays, differenceInHours, differenceInMinutes, differenceInSeconds, addDays, addHours, addMinutes, startOfDay, endOfDay, startOfWeek, endOfWeek, startOfMonth, endOfMonth, isToday, isYesterday, isTomorrow, isThisWeek, isThisMonth, isThisYear, isBefore, isAfter, isEqual, isValid } from 'date-fns';

// Get relative time (e.g., "2 hours ago", "in 3 days")
export const getRelativeTime = (date) => {
  if (!date) return '';
  
  const now = new Date();
  const then = new Date(date);
  
  if (!isValid(then)) return 'Invalid date';
  
  const diffMs = now - then;
  const isFuture = diffMs < 0;
  const absDiffMs = Math.abs(diffMs);
  
  const diffSec = Math.floor(absDiffMs / 1000);
  const diffMin = Math.floor(absDiffMs / (1000 * 60));
  const diffHour = Math.floor(absDiffMs / (1000 * 60 * 60));
  const diffDay = Math.floor(absDiffMs / (1000 * 60 * 60 * 24));
  const diffWeek = Math.floor(diffDay / 7);
  const diffMonth = Math.floor(diffDay / 30);
  const diffYear = Math.floor(diffDay / 365);
  
  const prefix = isFuture ? 'in ' : '';
  const suffix = isFuture ? '' : ' ago';
  
  if (diffSec < 60) return isFuture ? 'in a moment' : 'just now';
  if (diffMin < 60) return `${prefix}${diffMin} minute${diffMin > 1 ? 's' : ''}${suffix}`;
  if (diffHour < 24) return `${prefix}${diffHour} hour${diffHour > 1 ? 's' : ''}${suffix}`;
  if (diffDay < 7) return `${prefix}${diffDay} day${diffDay > 1 ? 's' : ''}${suffix}`;
  if (diffWeek < 4) return `${prefix}${diffWeek} week${diffWeek > 1 ? 's' : ''}${suffix}`;
  if (diffMonth < 12) return `${prefix}${diffMonth} month${diffMonth > 1 ? 's' : ''}${suffix}`;
  
  return `${prefix}${diffYear} year${diffYear > 1 ? 's' : ''}${suffix}`;
};

// Get time ago (alias for getRelativeTime for past dates)
export const getTimeAgo = (date) => {
  return getRelativeTime(date);
};

// Add a simple formatDate function that wraps the dateFormatters
export const formatDate = (date, formatType = 'medium') => {
  if (!date) return '';
  
  const formatters = {
    short: (date) => format(new Date(date), 'MM/dd/yyyy'),
    long: (date) => format(new Date(date), 'MMMM dd, yyyy'),
    medium: (date) => format(new Date(date), 'MMM dd, yyyy'),
    time: (date) => format(new Date(date), 'HH:mm'),
    time12: (date) => format(new Date(date), 'h:mm a'),
    dateTime: (date) => format(new Date(date), 'MM/dd/yyyy HH:mm'),
    dateTime12: (date) => format(new Date(date), 'MM/dd/yyyy h:mm a'),
  };
  
  return formatters[formatType] ? formatters[formatType](date) : format(new Date(date), formatType);
};

// Add a simple formatTime function
export const formatTime = (date, format12Hour = true) => {
  if (!date) return '';
  
  if (format12Hour) {
    return format(new Date(date), 'h:mm a');
  } else {
    return format(new Date(date), 'HH:mm');
  }
};

// Add formatDuration function
export const formatDuration = (startDate, endDate) => {
  if (!startDate || !endDate) return '';
  
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  if (!isValid(start) || !isValid(end)) return 'Invalid dates';
  
  const diffMs = Math.abs(end - start);
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffMs / (1000 * 60));
  const diffHour = Math.floor(diffMs / (1000 * 60 * 60));
  
  if (diffHour > 0) {
    const remainingMin = diffMin % 60;
    return `${diffHour}h ${remainingMin}m`;
  } else if (diffMin > 0) {
    const remainingSec = diffSec % 60;
    return `${diffMin}m ${remainingSec}s`;
  } else {
    return `${diffSec}s`;
  }
};

// Date formatting functions
export const dateFormatters = {
  // Standard formats
  short: (date) => format(new Date(date), 'MM/dd/yyyy'),
  long: (date) => format(new Date(date), 'MMMM dd, yyyy'),
  medium: (date) => format(new Date(date), 'MMM dd, yyyy'),
  
  // Time formats
  time: (date) => format(new Date(date), 'HH:mm'),
  time12: (date) => format(new Date(date), 'h:mm a'),
  timeWithSeconds: (date) => format(new Date(date), 'HH:mm:ss'),
  
  // Date with time
  dateTime: (date) => format(new Date(date), 'MM/dd/yyyy HH:mm'),
  dateTime12: (date) => format(new Date(date), 'MM/dd/yyyy h:mm a'),
  longDateTime: (date) => format(new Date(date), 'MMMM dd, yyyy h:mm a'),
  
  // ISO formats
  iso: (date) => new Date(date).toISOString(),
  isoDate: (date) => format(new Date(date), 'yyyy-MM-dd'),
  isoDateTime: (date) => format(new Date(date), "yyyy-MM-dd'T'HH:mm:ss"),
  
  // Relative formats
  relative: (date) => getRelativeTime(date),
  ago: (date) => getTimeAgo(date),
  
  // Custom formats
  custom: (date, formatString) => format(new Date(date), formatString),
};

// Export all utilities including the new formatDate, formatTime, and formatDuration functions
export default {
  formatters: dateFormatters,
  
  // Convenience functions
  format: dateFormatters.custom,
  formatDate,
  formatTime,
  formatDuration,
  relative: getRelativeTime,
  ago: getTimeAgo,
};