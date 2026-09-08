import axiosInstance from '../api/axios';

const resourceService = {
  getNormalResource: async () => {
    const response = await axiosInstance.get('/resources/normal');
    return response.data;
  },
  
  getHrResource: async () => {
    const response = await axiosInstance.get('/resources/hr');
    return response.data;
  },
  
  getFinanceResource: async () => {
    const response = await axiosInstance.get('/resources/finance');
    return response.data;
  },
  
  getAdminResource: async () => {
    const response = await axiosInstance.get('/resources/admin');
    return response.data;
  },
  
  getTasks: async () => {
    const response = await axiosInstance.get('/resources/tasks');
    return response.data;
  },
  
  getPolicies: async () => {
    const response = await axiosInstance.get('/resources/policies');
    return response.data;
  },
  
  getAnnouncements: async () => {
    const response = await axiosInstance.get('/resources/announcements');
    return response.data;
  }
};

export default resourceService;
