// src/context/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from "react";



const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // Add loading state
  

  // On mount, hydrate user + token from localStorage (if present)
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (storedUser && token) {
      try {
        const userData = JSON.parse(storedUser);
        setUser({ ...userData, token });
      } catch {
        console.warn("Failed to parse stored user, clearing");
        localStorage.removeItem("user");
        localStorage.removeItem("token");
      }
    }
    setLoading(false);
  }, []);

  const login = ({ id, email, username, token }) => {
    // persist both user object *and* token
    localStorage.setItem("user", JSON.stringify({ id, email, username }));
    localStorage.setItem("token", token);
    setUser({ id, email, username, token });
  };

  const logout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("token");
    setUser(null);
  };


  return (
    <AuthContext.Provider value={{ user, login, logout, loading}}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
};
