import { create } from 'zustand';

export const useDatasetStore = create((set) => ({
  datasets: [],
  selectedDataset: null,
  currentDatasetData: null,
  uploadedFiles: [],
  
  setDatasets: (datasets) => set({ datasets }),
  
  setSelectedDataset: (dataset) => set({ selectedDataset: dataset }),
  
  setCurrentDatasetData: (data) => set({ currentDatasetData: data }),
  
  addUploadedFile: (file) => set((state) => ({
    uploadedFiles: [...state.uploadedFiles, file],
  })),
  
  clearDatasets: () => set({
    datasets: [],
    selectedDataset: null,
    currentDatasetData: null,
    uploadedFiles: [],
  }),
}));
