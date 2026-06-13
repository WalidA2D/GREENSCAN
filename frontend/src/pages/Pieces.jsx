import { useEffect, useState } from "react";
import { DoorOpen, Flame, Ruler, Users, Plug, TrendingUp } from "lucide-react";
import Api from "../api/client";
import { useHome } from "../context/HomeContext";
import { Card, Loader, ProgressBar, Badge, KpiCard } from "../components/ui";
import { RoomBars } from "../components/charts";
import { fmt, eur, kwh, levelColor } from "../lib/format";

export default function Pieces() {
  const { homeId } = useHome();
  const [rooms, setRooms] = useState(null);

  useEffect(() => {
    if (!homeId) return;
    setRooms(null);
    Api.rooms(homeId).then(setRooms);
  }, [homeId]);

  if (!rooms) return <Loader />;
  if (!rooms.length) return <div className="page muted">Aucune pièce.</div>;

  const top = rooms[0];
  const totalKwh = rooms.reduce((s, r) => s + r.consumption_kwh, 0);
  const maxKwh = Math.max(...rooms.map((r) => r.consumption_kwh), 1);

  return (
    <div className="page">
      <div className="grid grid-3" style={{ marginBottom: 18 }}>
        <KpiCard label="Nombre de pièces" value={rooms.length} icon={<DoorOpen size={22} />} tint="tint-blue" />
        <KpiCard label="Pièce la plus énergivore" value={top.name} icon={<Flame size={22} />} tint="tint-red" />
        <KpiCard label="Consommation totale (30j)" value={fmt(totalKwh)} unit="kWh"
          icon={<TrendingUp size={22} />} tint="tint-green" />
      </div>

      <div className="grid grid-2" style={{ marginBottom: 18 }}>
        <Card title="Comparaison des pièces">
          <RoomBars data={rooms} />
          <div style={{ display: "flex", gap: 16, marginTop: 12, justifyContent: "center", fontSize: "0.82rem" }}>
            <span><span className="dot vert" /> Faible</span>
            <span><span className="dot orange" /> Moyen</span>
            <span><span className="dot rouge" /> Élevé</span>
          </div>
        </Card>

        <Card title="Détail par pièce">
          <table>
            <thead>
              <tr><th>Pièce</th><th>Conso</th><th>Part</th><th>Niveau</th></tr>
            </thead>
            <tbody>
              {rooms.map((r) => (
                <tr key={r.id}>
                  <td><b>{r.name}</b><div className="muted" style={{ fontSize: "0.78rem" }}>{r.surface_m2} m²</div></td>
                  <td>{kwh(r.consumption_kwh)}</td>
                  <td>{fmt(r.share_pct)} %</td>
                  <td><Badge kind={r.level}>{r.level}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>

      {/* ---- Grille visuelle des pièces ---- */}
      <h3 style={{ margin: "8px 0 14px" }}>Carte des pièces</h3>
      <div className="grid grid-3">
        {rooms.map((r) => (
          <div className={`room-card ${r.level}`} key={r.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: "1.05rem" }}>{r.name}</div>
                <div className="muted" style={{ textTransform: "capitalize", fontSize: "0.82rem" }}>{r.room_type.replace(/_/g, " ")}</div>
              </div>
              <Badge kind={r.level}>{r.level}</Badge>
            </div>
            <div style={{ fontSize: "1.7rem", fontWeight: 800, margin: "12px 0 4px" }}>
              {fmt(r.consumption_kwh)}<span className="kpi-unit"> kWh</span>
            </div>
            <ProgressBar value={(r.consumption_kwh / maxKwh) * 100} color={levelColor[r.level]} />
            <div style={{ display: "flex", gap: 14, marginTop: 14, color: "#64748b", fontSize: "0.82rem", flexWrap: "wrap" }}>
              <span><Ruler size={14} /> {r.surface_m2} m²</span>
              <span><Users size={14} /> {r.usual_occupants}</span>
              <span><Flame size={14} /> {fmt(r.target_temperature, 0)}°C</span>
              <span><Plug size={14} /> {r.equipment_count} équip.</span>
              <span>· {eur(r.cost_eur)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
