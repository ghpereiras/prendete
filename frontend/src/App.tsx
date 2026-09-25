import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Route, Routes, useLocation } from "react-router-dom";
import "./App.css";
import Header from "./components/Header";
import { PageTitleProvider } from "./context/PageTitleContext";
import ProtectedRoute from "./context/ProtectedRoute";
import CreateEvent from "./pages/CreateEvent";
import EventDetail from "./pages/EventDetail";
import Home from "./pages/Home";
import InvitePreview from "./pages/InvitePreview";
import Login from "./pages/Login";
import PastEvents from "./pages/PastEvents";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import UpcomingEvents from "./pages/UpcomingEvents";

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
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/invite/:token" element={<InvitePreview />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
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
          path="/events/upcoming"
          element={
            <ProtectedRoute>
              <UpcomingEvents />
            </ProtectedRoute>
          }
        />
        <Route
          path="/events/past"
          element={
            <ProtectedRoute>
              <PastEvents />
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
