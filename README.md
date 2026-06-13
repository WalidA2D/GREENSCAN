# 🌿 GreenScan — Assistant énergétique intelligent

GreenScan est une application complète permettant aux particuliers de **suivre, analyser, prédire et optimiser** leur consommation énergétique. Ce n'est pas un simple afficheur de courbes : c'est un **assistant énergétique personnalisé** qui s'adapte à tout type de logement (studio, appartement, maison) avec une structure relationnelle dynamique (logement → pièces → équipements → mesures).

> Projet construit à partir des deux référentiels métier `Patrimoine_Donnees_GREEN_Professionnel.xlsx` (38 variables, 5 sources, 6 variables IA) et `KPI_GREEN_Professionnel.xlsx` (KPI énergétiques, financiers, écologiques, IA + dashboard cible).

---

## ✨ Fonctionnalités

| Domaine | Détail |
|---|---|
| **Dashboard** | Conso actuelle, facture estimée, prévisions J+1 / J+7, Green/Anomaly/Waste Score, CO₂, économie potentielle, courbes jour/semaine/mois |
| **Pièces** | Structure relationnelle dynamique, consommation par pièce, code couleur vert/orange/rouge, pièce la plus énergivore, grille visuelle |
| **Équipements** | 12 types (chauffage, PAC, four, VE, panneaux solaires…), puissance, conso estimée, criticité 1-5, état actif/inactif |
| **Alertes IA** | Surconsommation, conso nocturne anormale, chauffage par temps doux, équipement énergivore, dérive, dépassement de moyenne |
| **Recommandations** | Conseils chiffrés (gain €/mois, kWh, CO₂ évité, impact, difficulté) |
| **Prédiction IA** | RandomForest (fallback LinearRegression), prévision J+1/J+7, facture fin de mois, risque budget + métriques MAE/RMSE/MAPE/R² |
| **Anomalies** | IsolationForest sur les pas 30 min |
| **Simulation** | Scénarios « baisser le chauffage », « heures creuses », « panneaux solaires », « réduire le nocturne » |

---

## 🏗️ Architecture

```
Openinnovation/
├── docker-compose.yml          # PostgreSQL (+ backend optionnel)
├── README.md
├── backend/                    # API FastAPI + IA
│   ├── app/
│   │   ├── main.py             # app FastAPI + CORS + routers
│   │   ├── config.py           # configuration (.env)
│   │   ├── database.py         # SQLAlchemy engine/session
│   │   ├── schemas.py          # schémas Pydantic
│   │   ├── models/             # 11 tables ORM
│   │   ├── domain/             # catalogue, KPI, scoring, alertes, reco, simulation
│   │   ├── services/           # analytics (agrégations) + intelligence
│   │   ├── ml/                 # features, train, predictor, anomaly
│   │   └── routers/            # 11 groupes de routes /api/*
│   ├── scripts/
│   │   ├── generate_data.py    # génération de données fictives réalistes + seed
│   │   └── train_models.py     # entraînement des modèles IA
│   ├── sql/schema.sql          # schéma PostgreSQL
│   └── requirements.txt
└── frontend/                   # React + Vite
    └── src/
        ├── pages/              # 8 pages
        ├── components/         # Layout, UI, graphiques (Recharts)
        ├── context/            # logement sélectionné
        ├── api/client.js       # client Axios
        └── lib/format.js
```

**Stack :** React + Vite · FastAPI · PostgreSQL · SQLAlchemy · scikit-learn · pandas · Recharts.

---

## 🗄️ Modèle de données (11 tables)

`users` → `homes` → `rooms` → `equipments`
`consumption_records` (séries 30 min + ventilation par pièce) · `weather_records`
`predictions` · `alerts` · `recommendations` · `kpi_results` · `simulations`

La consommation est stockée en **série temporelle relationnelle** : pas de colonne figée par pièce. Une mesure au niveau logement a `room_id = NULL` ; une ventilation par pièce porte `room_id`.

---

## 🚀 Installation & lancement

