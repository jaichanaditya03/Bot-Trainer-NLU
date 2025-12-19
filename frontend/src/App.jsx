import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { Sidebar } from './components/Sidebar';
import { ProtectedRoute, AdminRoute } from './components/auth/ProtectedRoute';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { DashboardPage } from './pages/DashboardPage';
import { AdminPanelPage } from './pages/AdminPanelPage';
import { useAuthStore } from './store/authStore';

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const checkSession = useAuthStore((state) => state.checkSession);
  const logout = useAuthStore((state) => state.logout);

  // Check session validity on mount and periodically
  useEffect(() => {
    // Initial session check
    if (isAuthenticated) {
      const isValid = checkSession();
      if (!isValid) {
        toast.error('Your session has expired. Please login again.', {
          duration: 5000,
          position: 'top-center',
        });
        window.location.href = '/login';
      }
    }

    // Check session every minute
    const intervalId = setInterval(() => {
      if (isAuthenticated) {
        const isValid = checkSession();
        if (!isValid) {
          toast.error('Your session has expired after 12 hours. Please login again.', {
            duration: 5000,
            position: 'top-center',
          });
          window.location.href = '/login';
        }
      }
    }, 60000); // Check every 1 minute

    return () => clearInterval(intervalId);
  }, [isAuthenticated, checkSession]);

  return (
    <Router>
      <div className="flex min-h-screen">
        {/* Toast Notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#363636',
              color: '#fff',
            },
            success: {
              duration: 3000,
              iconTheme: {
                primary: '#10B981',
                secondary: '#fff',
              },
            },
            error: {
              duration: 4000,
              iconTheme: {
                primary: '#EF4444',
                secondary: '#fff',
              },
            },
          }}
        />

        {/* Sidebar - only show on authenticated pages */}
        {isAuthenticated && <Sidebar />}

        {/* Main Content */}
        <div className="flex-1">
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />

            {/* Protected Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />

            {/* Admin Routes */}
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminPanelPage />
                </AdminRoute>
              }
            />

            {/* Catch all - redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
