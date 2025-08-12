import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import LoadingSpinner from '../common/LoadingSpinner';

const PrivateRoute = ({ children, allowedRoles = [] }) => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  console.log('🔍 PrivateRoute - user:', user);
  console.log('🔍 PrivateRoute - loading:', loading);
  console.log('🔍 PrivateRoute - isAuthenticated:', isAuthenticated);
  console.log('🔍 PrivateRoute - allowedRoles:', allowedRoles);
  console.log('🔍 PrivateRoute - current location:', location.pathname);

  if (loading) {
    console.log('🔍 PrivateRoute - showing loading spinner');
    return <LoadingSpinner message="Checking authentication..." />;
  }

  if (!isAuthenticated) {
    console.log('🔍 PrivateRoute - not authenticated, redirecting to login');
    // Redirect to login page with return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user role is allowed for this route
  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    console.log('🔍 PrivateRoute - role not allowed, redirecting to user dashboard');
    // Redirect to appropriate dashboard based on user role with /dashboard
    const dashboardPath = `/${user?.role}/dashboard`;
    return <Navigate to={dashboardPath} replace />;
  }

  console.log('🔍 PrivateRoute - access granted, rendering children');
  return children;
};

export default PrivateRoute;