### Prérequis
- **Docker** (pour PostgreSQL) · **Python 3.11+** · **Node.js 18+**

### 1) Base de données PostgreSQL

```bash
docker compose up -d db
```
La base `greenscan` est créée automatiquement (utilisateur/mot de passe : `greenscan`).

### 2) Backend (API + IA)

```bash
cd backend
python -m venv .venv
# Windows :
.venv\Scripts\activate
# macOS/Linux :
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env          # (Windows)  /  cp .env.example .env

# Génération des données fictives réalistes (150 jours, 4 logements) :
python -m scripts.generate_data --days 150

# Entraînement des modèles IA :
python -m scripts.train_models

# Lancement de l'API :
uvicorn app.main:app --reload --port 8000
```

➡️ API : http://localhost:8000 · **Docs interactives** : http://localhost:8000/docs

### 3) Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

➡️ Application : **http://localhost:5173**

> **Réseau d'entreprise (proxy SSL).** Si `npm install` échoue avec
> `UNABLE_TO_VERIFY_LEAF_SIGNATURE` (proxy d'entreprise qui ré-signe le HTTPS),
> exécuter une fois : `npm config set strict-ssl false` puis relancer `npm install`.
> Pour revenir à l'état sécurisé : `npm config set strict-ssl true`.
> (Vite démarre en IPv6 `::1` : utiliser **http://localhost:5173**, pas `127.0.0.1`.)

---

## 🔌 API REST (`/api/*`)

| Route | Description |
|---|---|
| `GET /api/dashboard` | Agrégat complet de la page d'accueil |
| `GET /api/homes` · `GET/PATCH /api/homes/{id}` | Logements |
| `GET /api/rooms` | Pièces + consommation + niveau couleur |
| `GET/PATCH /api/equipments` | Équipements |
| `GET /api/consumption?granularity=daily\|weekly\|monthly\|hourly` | Séries |
| `GET /api/kpis` | KPI énergétiques / financiers / écologiques / IA |
| `GET /api/predictions` | Prévisions IA + métriques |
| `GET /api/alerts` · `POST /api/alerts/refresh` | Alertes |
| `GET /api/recommendations` · `POST .../refresh` | Recommandations |
| `GET /api/anomalies` | Anomalies (IsolationForest) |
| `GET /api/simulations/scenarios` · `POST /api/simulations` | Simulations |

Tous les endpoints acceptent `?home_id=` ; sans paramètre, le **premier logement** est utilisé (mode démo).

---

## 🤖 Modèles IA

- **Régression de consommation** : `RandomForestRegressor` (fallback `LinearRegression`).
  Variables : météo (température), jour de semaine, week-end, mois, jour de l'année, historique (lag J-1, J-7, moyenne glissante 7 j).
  Évaluation par split aléatoire 80/20 → **MAE, RMSE, MAPE, R²**. Ré-entraînement final sur tout l'historique.
- **Prévision** : récursive sur 7 jours (les prévisions alimentent les lags), météo future approximée par la moyenne récente (sans API externe).
- **Anomalies** : `IsolationForest` (heure + consommation), fallback z-score.

Les artefacts sont enregistrés dans `backend/ml/artifacts/`.

---

## 🎨 Données de démonstration

4 logements variés sont générés : Studio (Lyon), Appartement (Paris), Maison + solaire + VE (Nantes), Maison passoire thermique DPE F (Lille).
Les données intègrent : cycles saisonnier/journalier, météo, chauffage dépendant de la température et du DPE, production solaire, recharge VE en heures creuses, et **anomalies injectées** (pics nocturnes, surconsommations) pour démontrer la détection.

---

## 📝 Notes

- Sans API météo/Linky réelle : tout repose sur des **données fictives réalistes** (cf. contrainte du cahier des charges).
- Pour réinitialiser : relancer `python -m scripts.generate_data` (drop + recreate) puis `python -m scripts.train_models`.
- Facteurs métier (prix kWh HP/HC, facteur CO₂) configurables dans `.env`.
