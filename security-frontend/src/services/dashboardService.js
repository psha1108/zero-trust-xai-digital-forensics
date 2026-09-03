import axiosInstance from '../api/axios';

const dashboardService = {
  getSessionStatus: async () => {
    const response = await axiosInstance.get('/dashboard/session-status');
    return response.data;
  },

  getLoginHistory: async () => {
    const response = await axiosInstance.get('/dashboard/login-history');
    return response.data;
  },

  getAccessHistory: async () => {
    const response = await axiosInstance.get('/dashboard/access-history');
    return response.data;
  },

  getSecurityState: async () => {
    const response = await axiosInstance.get('/dashboard/security-state');
    return response.data;
  },

  getSecurityAlerts: async () => {
    const response = await axiosInstance.get('/dashboard/security-alerts');
    return response.data;
  },
};

export default dashboardService;
