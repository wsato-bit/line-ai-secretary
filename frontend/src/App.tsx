import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import WorkspacePage from './pages/WorkspacePage';
import MemosPage from './pages/MemosPage';
import SettingsPage from './pages/SettingsPage';
import AdminUsersPage from './pages/AdminUsersPage';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<WorkspacePage />} />
      <Route path="/memos" element={<MemosPage />} />
      <Route path="/settings" element={<SettingsPage />} />
      <Route path="/admin/users" element={<AdminUsersPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
