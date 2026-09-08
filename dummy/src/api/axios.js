import axios from 'axios';

// Flask REST API used by the React frontend.
const axiosInstance = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Handle Zero Trust responses.
axiosInstance.interceptors.response.use(
  (response) => response,

  (error) => {
    const response = error.response;
    const payload = response?.data;

    const isOtpChallenge =
      response?.status === 401 &&
      payload?.requires_otp === true &&
      payload?.policy_action === 'OTP';

    // OTP is a Zero Trust step-up challenge.
    // Keep the original request pending until verification is completed.
    if (isOtpChallenge) {
      const originalRequest = error.config;

      return new Promise((resolve, reject) => {
        window.dispatchEvent(
          new CustomEvent('otp_required', {
            detail: {
              onVerify: async () => {
                try {
                  const retryResponse = await axiosInstance(originalRequest);
                  resolve(retryResponse);
                  return retryResponse;
                } catch (retryError) {
                  reject(retryError);
                  throw retryError;
                }
              },

              onCancel: () => {
                reject(error);
              },
            },
          })
        );
      });
    }

    const isSessionTerminated =
      (response?.status === 401 && payload?.policy_action === 'Block') ||
      (response?.status === 423 && payload?.error === 'OTP challenge locked.');

    if (isSessionTerminated) {
      console.warn('Session terminated. Automatically logging out.');
      window.dispatchEvent(new CustomEvent('session_expired'));
      return Promise.reject(error);
    }

    // Other 401 responses are authentication/session issues.
    if (response?.status === 401) {
      console.warn(
        'Session expired, blocked, or unauthorized. Please authenticate again.'
      );
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;