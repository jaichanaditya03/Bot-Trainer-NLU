import api from './api';

export const authService = {
  // Register new user
  register: async (username, email, password, isAdmin = false) => {
    const response = await api.post('/register', {
      username,
      email,
      password,
      is_admin: isAdmin,
    });
    return response.data;
  },

  // Login user
  login: async (email, password) => {
    const response = await api.post('/login', {
      email,
      password,
    });
    return response.data;
  },

  // Forgot password
  forgotPassword: async (email) => {
    const response = await api.post('/forgot-password', { email });
    return response.data;
  },

  // Verify OTP
  verifyOTP: async (email, otp) => {
    const response = await api.post('/verify-otp', { email, otp });
    return response.data;
  },

  // Reset password
  resetPassword: async (email, otp, newPassword) => {
    const response = await api.post('/reset-password', {
      email,
      otp,
      new_password: newPassword,
    });
    return response.data;
  },
};
