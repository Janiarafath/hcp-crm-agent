import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatWithAgent = async (message) => {
  const response = await api.post('/chat', { message });
  return response.data;
};

export const getInteractions = async () => {
  const response = await api.get('/interactions');
  return response.data;
};

export const createInteraction = async (interactionData) => {
  const response = await api.post('/interactions', interactionData);
  return response.data;
};

export const updateInteraction = async (id, interactionData) => {
  const response = await api.put(`/interactions/${id}`, interactionData);
  return response.data;
};

export const deleteInteraction = async (id) => {
  const response = await api.delete(`/interactions/${id}`);
  return response.data;
};

export const searchHCP = async (name) => {
  const response = await api.get(`/search/${name}`);
  return response.data;
};

export default api;
