"""Catalogue de référence métier GreenScan.

Centralise les hypothèses physiques/énergétiques réutilisées par :
- la génération de données (scripts/generate_data.py)
- le moteur de KPI / recommandations / alertes
- les simulations "what-if"

Les valeurs sont des ordres de grandeur réalistes (logement résidentiel français).
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Équipements : puissance nominale (W), usage moyen (h/jour), criticité (1-5)
# --------------------------------------------------------------------------- #
EQUIPMENT_CATALOG: dict[str, dict] = {
    "chauffage":        {"rated_power_w": 1500, "daily_usage_hours": 6.0, "criticality": 5},
    "pompe_a_chaleur":  {"rated_power_w": 2000, "daily_usage_hours": 5.0, "criticality": 5},
    "climatisation":    {"rated_power_w": 1200, "daily_usage_hours": 2.0, "criticality": 4},
    "chauffe_eau":      {"rated_power_w": 2000, "daily_usage_hours": 3.0, "criticality": 4},
    "four":             {"rated_power_w": 2500, "daily_usage_hours": 0.6, "criticality": 3},
    "lave_linge":       {"rated_power_w": 2000, "daily_usage_hours": 0.7, "criticality": 3},
    "refrigerateur":    {"rated_power_w": 150,  "daily_usage_hours": 24.0, "criticality": 3},
    "borne_ve":         {"rated_power_w": 7400, "daily_usage_hours": 2.5, "criticality": 5},
    "television":       {"rated_power_w": 120,  "daily_usage_hours": 4.0, "criticality": 2},
    "ordinateur":       {"rated_power_w": 150,  "daily_usage_hours": 5.0, "criticality": 2},
    "eclairage":        {"rated_power_w": 60,   "daily_usage_hours": 5.0, "criticality": 1},
    "panneaux_solaires": {"rated_power_w": 3000, "daily_usage_hours": 0.0, "criticality": 1},
}

# Étiquette d'affichage lisible.
EQUIPMENT_LABELS: dict[str, str] = {
    "chauffage": "Chauffage",
    "pompe_a_chaleur": "Pompe à chaleur",
    "climatisation": "Climatisation",
    "chauffe_eau": "Chauffe-eau",
    "four": "Four",
    "lave_linge": "Lave-linge",
    "refrigerateur": "Réfrigérateur",
    "borne_ve": "Borne de recharge VE",
    "television": "Télévision",
    "ordinateur": "Ordinateur",
    "eclairage": "Éclairage",
    "panneaux_solaires": "Panneaux solaires",
}

ROOM_LABELS: dict[str, str] = {
    "piece_principale": "Pièce principale",
    "salon": "Salon",
    "cuisine": "Cuisine",
    "salle_de_bain": "Salle de bain",
    "chambre": "Chambre",
    "bureau": "Bureau",
    "garage": "Garage",
    "cave": "Cave",
}

# --------------------------------------------------------------------------- #
# Modèles de pièces par type d'équipement habituellement présent.
# --------------------------------------------------------------------------- #
ROOM_EQUIPMENT_DEFAULTS: dict[str, list[str]] = {
    "piece_principale": ["television", "eclairage", "chauffage", "ordinateur"],
    "salon":            ["television", "eclairage", "chauffage"],
    "cuisine":          ["refrigerateur", "four", "lave_linge", "eclairage"],
    "salle_de_bain":    ["chauffe_eau", "eclairage", "chauffage"],
    "chambre":          ["eclairage", "chauffage", "television"],
    "bureau":           ["ordinateur", "eclairage", "chauffage"],
    "garage":           ["borne_ve", "eclairage"],
    "cave":             ["eclairage"],
}

# --------------------------------------------------------------------------- #
# Archétypes de logement : composition de pièces typique.
# --------------------------------------------------------------------------- #
HOME_ARCHETYPES: dict[str, dict] = {
    "studio": {
        "surface_m2": 28,
        "rooms": [
            ("Pièce principale", "piece_principale", 20, 0),
            ("Cuisine", "cuisine", 5, 0),
            ("Salle de bain", "salle_de_bain", 3, 0),
        ],
    },
    "appartement": {
        "surface_m2": 65,
        "rooms": [
            ("Salon", "salon", 24, 1),
            ("Cuisine", "cuisine", 10, 1),
            ("Chambre 1", "chambre", 12, 1),
            ("Chambre 2", "chambre", 10, 1),
            ("Salle de bain", "salle_de_bain", 6, 1),
        ],
    },
    "maison": {
        "surface_m2": 120,
        "rooms": [
            ("Salon", "salon", 32, 0),
            ("Cuisine", "cuisine", 14, 0),
            ("Chambre 1", "chambre", 14, 1),
            ("Chambre 2", "chambre", 12, 1),
            ("Bureau", "bureau", 10, 1),
            ("Salle de bain", "salle_de_bain", 8, 1),
            ("Garage", "garage", 18, 0),
            ("Cave", "cave", 15, -1),
        ],
    },
}

# --------------------------------------------------------------------------- #
# Coefficient d'isolation selon le DPE (multiplie le besoin de chauffage).
# A = très bien isolé (peu de pertes) ... G = passoire thermique.
# --------------------------------------------------------------------------- #
DPE_HEATING_FACTOR: dict[str, float] = {
    "A": 0.45, "B": 0.6, "C": 0.8, "D": 1.0, "E": 1.3, "F": 1.7, "G": 2.2,
}

# Efficacité du système de chauffage (kWh élec par kWh de chaleur utile).
HEATING_EFFICIENCY: dict[str, float] = {
    "PAC": 0.33,          # COP ~3
    "électrique": 1.0,    # effet Joule
    "gaz": 0.15,          # peu d'élec (juste régulation/pompe) -> faible part électrique
}

# Profil horaire d'usage électrique (hors chauffage), 24 valeurs normalisées (~moyenne 1).
HOURLY_USAGE_PROFILE: list[float] = [
    0.45, 0.40, 0.38, 0.37, 0.38, 0.45,   # 0h-5h : nuit
    0.70, 1.10, 1.20, 0.95, 0.85, 0.90,   # 6h-11h : matin
    1.15, 1.00, 0.80, 0.78, 0.85, 1.15,   # 12h-17h : journée
    1.55, 1.70, 1.55, 1.20, 0.80, 0.55,   # 18h-23h : soirée (pic)
]

# Heures creuses (tarif HC), sinon heures pleines (HP).
OFF_PEAK_HOURS = set(range(22, 24)) | set(range(0, 6))  # 22h-6h


def is_off_peak(hour: int) -> bool:
    return hour in OFF_PEAK_HOURS
