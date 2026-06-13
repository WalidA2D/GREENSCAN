import { useEffect, useState } from "react";
import { AlertTriangle, RefreshCw, Check, Activity } from "lucide-react";
import Api from "../api/client";
import { useHome } from "../context/HomeContext";
import { Card, Loader, Badge, KpiCard } from "../components/ui";
import { AnomalyScatter } from "../components/charts";
import { fmt, dateTime } from "../lib/format";

const LEVELS = [
  { key: null, label: "Toutes" },
  { key: "critical", label: "Critiques" },
  { key: "warning", label: "Avertissements" },
  { key: "info", label: "Infos" },
];

export default function Alertes() {
  const { homeId } = useHome();
  const [alerts, setAlerts] = useState(null);
  const [anomaly, setAnomaly] = useState(null);
  const [level, setLevel] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    Api.alerts(homeId, level).then(setAlerts);
    Api.anomalies(homeId).then(setAnomaly);
  };
  useEffect(() => { if (homeId) { setAlerts(null); load(); } }, [homeId, level]);

  if (!alerts) return <Loader />;

  const refresh = async () => { setBusy(true); await Api.refreshAlerts(homeId); setBusy(false); load(); };
  const resolve = async (id) => { await Api.resolveAlert(id); load(); };

  const counts = {
    critical: alerts.filter((a) => a.level === "critical").length,
    warning: alerts.filter((a) => a.level === "warning").length,
    info: alerts.filter((a) => a.level === "info").length,
  };

  return (
    <div className="page">
      <div className="grid grid-kpi" style={{ marginBottom: 18 }}>
        <KpiCard label="Alertes critiques" value={counts.critical} icon={<AlertTriangle size={22} />} tint="tint-red" />
        <KpiCard label="Avertissements" value={counts.warning} icon={<AlertTriangle size={22} />} tint="tint-orange" />
        <KpiCard label="Infos" value={counts.info} icon={<AlertTriangle size={22} />} tint="tint-blue" />
        <KpiCard label="Taux d'anomalies IA" value={fmt((anomaly?.anomaly_rate || 0) * 100, 1)} unit="%"
          icon={<Activity size={22} />} tint="tint-orange" />
      </div>

      <div className="toolbar">
        {LEVELS.map((l) => (
          <button key={l.label} className={`btn btn-ghost ${level === l.key ? "active" : ""}`}
            onClick={() => setLevel(l.key)}>{l.label}</button>
        ))}
        <div className="spacer" />
        <button className="btn btn-primary" onClick={refresh} disabled={busy}>
          <RefreshCw size={16} className={busy ? "spin" : ""} /> Recalculer
        </button>
      </div>

      <div className="grid grid-2">
        <Card title="Liste des alertes">
          {alerts.length === 0 && <div className="muted">Aucune alerte pour ce filtre 🎉</div>}
          {alerts.map((a) => (
            <div className="list-item" key={a.id} style={{ opacity: a.is_resolved ? 0.5 : 1 }}>
              <div className={`ico tint-${a.level === "critical" ? "red" : a.level === "warning" ? "orange" : "blue"}`}>
                <AlertTriangle size={18} />
              </div>
              <div className="body">
                <div className="t">{a.title} <Badge kind={a.level}>{a.level}</Badge></div>
                <div className="d">{a.description}</div>
                <div className="d" style={{ marginTop: 4 }}>💡 {a.recommendation}</div>
                <div className="muted" style={{ fontSize: "0.75rem", marginTop: 4 }}>{dateTime(a.detected_at)}</div>
              </div>
              {!a.is_resolved && (
                <button className="btn btn-ghost" style={{ alignSelf: "center", padding: "6px 10px" }}
                  onClick={() => resolve(a.id)}><Check size={14} /> Résoudre</button>
              )}
            </div>
          ))}
        </Card>

        <Card title="Anomalies détectées par l'IA (IsolationForest)"
          extra={`${anomaly?.anomalies?.length || 0} points`}>
          {anomaly?.anomalies?.length ? (
            <>
              <AnomalyScatter data={anomaly.anomalies.slice(0, 40)} />
              <table style={{ marginTop: 12 }}>
                <thead><tr><th>Date / heure</th><th>Conso</th><th>Écart (z)</th><th>Raison</th></tr></thead>
                <tbody>
                  {anomaly.anomalies.slice(0, 8).map((a, i) => (
                    <tr key={i}>
                      <td>{dateTime(a.timestamp)}</td>
                      <td>{fmt(a.consumption_kwh, 2)} kWh</td>
                      <td>{fmt(a.z_score, 1)}</td>
                      <td>{a.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          ) : <div className="muted">Aucune anomalie détectée.</div>}
        </Card>
      </div>
    </div>
  );
}
