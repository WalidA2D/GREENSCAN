import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Zap, Receipt, CalendarClock, CalendarDays, Leaf, AlertTriangle,
  Trash2, Cloud, PiggyBank, Bell, Lightbulb,
} from "lucide-react";
import Api from "../api/client";
import { useHome } from "../context/HomeContext";
import { Card, KpiCard, Gauge, Loader, Badge } from "../components/ui";
import { ConsumptionArea, RoomBars } from "../components/charts";
import { eur, kwh, fmt, dateTime } from "../lib/format";

const kpiVal = (kpis, code) => kpis.find((k) => k.code === code)?.value ?? 0;

export default function Dashboard() {
  const { homeId } = useHome();
  const [data, setData] = useState(null);
  const [granularity, setGranularity] = useState("daily");

  useEffect(() => {
    if (!homeId) return;
    setData(null);
    Api.dashboard(homeId).then(setData);
  }, [homeId]);

  if (!data) return <Loader />;

  const { kpis, predictions, consumption_today_kwh, top_rooms, recent_alerts, quick_recommendations } = data;
  const series = {
    daily: data.consumption_daily,
    weekly: data.consumption_weekly,
    monthly: data.consumption_monthly,
  }[granularity];

  return (
    <div className="page">
      {/* ---- Cartes KPI principales ---- */}
      <div className="grid grid-kpi" style={{ marginBottom: 18 }}>
        <KpiCard label="Consommation aujourd'hui" value={fmt(consumption_today_kwh)} unit="kWh"
          icon={<Zap size={22} />} tint="tint-green" />
        <KpiCard label="Facture estimée (mois)" value={eur(kpiVal(kpis, "facture_estimee"))}
          icon={<Receipt size={22} />} tint="tint-blue" />
        <KpiCard label="Prévision J+1" value={fmt(predictions.consumption_j1_kwh)} unit="kWh"
          icon={<CalendarClock size={22} />} tint="tint-blue" />
        <KpiCard label="Prévision J+7" value={fmt(predictions.consumption_j7_kwh)} unit="kWh"
          icon={<CalendarDays size={22} />} tint="tint-blue" />
        <KpiCard label="Green Score" value={fmt(kpiVal(kpis, "green_score"), 0)} unit="/100"
          icon={<Leaf size={22} />} tint="tint-green" />
        <KpiCard label="Anomaly Score" value={fmt(kpiVal(kpis, "anomaly_score"), 0)} unit="/100"
          icon={<AlertTriangle size={22} />} tint="tint-orange" />
        <KpiCard label="Waste Score" value={fmt(kpiVal(kpis, "waste_score"), 0)} unit="/100"
          icon={<Trash2 size={22} />} tint="tint-red" />
        <KpiCard label="CO₂ émis (30j)" value={fmt(kpiVal(kpis, "co2_emis"))} unit="kg"
          icon={<Cloud size={22} />} tint="tint-gray" />
        <KpiCard label="Économie potentielle" value={eur(kpiVal(kpis, "economie_potentielle"))}
          icon={<PiggyBank size={22} />} tint="tint-green" />
      </div>

      {/* ---- Graphique conso + jauges ---- */}
      <div className="grid grid-2" style={{ marginBottom: 18 }}>
        <Card title="Évolution de la consommation"
          extra={
            <span style={{ display: "flex", gap: 6 }}>
              {["daily", "weekly", "monthly"].map((g) => (
                <button key={g} className={`btn btn-ghost ${granularity === g ? "active" : ""}`}
                  style={{ padding: "5px 11px", fontSize: "0.8rem" }} onClick={() => setGranularity(g)}>
                  {{ daily: "Jour", weekly: "Semaine", monthly: "Mois" }[g]}
                </button>
              ))}
            </span>
          }>
          <ConsumptionArea data={series} dateAxis={granularity !== "weekly" && granularity !== "monthly"} />
        </Card>

        <Card title="Scores IA">
          <div style={{ display: "flex", justifyContent: "space-around", flexWrap: "wrap", gap: 10 }}>
            <Gauge value={kpiVal(kpis, "green_score")} label="Green Score" color="#10b981" />
            <Gauge value={kpiVal(kpis, "anomaly_score")} label="Anomaly Score" color="#f59e0b" />
            <Gauge value={kpiVal(kpis, "waste_score")} label="Waste Score" color="#ef4444" />
          </div>
          <div style={{ marginTop: 8, textAlign: "center" }} className="muted">
            Modèle de prévision : <b>{predictions.model_name}</b>
            {predictions.metrics?.MAPE != null && <> · MAPE {fmt(predictions.metrics.MAPE)}%</>}
          </div>
        </Card>
      </div>

      {/* ---- Pièces énergivores + alertes + recos ---- */}
      <div className="grid grid-2">
        <Card title="Pièces les plus énergivores" extra={<Link to="/pieces" className="muted">Tout voir →</Link>}>
          <RoomBars data={top_rooms} />
        </Card>

        <div className="grid" style={{ gap: 18 }}>
          <Card title={<><Bell size={16} /> Alertes récentes</>}
            extra={<Link to="/alertes" className="muted">Tout voir →</Link>}>
            {recent_alerts.length === 0 && <div className="muted">Aucune alerte 🎉</div>}
            {recent_alerts.map((a) => (
              <div className="list-item" key={a.id}>
                <div className={`ico tint-${a.level === "critical" ? "red" : a.level === "warning" ? "orange" : "blue"}`}>
                  <AlertTriangle size={18} />
                </div>
                <div className="body">
                  <div className="t">{a.title} <Badge kind={a.level}>{a.level}</Badge></div>
                  <div className="d">{a.description}</div>
                </div>
              </div>
            ))}
          </Card>

          <Card title={<><Lightbulb size={16} /> Conseils rapides</>}
            extra={<Link to="/recommandations" className="muted">Tout voir →</Link>}>
            {quick_recommendations.map((r) => (
              <div className="list-item" key={r.id}>
                <div className="ico tint-green"><Lightbulb size={18} /></div>
                <div className="body">
                  <div className="t">{r.action}</div>
                  <div className="d">
                    Gain estimé <b>{eur(r.gain_eur_month)}/mois</b> · {kwh(r.gain_kwh_month)} · CO₂ −{fmt(r.co2_avoided_kg_month)} kg
                  </div>
                </div>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
