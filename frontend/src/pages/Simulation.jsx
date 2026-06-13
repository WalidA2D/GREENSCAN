import { useEffect, useState } from "react";
import { SlidersHorizontal, PiggyBank, Zap, Leaf, Play } from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
} from "recharts";
import Api from "../api/client";
import { useHome } from "../context/HomeContext";
import { Card, Loader, KpiCard } from "../components/ui";
import { fmt, eur, kwh } from "../lib/format";

export default function Simulation() {
  const { homeId } = useHome();
  const [scenarios, setScenarios] = useState(null);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    Api.scenarios().then((s) => { setScenarios(s); setSelected(s[0]); });
  }, []);

  // Relance la simulation quand le logement ou le scénario change.
  useEffect(() => {
    if (homeId && selected) run(selected);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [homeId, selected?.scenario]);

  if (!scenarios || !selected) return <Loader />;

  const run = async (scenario) => {
    setBusy(true);
    const res = await Api.simulate(homeId, scenario.scenario, scenario.params);
    setResult(res);
    setBusy(false);
  };

  const chartData = result ? [
    { name: "Actuel", value: result.baseline_kwh_month, color: "#94a3b8" },
    { name: "Après optimisation", value: result.simulated_kwh_month, color: "#10b981" },
  ] : [];

  return (
    <div className="page">
      <div className="toolbar">
        {scenarios.map((s) => (
          <button key={s.scenario} className={`btn btn-ghost ${selected.scenario === s.scenario ? "active" : ""}`}
            onClick={() => setSelected(s)}>
            {s.label}
          </button>
        ))}
      </div>

      {!result || busy ? <Loader label="Simulation en cours…" /> : (
        <>
          <div className="grid grid-3" style={{ marginBottom: 18 }}>
            <KpiCard label="Économie / mois" value={eur(result.saving_eur_month)} icon={<PiggyBank size={22} />} tint="tint-green" />
            <KpiCard label="Énergie économisée" value={fmt(result.saving_kwh_month)} unit="kWh" icon={<Zap size={22} />} tint="tint-blue" />
            <KpiCard label="CO₂ évité / mois" value={fmt(result.co2_avoided_kg_month)} unit="kg" icon={<Leaf size={22} />} tint="tint-green" />
          </div>

          <div className="grid grid-2">
            <Card title={<><SlidersHorizontal size={16} /> {selected.label}</>}>
              <p className="muted" style={{ marginBottom: 16 }}>{result.explanation}</p>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={chartData} margin={{ left: -10, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <Tooltip formatter={(v) => `${fmt(v, 1)} kWh`} />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]} barSize={80}>
                    {chartData.map((d, i) => <Cell key={i} fill={d.color} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Résultat de la simulation">
              <div style={{ textAlign: "center", padding: "20px 0" }}>
                <div className="muted">Réduction de consommation</div>
                <div style={{ fontSize: "3rem", fontWeight: 800, color: "#10b981" }}>
                  −{fmt(result.saving_pct, 1)}%
                </div>
              </div>
              <div className="stat-row"><span className="k">Consommation actuelle</span><span className="v">{kwh(result.baseline_kwh_month)}/mois</span></div>
              <div className="stat-row"><span className="k">Après optimisation</span><span className="v">{kwh(result.simulated_kwh_month)}/mois</span></div>
              <div className="stat-row"><span className="k">Économie annuelle projetée</span><span className="v">{eur(result.saving_eur_month * 12)}</span></div>
              <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center", marginTop: 16 }}
                onClick={() => run(selected)}>
                <Play size={16} /> Relancer la simulation
              </button>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
