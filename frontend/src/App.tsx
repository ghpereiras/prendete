import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Route, Routes } from "react-router-dom";
import "./App.css";
import LanguageSwitcher from "./components/LanguageSwitcher";
import ProtectedRoute from "./context/ProtectedRoute";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";

export default function App() {
  const { i18n } = useTranslation();

  useEffect(() => {
    document.documentElement.lang = i18n.resolvedLanguage ?? "es";
  }, [i18n.resolvedLanguage]);

  return (
    <>
      <LanguageSwitcher />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}
