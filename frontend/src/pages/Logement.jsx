import { useEffect, useState } from "react";
import { Home, Ruler, Users, Thermometer, Sun, Car, Building2, Wallet } from "lucide-react";
import Api from "../api/client";
import { useHome } from "../context/HomeContext";
import { Card, Loader, StatRow, KpiCard } from "../components/ui";
import { fmt, eur } from "../lib/format";

const DPE_COLORS = { A: "#22c55e", B: "#84cc16", C: "#eab308", D: "#f59e0b", E: "#f97316", F: "#ef4444", G: "#b91c1c" };
const kpiVal = (kpis, code) => kpis.find((k) => k.code === code)?.value ?? 0;

export default function Logement() {
  const { homeId, currentHome } = useHome();
  const [kpis, setKpis] = useState(null);

  useEffect(() => {
    if (!homeId) return;
    Api.kpis(homeId).then(setKpis);
  }, [homeId]);

  if (!currentHome || !kpis) return <Loader />;
  const h = currentHome;

  return (
    <div className="page">
      <div className="grid grid-2" style={{ marginBottom: 18 }}>
        <Card title={<><Home size={16} /> {h.name}</>}>
          <StatRow k="Type de logement" v={<span style={{ textTransform: "capitalize" }}>{h.home_type}</span>} />
          <StatRow k="Ville" v={h.city} />
          <StatRow k="Surface" v={`${fmt(h.surface_m2)} m²`} />
          <StatRow k="Année de construction" v={h.construction_year || "—"} />
          <StatRow k="Orientation" v={h.orientation || "—"} />
          <StatRow k="Occupants" v={h.occupants_count} />
          <StatRow k="Type de chauffage" v={h.heating_type} />
          <StatRow k="Puissance souscrite" v={`${fmt(h.contracted_power_kva)} kVA`} />
          <StatRow k="Budget mensuel" v={eur(h.monthly_budget_eur)} />
        </Card>

        <Card title="Performance énergétique (DPE)">
          <div style={{ textAlign: "center", padding: "10px 0 18px" }}>
            <div style={{
              width: 88, height: 88, borderRadius: 20, margin: "0 auto 12px",
              display: "grid", placeItems: "center", color: "#fff", fontSize: "2.6rem", fontWeight: 800,
              background: DPE_COLORS[h.dpe] || "#64748b",
            }}>
              {h.dpe}
            </div>
            <div className="muted">Diagnostic de Performance Énergétique</div>
          </div>
          <StatRow k="Intensité (Conso/occupant)" v={`${fmt(kpiVal(kpis, "conso_par_occupant"))} kWh`} />
          <StatRow k="Part du chauffage" v={`${fmt(kpiVal(kpis, "chauffage_pct"))} %`} />
          <StatRow k="Autonomie énergétique" v={`${fmt(kpiVal(kpis, "autonomie_pct"))} %`} />
          <StatRow k="Heures pleines" v={`${fmt(kpiVal(kpis, "hp_hc_pct"))} %`} />
        </Card>
      </div>

      <div className="grid grid-3" style={{ marginBottom: 18 }}>
        <KpiCard label="Surface" value={fmt(h.surface_m2)} unit="m²" icon={<Ruler size={22} />} tint="tint-blue" />
        <KpiCard label="Occupants" value={h.occupants_count} icon={<Users size={22} />} tint="tint-green" />
        <KpiCard label="Chauffage" value={h.heating_type} icon={<Thermometer size={22} />} tint="tint-orange" />
        <KpiCard label="Panneaux solaires" value={h.has_solar_panels ? "Oui" : "Non"} icon={<Sun size={22} />}
          tint={h.has_solar_panels ? "tint-green" : "tint-gray"} />
        <KpiCard label="Véhicule électrique" value={h.has_ev ? "Oui" : "Non"} icon={<Car size={22} />}
          tint={h.has_ev ? "tint-green" : "tint-gray"} />
        <KpiCard label="Green Score" value={fmt(kpiVal(kpis, "green_score"), 0)} unit="/100"
          icon={<Building2 size={22} />} tint="tint-green" />
      </div>

      <Card title={<><Wallet size={16} /> Synthèse financière & écologique (30 derniers jours)</>}>
        <div className="grid grid-3">
          <StatRow k="Consommation totale" v={`${fmt(kpiVal(kpis, "conso_totale"))} kWh`} />
          <StatRow k="Facture estimée" v={eur(kpiVal(kpis, "facture_estimee"))} />
          <StatRow k="Économie potentielle" v={eur(kpiVal(kpis, "economie_potentielle"))} />
          <StatRow k="Économie annuelle projetée" v={eur(kpiVal(kpis, "economie_annuelle"))} />
          <StatRow k="CO₂ émis" v={`${fmt(kpiVal(kpis, "co2_emis"))} kg`} />
          <StatRow k="CO₂ évitable" v={`${fmt(kpiVal(kpis, "co2_evitable"))} kg`} />
        </div>
      </Card>
    </div>
  );
}
