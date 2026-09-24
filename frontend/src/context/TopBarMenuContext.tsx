import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";

type MenuId = "language" | "account";

const CLOSE_DELAY_MS = 150;

interface TopBarMenuContextValue {
  activeMenu: MenuId | null;
  openMenu: (id: MenuId) => void;
  scheduleClose: (id: MenuId) => void;
  closeMenu: (id: MenuId) => void;
}

const TopBarMenuContext = createContext<TopBarMenuContextValue | undefined>(undefined);

export function TopBarMenuProvider({ children }: { children: ReactNode }) {
  const [activeMenu, setActiveMenu] = useState<MenuId | null>(null);
  const closeTimeoutRef = useRef<number | null>(null);

  function cancelPendingClose() {
    if (closeTimeoutRef.current !== null) {
      window.clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
  }

  function openMenu(id: MenuId) {
    cancelPendingClose();
    setActiveMenu(id);
  }

  function scheduleClose(id: MenuId) {
    cancelPendingClose();
    closeTimeoutRef.current = window.setTimeout(() => {
      setActiveMenu((current) => (current === id ? null : current));
    }, CLOSE_DELAY_MS);
  }

  function closeMenu(id: MenuId) {
    cancelPendingClose();
    setActiveMenu((current) => (current === id ? null : current));
  }

  return (
    <TopBarMenuContext.Provider value={{ activeMenu, openMenu, scheduleClose, closeMenu }}>
      {children}
    </TopBarMenuContext.Provider>
  );
}

export function useTopBarMenu(id: MenuId) {
  const ctxOrUndefined = useContext(TopBarMenuContext);
  if (!ctxOrUndefined) {
    throw new Error("useTopBarMenu must be used within a TopBarMenuProvider");
  }
  const ctx = ctxOrUndefined;
  const open = ctx.activeMenu === id;
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        ctx.closeMenu(id);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        ctx.closeMenu(id);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, id, ctx]);

  return {
    open,
    containerRef,
    handleMouseEnter: () => ctx.openMenu(id),
    handleMouseLeave: () => ctx.scheduleClose(id),
    toggle: () => (ctx.activeMenu === id ? ctx.closeMenu(id) : ctx.openMenu(id)),
    close: () => ctx.closeMenu(id),
  };
}
