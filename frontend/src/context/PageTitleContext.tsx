import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

interface PageTitleContextValue {
  title: string;
  setTitle: (title: string) => void;
}

const PageTitleContext = createContext<PageTitleContextValue | undefined>(undefined);

export function PageTitleProvider({ children }: { children: ReactNode }) {
  const [title, setTitle] = useState("");

  return (
    <PageTitleContext.Provider value={{ title, setTitle }}>{children}</PageTitleContext.Provider>
  );
}

function useContextOrThrow(): PageTitleContextValue {
  const ctx = useContext(PageTitleContext);
  if (!ctx) {
    throw new Error("must be used within a PageTitleProvider");
  }
  return ctx;
}

// Called by each page to set the title shown in the header.
export function usePageTitle(title: string) {
  const { setTitle } = useContextOrThrow();
  useEffect(() => {
    setTitle(title);
  }, [title, setTitle]);
}

// Called by the header itself to read the current page's title.
export function usePageTitleValue(): string {
  return useContextOrThrow().title;
}
