import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const CLOSE_DELAY_MS = 300;

export default function AccountMenu() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const closeTimeoutRef = useRef<number | null>(null);

  function clearCloseTimeout() {
    if (closeTimeoutRef.current !== null) {
      window.clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
  }

  function handleMouseEnter() {
    clearCloseTimeout();
    setOpen(true);
  }

  function handleMouseLeave() {
    clearCloseTimeout();
    closeTimeoutRef.current = window.setTimeout(() => {
      setOpen(false);
    }, CLOSE_DELAY_MS);
  }

  useEffect(() => clearCloseTimeout, []);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  if (!user) return null;

  const initial = user.full_name.trim().charAt(0).toUpperCase();

  function goToProfile() {
    clearCloseTimeout();
    setOpen(false);
    navigate("/profile");
  }

  function handleLogout() {
    clearCloseTimeout();
    setOpen(false);
    logout();
  }

  return (
    <div
      className="account-menu"
      ref={containerRef}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button
        type="button"
        className="account-menu-trigger"
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t("account.label")}
      >
        {initial}
      </button>
      {open && (
        <div className="account-menu-dropdown" role="menu">
          <button type="button" role="menuitem" onClick={goToProfile}>
            {t("account.profile")}
          </button>
          <button type="button" role="menuitem" onClick={handleLogout}>
            {t("account.logout")}
          </button>
        </div>
      )}
    </div>
  );
}
