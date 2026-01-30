import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '@/app/context/AuthContext';
import ProtectedRoute from '@/app/components/ProtectedRoute';
import LandingPage from '@/app/pages/LandingPage';
import LoginPage from '@/app/pages/auth/LoginPage';
import SignUpPage from '@/app/pages/auth/SignUpPage';
import ForgotPasswordPage from '@/app/pages/auth/ForgotPasswordPage';
import DashboardLayout from '@/app/components/DashboardLayout';
import Home from '@/app/pages/dashboard/Home';
import RegisterCase from '@/app/pages/dashboard/RegisterCase';
import AllCases from '@/app/pages/dashboard/AllCases';
import MatchCases from '@/app/pages/dashboard/MatchCases';
import MobileApp from '@/app/pages/dashboard/MobileApp';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignUpPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Home />} />
            <Route path="register-case" element={<RegisterCase />} />
            <Route path="all-cases" element={<AllCases />} />
            <Route path="match-cases" element={<MatchCases />} />
            <Route path="mobile-app" element={<MobileApp />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}