// Composants UI réutilisables.
import { fmt } from "../lib/format";

export function Loader({ label = "Chargement…" }) {
  return (
    <div className="center-screen">
      <div style={{ textAlign: "center" }}>
        <div className="spinner" style={{ margin: "0 auto 14px" }} />
        {label}
      </div>
    </div>
  );
}

export function Card({ title, extra, children, style }) {
  return (
    <div className="card" style={style}>
      {title && (
        <div className="card-title">
          {title}
          {extra && <span className="muted" style={{ marginLeft: "auto" }}>{extra}</span>}
        </div>
      )}
      {children}
    </div>
  );
}

export function Badge({ children, kind }) {
  return <span className={`badge ${kind}`}>{children}</span>;
}

// Carte KPI avec icône colorée.
export function KpiCard({ label, value, unit, icon, tint = "tint-green" }) {
  return (
    <div className="kpi">
      <div className={`kpi-icon ${tint}`}>{icon}</div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">
        {value}
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
    </div>
  );
}

// Jauge circulaire (SVG) 0..100 pour Green Score / Anomaly Score / Waste Score.
export function Gauge({ value = 0, max = 100, label, color = "#10b981", size = 150 }) {
  const r = size / 2 - 14;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, value / max));
  const dash = c * pct;
  return (
    <div style={{ textAlign: "center" }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e2e8f0" strokeWidth="12" />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="12"
          strokeLinecap="round" strokeDasharray={`${dash} ${c}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text x="50%" y="47%" textAnchor="middle" fontSize="30" fontWeight="800" fill="#0f172a">
          {fmt(value, 0)}
        </text>
        <text x="50%" y="63%" textAnchor="middle" fontSize="12" fill="#64748b">/ {max}</text>
      </svg>
      {label && <div style={{ fontWeight: 700, marginTop: 4 }}>{label}</div>}
    </div>
  );
}

export function ProgressBar({ value, color = "#10b981" }) {
  return (
    <div className="progress">
      <span style={{ width: `${Math.min(100, value)}%`, background: color }} />
    </div>
  );
}

export function StatRow({ k, v }) {
  return (
    <div className="stat-row">
      <span className="k">{k}</span>
      <span className="v">{v}</span>
    </div>
  );
}

export function EmptyState({ children }) {
  return <div className="center-screen">{children}</div>;
}
