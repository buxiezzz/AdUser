import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// In a real app, this might be dynamically loaded from config or environment variables
export const API_BASE = 'http://192.168.110.19:8000';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 10000,
});

api.interceptors.request.use(
    async (config) => {
        const token = await AsyncStorage.getItem('utom_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

api.interceptors.response.use(
    (response) => {
        return response;
    },
    async (error) => {
        if (error.response && error.response.status === 401) {
            // Token expired or invalid
            await AsyncStorage.removeItem('utom_token');
            // Additional logout logic can be dispatched from App.js based on auth state
        }
        return Promise.reject(error);
    }
);

export default api;
