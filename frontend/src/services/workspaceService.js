import api from './api';

export const workspaceService = {
  // Get all workspaces
  getWorkspaces: async () => {
    const response = await api.get('/workspaces');
    return response.data;
  },

  // Create workspace
  createWorkspace: async (name, description = '') => {
    const response = await api.post('/workspaces/create', {
      name,
      description,
    });
    return response.data;
  },

  // Select workspace
  selectWorkspace: async (workspaceId) => {
    const response = await api.post('/workspaces/select', {
      workspace_id: workspaceId,
    });
    return response.data;
  },
};
