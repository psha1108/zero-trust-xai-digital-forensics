import axiosInstance from '../api/axios';

const socService = {
  getActiveSessions: async () => {
    const response = await axiosInstance.get('/dashboard/soc/active-sessions');
    return response.data;
  },

  getSessionsHistory: async () => {
    const response = await axiosInstance.get('/dashboard/soc/sessions-history');
    return response.data;
  },

  getLoginHistory: async () => {
    const response = await axiosInstance.get('/dashboard/soc/login-history');
    return response.data;
  },

  getAccessHistory: async () => {
    const response = await axiosInstance.get('/dashboard/soc/access-history');
    return response.data;
  },

  getSecurityState: async () => {
    const response = await axiosInstance.get('/dashboard/soc/security-state');
    return response.data;
  },

  getSecurityAlerts: async () => {
    const response = await axiosInstance.get('/dashboard/soc/security-alerts');
    return response.data;
  }
};

export default socService;
