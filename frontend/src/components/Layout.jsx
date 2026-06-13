import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard, Home, DoorOpen, Plug, TrendingUp,
  Bell, Lightbulb, SlidersHorizontal, Leaf,
} from "lucide-react";
import { useHome } from "../context/HomeContext";

const NAV = [
  { to: "/", label: "Dashboard", icon: <LayoutDashboard size={20} />, end: true },
  { to: "/logement", label: "Logement", icon: <Home size={20} /> },
  { to: "/pieces", label: "Pièces", icon: <DoorOpen size={20} /> },
  { to: "/equipements", label: "Équipements", icon: <Plug size={20} /> },
  { to: "/predictions", label: "Prédictions IA", icon: <TrendingUp size={20} /> },
  { to: "/alertes", label: "Alertes", icon: <Bell size={20} /> },
  { to: "/recommandations", label: "Recommandations", icon: <Lightbulb size={20} /> },
  { to: "/simulation", label: "Simulation", icon: <SlidersHorizontal size={20} /> },
];

const TITLES = {
  "/": ["Tableau de bord", "Vue d'ensemble de votre consommation énergétique"],
  "/logement": ["Mon logement", "Caractéristiques et performance du logement"],
  "/pieces": ["Pièces", "Consommation détaillée pièce par pièce"],
  "/equipements": ["Équipements", "Vos appareils et leur impact énergétique"],
  "/predictions": ["Prédictions IA", "Prévisions de consommation et de facture"],
  "/alertes": ["Alertes intelligentes", "Détections et anomalies de consommation"],
  "/recommandations": ["Recommandations", "Conseils personnalisés pour économiser"],
  "/simulation": ["Simulation", "Testez des scénarios d'optimisation"],
};

export default function Layout({ children }) {
  const { homes, homeId, setHomeId, currentHome } = useHome();
  const { pathname } = useLocation();
  const [title, subtitle] = TITLES[pathname] || ["GreenScan", ""];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Leaf size={26} />
          <span>GreenScan</span>
        </div>
        {NAV.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end}
            className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            {n.icon}
            <span>{n.label}</span>
          </NavLink>
        ))}
        <div className="foot">GreenScan v1.0 · Assistant énergétique</div>
      </aside>

      <div className="main">
        <header className="header">
          <div>
            <h1>{title}</h1>
            <div className="sub">{subtitle}</div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            {currentHome && (
              <span className="tag-soft">
                {currentHome.home_type} · {currentHome.surface_m2} m² · DPE {currentHome.dpe}
              </span>
            )}
            <select value={homeId || ""} onChange={(e) => setHomeId(Number(e.target.value))}>
              {homes.map((h) => (
                <option key={h.id} value={h.id}>{h.name} — {h.city}</option>
              ))}
            </select>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
