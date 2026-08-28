import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ── Base URL ──────────────────────────────────────────────────────────────────
// Change this to your computer's local IP when testing on a real device.
// e.g. 'http://192.168.1.100:5000'  ← find your IP with `ipconfig` on Windows
// For Android emulator use: 'http://10.0.2.2:5000'
// For Expo Go on device: use your WiFi IP address
export const BASE_URL = 'http://192.168.1.37:5000'; // Set to computer's local WiFi IP

const api = axios.create({
  baseURL: `${BASE_URL}/api/mobile`,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach user id to every request automatically
api.interceptors.request.use(async (config) => {
  const userId = await AsyncStorage.getItem('user_id');
  if (userId) {
    config.headers['X-User-Id'] = userId;
  }
  return config;
});

// ── Auth ──────────────────────────────────────────────────────────────────────

export const apiLogin = (email, password) =>
  api.post('/auth/login', { email, password });

export const apiRegister = (username, email, password) =>
  api.post('/auth/register', { username, email, password });

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const apiDashboard = () => api.get('/dashboard');

// ── Search ────────────────────────────────────────────────────────────────────

export const apiSearch = (params) => api.get('/search', { params });

export const apiMuscleExercises = (muscle) =>
  api.get('/muscle-exercises', { params: { muscle } });

// ── Timeline ─────────────────────────────────────────────────────────────────

export const apiTimeline   = ()          => api.get('/timeline');
export const apiAddWorkout = (data)      => api.post('/workout', data);
export const apiDeleteWorkout = (id)     => api.delete(`/workout/${id}`);

// ── Progress ──────────────────────────────────────────────────────────────────

export const apiProgress = () => api.get('/progress');

// ── Goals ─────────────────────────────────────────────────────────────────────

export const apiGetGoals    = ()         => api.get('/goals');
export const apiAddGoal     = (data)     => api.post('/goals', data);
export const apiUpdateGoal  = (id, val)  => api.put(`/goals/${id}`, { current_value: val });
export const apiDeleteGoal  = (id)       => api.delete(`/goals/${id}`);

// ── Favourites ────────────────────────────────────────────────────────────────

export const apiGetFavourites    = ()    => api.get('/favourites');
export const apiAddFavourite     = (data)=> api.post('/favourites', data);
export const apiRemoveFavourite  = (id)  => api.delete(`/favourites/${id}`);

// ── Workout Plans ─────────────────────────────────────────────────────────────

export const apiGetPlans       = ()         => api.get('/plans');
export const apiCreatePlan     = (data)     => api.post('/plans', data);
export const apiGetPlan        = (id)       => api.get(`/plans/${id}`);
export const apiSavePlanProgress = (id, ex) => api.post(`/plans/${id}/progress`, { exercises: ex });
export const apiCompletePlan   = (id)       => api.post(`/plans/${id}/complete`);
export const apiDeletePlan     = (id)       => api.delete(`/plans/${id}`);

// ── AI Plan ───────────────────────────────────────────────────────────────────

export const apiAIPlan = (data) => api.post('/ai-plan', data);

// ── Profile ───────────────────────────────────────────────────────────────────

export const apiGetProfile    = ()       => api.get('/profile');
export const apiUpdateProfile = (data)   => api.put('/profile', data);

export default api;
