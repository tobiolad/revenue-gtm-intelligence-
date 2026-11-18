import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import OverviewPage from "./pages/OverviewPage";
import FunnelPage from "./pages/FunnelPage";
import ForecastPage from "./pages/ForecastPage";
import RepsPage from "./pages/RepsPage";
import DealsPage from "./pages/DealsPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/funnel" element={<FunnelPage />} />
        <Route path="/forecast" element={<ForecastPage />} />
        <Route path="/reps" element={<RepsPage />} />
        <Route path="/deals" element={<DealsPage />} />
      </Routes>
    </Layout>
  );
}
