import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Layout } from './components/Layout';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { CallsPage } from './pages/CallsPage';
import { AppointmentsPage } from './pages/AppointmentsPage';
import { CustomersPage } from './pages/CustomersPage';
import { ServicesPage } from './pages/ServicesPage';
import { StaffPage } from './pages/StaffPage';
import { AvailabilityPage } from './pages/AvailabilityPage';
import { KnowledgePage } from './pages/KnowledgePage';
import { VoiceAgentPage } from './pages/VoiceAgentPage';
import { SettingsPage } from './pages/SettingsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<AuthPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="calls" element={<CallsPage />} />
            <Route path="appointments" element={<AppointmentsPage />} />
            <Route path="customers" element={<CustomersPage />} />
            <Route path="services" element={<ServicesPage />} />
            <Route path="staff" element={<StaffPage />} />
            <Route path="availability" element={<AvailabilityPage />} />
            <Route path="knowledge" element={<KnowledgePage />} />
            <Route path="voice-agent" element={<VoiceAgentPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};
