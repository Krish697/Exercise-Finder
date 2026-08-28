import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const uid      = await AsyncStorage.getItem('user_id');
        const username = await AsyncStorage.getItem('username');
        const email    = await AsyncStorage.getItem('email');
        if (uid) setUser({ id: parseInt(uid), username, email });
      } catch {}
      setLoading(false);
    })();
  }, []);

  const login = async (userData) => {
    await AsyncStorage.multiSet([
      ['user_id',  String(userData.user_id)],
      ['username', userData.username],
      ['email',    userData.email],
    ]);
    setUser({ id: userData.user_id, username: userData.username, email: userData.email });
  };

  const logout = async () => {
    await AsyncStorage.multiRemove(['user_id', 'username', 'email']);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
