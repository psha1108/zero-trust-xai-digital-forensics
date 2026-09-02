import axios from 'axios';

// Flask REST API used by the React frontend.
const axiosInstance = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// OTP is intentionally returned as HTTP 401 by the Zero Trust backend.
// It must not be confused with an expired or unauthenticated session.
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    const response = error.response;
    const payload = response?.data;

    const isOtpChallenge =
      response?.status === 401 &&
      payload?.requires_otp === true &&
      payload?.policy_action === 'OTP';

    if (response?.status === 401 && !isOtpChallenge) {
      console.warn(
        'Session expired, blocked, or unauthorized. Please authenticate again.'
      );
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
