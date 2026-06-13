// Graphiques réutilisables basés sur Recharts.
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar, LineChart, Line,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine,
} from "recharts";
import { shortDate, fmt } from "../lib/format";

const GREEN = "#10b981";
const BLUE = "#3b82f6";
const ORANGE = "#f59e0b";
const PALETTE = ["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#ef4444", "#14b8a6", "#ec4899", "#64748b"];

const axis = { tick: { fontSize: 12, fill: "#64748b" }, axisLine: false, tickLine: false };

// Courbe de consommation (aire) — points {period, consumption_kwh, cost_eur}.
export function ConsumptionArea({ data, height = 260, dateAxis = true }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ left: -18, right: 8, top: 8 }}>
        <defs>
          <linearGradient id="gKwh" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={GREEN} stopOpacity={0.35} />
            <stop offset="100%" stopColor={GREEN} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
        <XAxis dataKey="period" {...axis} tickFormatter={dateAxis ? shortDate : undefined} minTickGap={24} />
        <YAxis {...axis} />
        <Tooltip formatter={(v) => `${fmt(v, 1)} kWh`} labelFormatter={dateAxis ? shortDate : undefined} />
        <Area type="monotone" dataKey="consumption_kwh" name="Consommation" stroke={GREEN}
          strokeWidth={2.5} fill="url(#gKwh)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// Barres de consommation par pièce — points {name, consumption_kwh, level}.
export function RoomBars({ data, height = 280 }) {
  const colors = { vert: GREEN, orange: ORANGE, rouge: "#ef4444" };
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 24, right: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" horizontal={false} />
        <XAxis type="number" {...axis} />
        <YAxis type="category" dataKey="name" {...axis} width={110} />
        <Tooltip formatter={(v) => `${fmt(v, 1)} kWh`} />
        <Bar dataKey="consumption_kwh" name="Consommation" radius={[0, 8, 8, 0]} barSize={22}>
          {data.map((d, i) => <Cell key={i} fill={colors[d.level] || BLUE} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// Donut de répartition — points {name, value}.
export function Donut({ data, height = 260, unit = "kWh" }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={62} outerRadius={95} paddingAngle={2}>
          {data.map((d, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
        </Pie>
        <Tooltip formatter={(v) => `${fmt(v, 1)} ${unit}`} />
        <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

// Prévision vs historique — history[] et forecast[] de points {date, value}.
export function ForecastChart({ history, forecast, height = 300 }) {
  // Fusion sur un axe date unique : champs séparés "real" et "pred".
  const merged = [
    ...history.map((p) => ({ date: p.date, real: p.value })),
    ...forecast.map((p) => ({ date: p.date, pred: p.value })),
  ];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={merged} margin={{ left: -18, right: 8, top: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
        <XAxis dataKey="date" {...axis} tickFormatter={shortDate} minTickGap={20} />
        <YAxis {...axis} />
        <Tooltip formatter={(v) => `${fmt(v, 1)} kWh`} labelFormatter={shortDate} />
        <Legend iconType="plainline" wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="real" name="Historique réel" stroke={BLUE}
          strokeWidth={2.5} dot={false} connectNulls />
        <Line type="monotone" dataKey="pred" name="Prévision IA" stroke={GREEN}
          strokeWidth={2.5} strokeDasharray="6 4" dot={{ r: 3 }} connectNulls />
      </LineChart>
    </ResponsiveContainer>
  );
}

// Nuage horaire des anomalies — points {hour, consumption_kwh}.
export function AnomalyScatter({ data, height = 260 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ left: -18, right: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
        <XAxis dataKey="hour" {...axis} label={{ value: "Heure", position: "insideBottom", offset: -2, fontSize: 11 }} />
        <YAxis {...axis} />
        <Tooltip formatter={(v) => `${fmt(v, 2)} kWh`} labelFormatter={(h) => `${h}h`} />
        <Bar dataKey="consumption_kwh" name="Conso anormale" fill="#ef4444" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
