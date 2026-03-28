import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  isGlobalLoading: boolean;
  snackbar: {
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  };

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setGlobalLoading: (loading: boolean) => void;
  showSnackbar: (message: string, severity?: 'success' | 'error' | 'warning' | 'info') => void;
  hideSnackbar: () => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  isGlobalLoading: false,
  snackbar: {
    open: false,
    message: '',
    severity: 'info',
  },

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  setGlobalLoading: (loading) => set({ isGlobalLoading: loading }),

  showSnackbar: (message, severity = 'info') =>
    set({ snackbar: { open: true, message, severity } }),

  hideSnackbar: () =>
    set((state) => ({ snackbar: { ...state.snackbar, open: false } })),
}));
