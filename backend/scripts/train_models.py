"""Entraîne tous les modèles IA (consommation + anomalies) pour chaque logement.

Usage (depuis backend/, après generate_data) :
    python -m scripts.train_models
"""
from __future__ import annotations

import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database import SessionLocal
from app.ml.train import train_all


def main() -> None:
    db = SessionLocal()
    try:
        print("· Entraînement des modèles IA par logement...")
        results = train_all(db)
        for r in results:
            cons = r["consumption"]
            m = cons.get("metrics", {})
            print(f"   · {r['name']}: modèle={cons.get('model_name', 'n/a')} "
                  f"MAE={m.get('MAE')} RMSE={m.get('RMSE')} MAPE={m.get('MAPE')}% R²={m.get('R2')} "
                  f"| anomalies={r['anomaly'].get('anomaly_rate')}")
        print("\n✅ Modèles entraînés et sauvegardés dans ml/artifacts/.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
