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

  // No dedicated backend Security Alerts endpoint exists yet.
  // Keep this empty rather than inventing security data or a fake API.
  getSecurityAlerts: async () => null,
};

export default dashboardService;
