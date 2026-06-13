import { useEffect, useState } from "react";
import { Lightbulb, RefreshCw, PiggyBank, Leaf, Zap } from "lucide-react";
import Api from "../api/client";
import { useHome } from "../context/HomeContext";
import { Card, Loader, Badge, KpiCard } from "../components/ui";
import { fmt, eur, kwh } from "../lib/format";

export default function Recommandations() {
  const { homeId } = useHome();
  const [recos, setRecos] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = () => Api.recommendations(homeId).then(setRecos);
  useEffect(() => { if (homeId) { setRecos(null); load(); } }, [homeId]);

  if (!recos) return <Loader />;

  const refresh = async () => { setBusy(true); await Api.refreshRecommendations(homeId); setBusy(false); load(); };

  const totalEur = recos.reduce((s, r) => s + r.gain_eur_month, 0);
  const totalKwh = recos.reduce((s, r) => s + r.gain_kwh_month, 0);
  const totalCo2 = recos.reduce((s, r) => s + r.co2_avoided_kg_month, 0);

  return (
    <div className="page">
      <div className="grid grid-3" style={{ marginBottom: 18 }}>
        <KpiCard label="Économie potentielle / mois" value={eur(totalEur)} icon={<PiggyBank size={22} />} tint="tint-green" />
        <KpiCard label="Énergie économisable / mois" value={fmt(totalKwh)} unit="kWh" icon={<Zap size={22} />} tint="tint-blue" />
        <KpiCard label="CO₂ évité / mois" value={fmt(totalCo2)} unit="kg" icon={<Leaf size={22} />} tint="tint-green" />
      </div>

      <div className="toolbar">
        <div className="spacer" />
        <button className="btn btn-primary" onClick={refresh} disabled={busy}>
          <RefreshCw size={16} className={busy ? "spin" : ""} /> Régénérer les conseils
        </button>
      </div>

      <div className="grid grid-2">
        {recos.map((r) => (
          <Card key={r.id}>
            <div style={{ display: "flex", gap: 14 }}>
              <div className="ico tint-green" style={{ width: 46, height: 46, borderRadius: 12, display: "grid", placeItems: "center", flexShrink: 0 }}>
                <Lightbulb size={22} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 800, fontSize: "1.05rem" }}>{r.action}</div>
                <div style={{ display: "flex", gap: 8, margin: "8px 0", flexWrap: "wrap" }}>
                  <Badge kind={r.impact}>Impact {r.impact}</Badge>
                  <Badge kind={r.difficulty}>{r.difficulty}</Badge>
                </div>
                <div className="grid grid-3" style={{ gap: 8, marginTop: 10 }}>
                  <div><div className="muted" style={{ fontSize: "0.76rem" }}>Gain €/mois</div><b>{eur(r.gain_eur_month)}</b></div>
                  <div><div className="muted" style={{ fontSize: "0.76rem" }}>Gain kWh/mois</div><b>{kwh(r.gain_kwh_month)}</b></div>
                  <div><div className="muted" style={{ fontSize: "0.76rem" }}>CO₂ évité</div><b>{fmt(r.co2_avoided_kg_month)} kg</b></div>
                </div>
              </div>
            </div>
          </Card>
        ))}
        {recos.length === 0 && <div className="muted">Aucune recommandation : votre consommation est déjà optimisée 🎉</div>}
      </div>
    </div>
  );
}
