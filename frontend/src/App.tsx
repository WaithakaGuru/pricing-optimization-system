import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import DashboardPage from "./pages/DashboardPage";
import InventoryPage from "./pages/InventoryPage";
import POSPage from "./pages/POSPage";
import PricesPage from "./pages/PricesPage";
import { AgentDashboardPage } from "./pages/AgentDashboardPage";
import { ModelComparisonPage } from "./pages/ModelComparisonPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="/prices" element={<PricesPage />} />
          <Route path="/pos" element={<POSPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/agents" element={<AgentDashboardPage />} />
          <Route path="/models" element={<ModelComparisonPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
