import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { Eye, EyeOff } from 'lucide-react';
import { authService } from '../services/authService';
import { useAuthStore } from '../store/authStore';
import { Loader } from '../components/common/Loader';

export const LoginPage = () => {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Debug: Track any page unload attempts
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      console.log('⚠️ WARNING: Page is about to unload!');
      console.log('⚠️ Current URL:', window.location.href);
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    console.log('🟢 LoginPage mounted, tracking page reloads...');

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      console.log('🔴 LoginPage unmounted');
    };
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = (e) => {
    console.log('🔵 handleSubmit called');
    
    if (e) {
      e.preventDefault();
      e.stopPropagation();
      console.log('🔵 preventDefault and stopPropagation called');
    }

    // Validate fields manually (no browser validation)
    if (!formData.email || !formData.email.trim()) {
      console.log('❌ Email validation failed');
      toast.error('Please enter your email address', {
        duration: 3000,
        position: 'top-center',
      });
      return false;
    }

    if (!formData.password || !formData.password.trim()) {
      console.log('❌ Password validation failed');
      toast.error('Please enter your password', {
        duration: 3000,
        position: 'top-center',
      });
      return false;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      console.log('❌ Email format validation failed');
      toast.error('Please enter a valid email address', {
        duration: 3000,
        position: 'top-center',
      });
      return false;
    }

    console.log('✅ Validation passed, starting login...');
    console.log('📧 Email:', formData.email);
    
    setLoading(true);
    const emailValue = formData.email;

    authService
      .login(formData.email, formData.password)
      .then((response) => {
        console.log('✅ Login successful:', response);
        
        login(response.access_token, {
          email: formData.email,
          username: response.username,
          is_admin: response.is_admin,
        });

        toast.success(response.message || 'Login successful!');
        console.log('🚀 Navigating to dashboard...');
        navigate('/dashboard');
      })
      .catch((error) => {
        console.log('❌ Login error caught:', error);
        console.log('❌ Error response:', error.response);
        console.log('❌ Error status:', error.response?.status);
        console.log('❌ Error detail:', error.response?.data?.detail);
        
        setLoading(false);

        let errorMessage = 'Login failed. Please try again.';

        if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response?.status === 401) {
          errorMessage = 'Incorrect password. Please try again.';
        } else if (error.response?.status === 404) {
          errorMessage = 'User not found. Please register first!';
        }

        console.log('📢 Showing error message:', errorMessage);
        
        toast.error(errorMessage, {
          duration: 5000,
          position: 'top-center',
        });

        console.log('🔄 Preserving email, clearing password...');
        setFormData({
          email: emailValue,
          password: '',
        });
        
        console.log('✅ Error handled, staying on page');
      });
    
    return false;
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="card max-w-md w-full">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold" style={{ color: '#f3f8ff' }}>Welcome Back!</h2>
          <p className="mt-2" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>Sign in to continue to Bot Trainer</p>
        </div>

        {/* Login Container - NO FORM element to prevent any browser form submission */}
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#f3f8ff' }}>
              Email Address
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              className="input-field"
              placeholder="Enter your email"
              autoComplete="email"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: '#f3f8ff' }}>
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                className="input-field pr-10"
                placeholder="Enter your password"
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none"
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Link
              to="/forgot-password"
              className="text-sm hover:underline"
              style={{ color: '#2a9df4' }}
            >
              Forgot password?
            </Link>
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? <Loader size="sm" /> : 'Sign In'}
          </button>
        </div>

        <div className="mt-6 text-center">
          <p style={{ color: 'rgba(243, 248, 255, 0.8)' }}>
            Don't have an account?{' '}
            <Link
              to="/register"
              className="font-medium hover:underline"
              style={{ color: '#2a9df4' }}
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
