import api from './api';

export const trainingService = {
  // Start training
  startTraining: async (trainingData) => {
    const response = await api.post('/train/start', trainingData);
    return response.data;
  },

  // Get training status
  getTrainingStatus: async () => {
    const response = await api.get('/train/status');
    return response.data;
  },

  // Train with spaCy
  trainSpacy: async (trainingData) => {
    const response = await api.post('/train/intent/spacy', trainingData);
    return response.data;
  },

  // Predict
  predict: async (text, modelId) => {
    const response = await api.post('/predict', {
      text,
      model_id: modelId,
    });
    return response.data;
  },

  // Batch predict
  batchPredict: async (texts, modelId) => {
    const response = await api.post('/predict/batch', {
      texts,
      model_id: modelId,
    });
    return response.data;
  },
};
