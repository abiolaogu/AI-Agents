// src/context/AuthContext.tsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import { getCurrentUser, login as apiLogin, logout as apiLogout, register as apiRegister } from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);

  useEffect(() => {
    const user = getCurrentUser();
    if (user) {
      setCurrentUser(user);
    }
  }, []);

  const login = async (username, password) => {
    const user = await apiLogin(username, password);
    setCurrentUser(user);
  };

  const logout = () => {
    apiLogout();
    setCurrentUser(null);
  };

  const register = (username, password) => {
    return apiRegister(username, password);
  };

  return (
    <AuthContext.Provider value={{ currentUser, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
