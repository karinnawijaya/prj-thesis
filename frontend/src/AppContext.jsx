import { createContext, useContext, useMemo, useState } from "react";

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [selectedSet, setSelectedSet] = useState("");
  const [compareId, setCompareId] = useState("");
  const value = useMemo(
    () => ({
      selectedSet,
      setSelectedSet,
      compareId,
      setCompareId,
    }),
    [selectedSet, compareId]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppState() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useAppState must be used within AppProvider");
  }
  return ctx;
}