import axiosInstance from '../api/axios';

const forensicsService = {
  getEvidence: async () => {
    const response = await axiosInstance.get('/forensics/evidence');
    return response.data;
  },
  
  verifyIntegrity: async () => {
    const response = await axiosInstance.get('/forensics/verify');
    return response.data;
  },
  
  getTimeline: async (sessionId) => {
    const response = await axiosInstance.get(`/forensics/timeline/${sessionId}`);
    return response.data;
  },
  
  getReport: async (sessionId) => {
    const response = await axiosInstance.get(`/forensics/report/${sessionId}`);
    return response.data;
  }
};

export default forensicsService;
