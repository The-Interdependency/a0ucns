import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.withCredentials = true;

const AuthContext = createContext(null);

const clearLocalAuth = () => {
  localStorage.removeItem('multi_ai_hub_chat');
  localStorage.removeItem('token'); // legacy cleanup only
  delete axios.defaults.headers.common['Authorization'];
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const checkAuth = React.useCallback(async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const response = await axios.get(`${API}/auth/me`);
      if (response.data) {
        setUser(response.data);
        setIsAuthenticated(true);
      }
    } catch (error) {
      if (error.response?.status === 401) {
        clearLocalAuth();
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
      }
    } finally {
      if (isInitial) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 && isAuthenticated) {
          clearLocalAuth();
          setToken(null);
          setUser(null);
          setIsAuthenticated(false);
        }
        return Promise.reject(error);
      }
    );

    return () => axios.interceptors.response.eject(interceptor);
  }, [isAuthenticated]);

  // Check authentication on mount and window focus
  useEffect(() => {
    checkAuth(true);
    
    // Re-check auth on focus — but silently (no loading flash)
    const handleFocus = () => {
      checkAuth(false);
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [checkAuth]);

  useEffect(() => {
    const tier = user?.subscription_tier || 'free';
    document.body.dataset.tier = tier;
    return () => {
      delete document.body.dataset.tier;
    };
  }, [user]);

  const login = async (username, password) => {
    const response = await axios.post(`${API}/auth/login`, { username, password });
    const { access_token, user: userData } = response.data;
    setToken(access_token);
    setUser(userData);
    setIsAuthenticated(true);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    return userData;
  };

  const register = async (username, password) => {
    const response = await axios.post(`${API}/auth/register`, { username, password });
    const { access_token, user: userData } = response.data;
    setToken(access_token);
    setUser(userData);
    setIsAuthenticated(true);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    return userData;
  };

  const logout = async () => {
    try {
      // Try to logout from backend (for cookie sessions)
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout request failed:', error);
    }
    
    clearLocalAuth();
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, isAuthenticated, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};
