import { create } from 'zustand';

export const useWorkspaceStore = create((set) => ({
  workspaces: [],
  selectedWorkspace: null,
  
  setWorkspaces: (workspaces) => set({ workspaces }),
  
  setSelectedWorkspace: (workspace) => set({ selectedWorkspace: workspace }),
  
  addWorkspace: (workspace) => set((state) => ({
    workspaces: [...state.workspaces, workspace],
  })),
  
  clearWorkspaces: () => set({ workspaces: [], selectedWorkspace: null }),
}));
