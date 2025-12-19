import { Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../../store/authStore';

export const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const checkSession = useAuthStore((state) => state.checkSession);

  useEffect(() => {
    if (isAuthenticated) {
      const isValid = checkSession();
      if (!isValid) {
        toast.error('Your session has expired. Please login again.', {
          duration: 5000,
        });
      }
    }
  }, [isAuthenticated, checkSession]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export const AdminRoute = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore();
  const checkSession = useAuthStore((state) => state.checkSession);

  useEffect(() => {
    if (isAuthenticated) {
      const isValid = checkSession();
      if (!isValid) {
        toast.error('Your session has expired. Please login again.', {
          duration: 5000,
        });
      }
    }
  }, [isAuthenticated, checkSession]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!user?.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};
