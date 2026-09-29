import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import "./App.css";
import Header from "./components/Header";
import NotificationPrompt from "./components/NotificationPrompt";
import { PageTitleProvider } from "./context/PageTitleContext";
import ProtectedRoute from "./context/ProtectedRoute";
import CreateEvent from "./pages/CreateEvent";
import CreatePoll from "./pages/CreatePoll";
import EventDetail from "./pages/EventDetail";
import Events from "./pages/Events";
import InvitePreview from "./pages/InvitePreview";
import Login from "./pages/Login";
import PollDetail from "./pages/PollDetail";
import PollInvitePreview from "./pages/PollInvitePreview";
import Profile from "./pages/Profile";
import Register from "./pages/Register";

const NO_HEADER_PATHS = ["/login", "/register"];

export default function App() {
  const { i18n } = useTranslation();
  const location = useLocation();

  useEffect(() => {
    document.documentElement.lang = i18n.resolvedLanguage ?? "es";
  }, [i18n.resolvedLanguage]);

  return (
    <PageTitleProvider>
      {!NO_HEADER_PATHS.includes(location.pathname) && <Header />}
      {!NO_HEADER_PATHS.includes(location.pathname) && <NotificationPrompt />}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
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
