import api from './api';

export const evaluationService = {
  // Run evaluation
  runEvaluation: async (evaluationData) => {
    const response = await api.post('/run', evaluationData);
    return response.data;
  },

  // Save model comparison
  saveModelComparison: async (comparisonData) => {
    const response = await api.post('/model-comparison/save', comparisonData);
    return response.data;
  },
};
