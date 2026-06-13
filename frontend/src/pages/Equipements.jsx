import { useEffect, useState } from "react";
import { Plug, Power, PowerOff } from "lucide-react";
import Api from "../api/client";
import { useHome } from "../context/HomeContext";
import { Card, Loader, KpiCard } from "../components/ui";
import { Donut } from "../components/charts";
import { fmt, kwh } from "../lib/format";

const CRIT_TINT = { 5: "tint-red", 4: "tint-orange", 3: "tint-orange", 2: "tint-blue", 1: "tint-gray" };

export default function Equipements() {
  const { homeId } = useHome();
  const [equipments, setEquipments] = useState(null);
  const [rooms, setRooms] = useState([]);

  const load = () => {
    Api.equipments(homeId).then(setEquipments);
    Api.rooms(homeId).then(setRooms);
  };
  useEffect(() => { if (homeId) { setEquipments(null); load(); } }, [homeId]);

  if (!equipments) return <Loader />;

  const roomName = (id) => rooms.find((r) => r.id === id)?.name || "—";

  // Répartition (donut) par équipement, hors panneaux solaires.
  const donut = equipments
    .filter((e) => e.estimated_kwh_month > 0)
    .map((e) => ({ name: e.name, value: e.estimated_kwh_month }));

  const totalKwh = donut.reduce((s, d) => s + d.value, 0);
  const activeCount = equipments.filter((e) => e.is_active).length;

  const toggle = async (e) => {
    await Api.updateEquipment(e.id, { is_active: !e.is_active });
    load();
  };

  return (
    <div className="page">
      <div className="grid grid-3" style={{ marginBottom: 18 }}>
        <KpiCard label="Équipements" value={equipments.length} icon={<Plug size={22} />} tint="tint-blue" />
        <KpiCard label="Actifs" value={`${activeCount} / ${equipments.length}`} icon={<Power size={22} />} tint="tint-green" />
        <KpiCard label="Conso estimée (mois)" value={fmt(totalKwh)} unit="kWh" icon={<Plug size={22} />} tint="tint-orange" />
      </div>

      <div className="grid grid-2" style={{ marginBottom: 18 }}>
        <Card title="Répartition de la consommation par équipement">
          <Donut data={donut} />
        </Card>

        <Card title="Détail des équipements" extra={`${equipments.length} appareils`}>
          <table>
            <thead>
              <tr><th>Équipement</th><th>Pièce</th><th>Puissance</th><th>Conso/mois</th><th>Criticité</th><th>État</th></tr>
            </thead>
            <tbody>
              {equipments.map((e) => (
                <tr key={e.id}>
                  <td><b>{e.name}</b><div className="muted" style={{ fontSize: "0.76rem", textTransform: "capitalize" }}>{e.equipment_type.replace(/_/g, " ")}</div></td>
                  <td>{roomName(e.room_id)}</td>
                  <td>{fmt(e.rated_power_w, 0)} W</td>
                  <td>{kwh(e.estimated_kwh_month)}</td>
                  <td><span className={`badge ${CRIT_TINT[e.criticality]}`}>{e.criticality}/5</span></td>
                  <td>
                    <button className="btn btn-ghost" style={{ padding: "5px 10px", fontSize: "0.78rem" }}
                      onClick={() => toggle(e)}>
                      {e.is_active ? <><Power size={14} /> Actif</> : <><PowerOff size={14} /> Inactif</>}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  );
}
