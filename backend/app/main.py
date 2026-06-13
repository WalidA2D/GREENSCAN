"""Point d'entrée de l'API GreenScan (FastAPI)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.database import init_db
from app.routers import (
    dashboard, homes, rooms, equipments, consumption, kpis,
    predictions, alerts, recommendations, anomalies, simulations,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crée les tables si absentes (idempotent). Le seed reste manuel.
    init_db()
    yield


app = FastAPI(
    title="GreenScan API",
    description="Assistant énergétique intelligent pour particuliers — "
                "suivi, KPI, prévisions IA, alertes et recommandations.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des 11 groupes de routes.
for module in (
    dashboard, homes, rooms, equipments, consumption, kpis,
    predictions, alerts, recommendations, anomalies, simulations,
):
    app.include_router(module.router)


@app.get("/", tags=["health"])
def root():
    return {"name": "GreenScan API", "version": __version__, "docs": "/docs"}


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
