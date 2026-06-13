import { useEffect, useState } from "react";
import { CalendarClock, CalendarDays, Receipt, Gauge as GaugeIcon, Brain } from "lucide-react";
import Api from "../api/client";
import { useHome } from "../context/HomeContext";
import { Card, Loader, KpiCard, ProgressBar, StatRow } from "../components/ui";
import { ForecastChart } from "../components/charts";
import { fmt, eur, kwh } from "../lib/format";

export default function Predictions() {
  const { homeId } = useHome();
  const [pred, setPred] = useState(null);

  useEffect(() => {
    if (!homeId) return;
    setPred(null);
    Api.predictions(homeId, 7).then(setPred);
  }, [homeId]);

  if (!pred) return <Loader />;

  const m = pred.metrics || {};
  const riskPct = pred.budget_overrun_risk * 100;
  const riskColor = riskPct > 66 ? "#ef4444" : riskPct > 33 ? "#f59e0b" : "#10b981";

  return (
    <div className="page">
      <div className="grid grid-kpi" style={{ marginBottom: 18 }}>
        <KpiCard label="Prévision J+1" value={fmt(pred.consumption_j1_kwh)} unit="kWh"
          icon={<CalendarClock size={22} />} tint="tint-blue" />
        <KpiCard label="Prévision J+7" value={fmt(pred.consumption_j7_kwh)} unit="kWh"
          icon={<CalendarDays size={22} />} tint="tint-blue" />
        <KpiCard label="Facture fin de mois" value={eur(pred.monthly_bill_eur)}
          icon={<Receipt size={22} />} tint="tint-orange" />
        <KpiCard label="Risque dépassement budget" value={fmt(riskPct, 0)} unit="%"
          icon={<GaugeIcon size={22} />} tint={riskPct > 50 ? "tint-red" : "tint-green"} />
      </div>

      <div className="grid grid-2" style={{ marginBottom: 18 }}>
        <Card title="Prévision de consommation vs historique"
          extra={<span><Brain size={14} /> {pred.model_name}</span>}>
          <ForecastChart history={pred.history_curve} forecast={pred.forecast_curve} />
        </Card>

        <div className="grid" style={{ gap: 18 }}>
          <Card title="Qualité du modèle IA">
            <StatRow k="MAE (erreur absolue moyenne)" v={m.MAE != null ? `${fmt(m.MAE, 2)} kWh` : "—"} />
            <StatRow k="RMSE" v={m.RMSE != null ? `${fmt(m.RMSE, 2)} kWh` : "—"} />
            <StatRow k="MAPE (erreur %)" v={m.MAPE != null ? `${fmt(m.MAPE, 1)} %` : "—"} />
            <StatRow k="R² (qualité d'ajustement)" v={m.R2 != null ? fmt(m.R2, 3) : "—"} />
            <div className="muted" style={{ fontSize: "0.8rem", marginTop: 10 }}>
              Variables : météo, jour de semaine, week-end, mois, historique (J-1, J-7, moyenne 7j).
            </div>
          </Card>

          <Card title="Budget mensuel">
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <span className="muted">Facture projetée</span>
              <b>{eur(pred.monthly_bill_eur)} / {eur(pred.budget_eur)}</b>
            </div>
            <ProgressBar value={(pred.monthly_bill_eur / Math.max(pred.budget_eur, 1)) * 100} color={riskColor} />
            <div style={{ marginTop: 12, color: riskColor, fontWeight: 700 }}>
              {riskPct > 66 ? "⚠️ Risque élevé de dépassement"
                : riskPct > 33 ? "Surveillez votre budget"
                : "✅ Budget sous contrôle"}
            </div>
          </Card>
        </div>
      </div>

      <Card title="Détail de la prévision (7 prochains jours)">
        <table>
          <thead><tr><th>Date</th><th>Consommation prévue</th></tr></thead>
          <tbody>
            {pred.forecast_curve.map((p) => (
              <tr key={p.date}><td>{p.date}</td><td>{kwh(p.value)}</td></tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
