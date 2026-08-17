import axios from 'axios';

// The backend is expected to be running on localhost (typically port 5000 for Flask)
// You can adjust the baseURL if your backend uses a different port.
const axiosInstance = axios.create({
  baseURL: 'http://localhost:5000/api',
  withCredentials: true, // This is CRITICAL for Flask-Login session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor to handle common errors (e.g., 401 Unauthorized)
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // If we receive a 401, it means the session has expired or the user is not authenticated
    if (error.response && error.response.status === 401) {
      // We will handle redirecting to login at the app level or context level,
      // but logging it here is helpful.
      console.warn('Session expired or unauthorized. Please log in again.');
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
