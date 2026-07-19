import { Navigate, Route, Routes } from "react-router-dom";
import { useState } from "react";

import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { InventoryPage } from "./pages/InventoryPage";

export default function App(): JSX.Element {
  const [refreshToken, setRefreshToken] = useState(0);

  function handleInventoryChanged(): void {
    setRefreshToken((current) => current + 1);
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage refreshToken={refreshToken} />} />
        <Route
          path="/inventory"
          element={<InventoryPage refreshToken={refreshToken} onInventoryChanged={handleInventoryChanged} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
