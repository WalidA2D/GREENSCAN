import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import { useHome } from "./context/HomeContext";
import { Loader } from "./components/ui";

import Dashboard from "./pages/Dashboard";
import Logement from "./pages/Logement";
import Pieces from "./pages/Pieces";
import Equipements from "./pages/Equipements";
import Predictions from "./pages/Predictions";
import Alertes from "./pages/Alertes";
import Recommandations from "./pages/Recommandations";
import Simulation from "./pages/Simulation";

export default function App() {
  const { loading, homes } = useHome();

  if (loading) return <Loader label="Connexion à GreenScan…" />;
  if (!homes.length)
    return (
      <div className="center-screen">
        Aucun logement trouvé. Lancez <code style={{ margin: "0 6px" }}>python -m scripts.generate_data</code>
        côté backend.
      </div>
    );

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/logement" element={<Logement />} />
        <Route path="/pieces" element={<Pieces />} />
        <Route path="/equipements" element={<Equipements />} />
        <Route path="/predictions" element={<Predictions />} />
        <Route path="/alertes" element={<Alertes />} />
        <Route path="/recommandations" element={<Recommandations />} />
        <Route path="/simulation" element={<Simulation />} />
      </Routes>
    </Layout>
  );
}
