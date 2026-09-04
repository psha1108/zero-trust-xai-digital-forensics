import axiosInstance from '../api/axios';

const portalService = {
  getCurrentSession: async () => {
    const response = await axiosInstance.get(
      '/dashboard/session-status'
    );

    return response.data;
  },
};

export default portalService;
