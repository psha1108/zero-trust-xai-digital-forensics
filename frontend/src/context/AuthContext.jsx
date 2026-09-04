import React, { createContext, useState, useEffect } from 'react';
import authService from '../services/authService';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const handleSessionExpired = () => setUser(null);
    window.addEventListener('session_expired', handleSessionExpired);

    const checkAuth = async () => {
      try {
        const data = await authService.checkAuth();
        // The backend /api/auth/me endpoint returns the user object directly: { id, username, role }
        if (data && data.id) {
          setUser(data);
        } else {
          setUser(null);
        }
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
    
    return () => {
      window.removeEventListener('session_expired', handleSessionExpired);
    };
  }, []);

  const login = async (username, password) => {
    const data = await authService.login(username, password);
    // Setting user data from login response (assumes backend sends user details)
    setUser(data.user || { username }); 
    return data;
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout failed:', error);
    } finally {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
