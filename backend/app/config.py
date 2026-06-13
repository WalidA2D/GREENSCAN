"""Configuration centralisée de l'application (lue depuis .env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres applicatifs et métier de GreenScan."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Base de données ---
    database_url: str = "postgresql+psycopg://greenscan:greenscan@localhost:5432/greenscan"

    # --- Paramètres métier (alignés sur KPI_GREEN_Professionnel.xlsx) ---
    co2_factor_kg_per_kwh: float = 0.052       # CO2 émis = kWh × facteur CO2
    price_hp_eur_per_kwh: float = 0.2516       # Facture = kWh × prix kWh (heures pleines)
    price_hc_eur_per_kwh: float = 0.2032       # heures creuses

    # --- CORS ---
    frontend_origin: str = "http://localhost:5173"

    # --- ML ---
    ml_artifacts_dir: str = "ml/artifacts"

    @property
    def cors_origins(self) -> list[str]:
        # Autorise le port Vite par défaut + variantes localhost.
        base = {self.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"}
        return sorted(base)


@lru_cache
def get_settings() -> Settings:
    """Singleton de configuration (mis en cache)."""
    return Settings()


settings = get_settings()
