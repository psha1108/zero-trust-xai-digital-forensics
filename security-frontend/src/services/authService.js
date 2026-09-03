import axiosInstance from '../api/axios';

const authService = {
  login: async (username, password) => {
    const response = await axiosInstance.post('/auth/login', {
      username,
      password,
    });

    return response.data;
  },

  register: async (userData) => {
    const response = await axiosInstance.post(
      '/auth/register',
      userData
    );

    return response.data;
  },

  logout: async () => {
    const response = await axiosInstance.post('/auth/logout');
    return response.data;
  },

  checkAuth: async () => {
    const response = await axiosInstance.get('/auth/me');
    return response.data;
  },

  verifyOtp: async (otpCode) => {
    const response = await axiosInstance.post(
      '/auth/otp/verify',
      {
        otp_code: otpCode,
      }
    );

    return response.data;
  },
};

export default authService;
