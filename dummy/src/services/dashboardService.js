import axiosInstance from '../api/axios';

const dashboardService = {
  // TODO: Missing backend endpoint for session status details (like Login Time).
  // Current implementation relies on the AuthContext user object for Username and Role.
  // getSessionDetails: async () => {
  //   const response = await axiosInstance.get('/session-status');
  //   return response.data;
  // },

  // TODO: Missing backend endpoint for login history.
  getLoginHistory: async () => {
    // Placeholder function. Do NOT invent fake APIs.
    // Uncomment and adjust when the endpoint is created.
    /*
    const response = await axiosInstance.get('/logins');
    return response.data;
    */
    return null; 
  },

  // TODO: Missing backend endpoint for access events.
  getAccessHistory: async () => {
    // Placeholder function.
    /*
    const response = await axiosInstance.get('/access-events');
    return response.data;
    */
    return null;
  },

  // TODO: Missing backend endpoint for security alerts (ML generated).
  getSecurityAlerts: async () => {
    // Placeholder function.
    /*
    const response = await axiosInstance.get('/alerts');
    return response.data;
    */
    return null;
  }
};

export default dashboardService;
