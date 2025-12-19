import api from './api';

export const datasetService = {
  // Upload dataset
  uploadDataset: async (payload) => {
    const response = await api.post('/datasets', payload);
    return response.data;
  },

  // Get all datasets
  getDatasets: async () => {
    const response = await api.get('/datasets');
    return response.data;
  },

  // Select dataset
  selectDataset: async (checksum) => {
    const response = await api.post('/datasets/select', {
      checksum,
    });
    return response.data;
  },

  // Get complete dataset
  getCompleteDataset: async (checksum) => {
    const response = await api.get(`/datasets/complete/${checksum}`);
    return response.data;
  },
};
