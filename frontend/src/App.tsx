import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import "./App.css";
import { API_URL } from "./api/client";
import Header from "./components/Header";
import NotificationPrompt from "./components/NotificationPrompt";
import { PageTitleProvider } from "./context/PageTitleContext";
import ProtectedRoute from "./context/ProtectedRoute";
import Admin from "./pages/Admin";
import CreateEvent from "./pages/CreateEvent";
import CreatePoll from "./pages/CreatePoll";
import EventDetail from "./pages/EventDetail";
import Events from "./pages/Events";
import GoogleCallback from "./pages/GoogleCallback";
import ForgotPassword from "./pages/ForgotPassword";
import LegalPage from "./pages/LegalPage";
import InvitePreview from "./pages/InvitePreview";
import Login from "./pages/Login";
import PollDetail from "./pages/PollDetail";
import PollInvitePreview from "./pages/PollInvitePreview";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import VerifyEmail from "./pages/VerifyEmail";
import VerifyEmailBanner from "./components/VerifyEmailBanner";

const NO_HEADER_PATHS = ["/login", "/register", "/verify-email", "/forgot-password", "/reset-password"];

export default function App() {
  const { i18n } = useTranslation();
  const location = useLocation();
  const hideHeader = NO_HEADER_PATHS.some((path) => location.pathname.startsWith(path));

  useEffect(() => {
    document.documentElement.lang = i18n.resolvedLanguage ?? "es";
  }, [i18n.resolvedLanguage]);

  useEffect(() => {
    // Free-tier backends can be asleep on the first visit — wake it up as
    // soon as the app loads instead of waiting for the user's first request.
    fetch(`${API_URL}/health`).catch(() => {});
  }, []);

  return (
    <PageTitleProvider>
      {!hideHeader && <Header />}
      {!hideHeader && <VerifyEmailBanner />}
      {!hideHeader && <NotificationPrompt />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/auth/google/callback" element={<GoogleCallback />} />
        <Route path="/verify-email/:token" element={<VerifyEmail />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:token" element={<ResetPassword />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <Admin />
            </ProtectedRoute>
          }
        />
        <Route path="/privacy" element={<LegalPage namespace="privacy" />} />
        <Route path="/terms" element={<LegalPage namespace="terms" />} />
        <Route path="/invite/:token" element={<InvitePreview />} />
        <Route path="/polls/invite/:token" element={<PollInvitePreview />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Navigate to="/events" replace />
            </ProtectedRoute>
          }
        />
        <Route
          path="/events"
          element={
            <ProtectedRoute>
              <Events />
            </ProtectedRoute>
          }
        />
        <Route
          path="/events/new"
          element={
            <ProtectedRoute>
              <CreateEvent />
            </ProtectedRoute>
          }
        />
        <Route
          path="/events/:eventId/edit"
          element={
            <ProtectedRoute>
              <CreateEvent />
            </ProtectedRoute>
          }
        />
        <Route
          path="/events/:eventId"
          element={
            <ProtectedRoute>
              <EventDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/polls/new"
          element={
            <ProtectedRoute>
              <CreatePoll />
            </ProtectedRoute>
          }
        />
        <Route
          path="/polls/:pollId"
          element={
            <ProtectedRoute>
              <PollDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
      </Routes>
    </PageTitleProvider>
  );
}
