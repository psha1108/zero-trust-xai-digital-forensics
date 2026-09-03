import axiosInstance from '../api/axios';

const dashboardService = {
  getActiveSessions: async () => {
    const response = await axiosInstance.get(
      '/dashboard/soc/active-sessions'
    );

    return response.data;
  },

  getLoginHistory: async () => {
    const response = await axiosInstance.get(
      '/dashboard/soc/login-history'
    );

    return response.data;
  },

  getAccessHistory: async () => {
    const response = await axiosInstance.get(
      '/dashboard/soc/access-history'
    );

    return response.data;
  },

  getSecurityState: async () => {
    const response = await axiosInstance.get(
      '/dashboard/soc/security-state'
    );

    return response.data;
  },

  getSecurityAlerts: async () => {
    const response = await axiosInstance.get(
      '/dashboard/soc/security-alerts'
    );

    return response.data;
  },
};

export default dashboardService;