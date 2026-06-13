// Client API centralisé. Toutes les requêtes passent par /api (proxifié vers FastAPI).
import axios from "axios";

const api = axios.create({ baseURL: "/api", timeout: 20000 });

// Ajoute automatiquement ?home_id=... si fourni.
const withHome = (homeId, params = {}) =>
  homeId ? { params: { home_id: homeId, ...params } } : { params };

export const Api = {
  // Logements
  listHomes: () => api.get("/homes").then((r) => r.data),
  getHome: (id) => api.get(`/homes/${id}`).then((r) => r.data),
  updateHome: (id, patch) => api.patch(`/homes/${id}`, patch).then((r) => r.data),

  // Dashboard
  dashboard: (homeId) => api.get("/dashboard", withHome(homeId)).then((r) => r.data),

  // Consommation
  consumption: (homeId, granularity = "daily", days) =>
    api.get("/consumption", withHome(homeId, { granularity, ...(days ? { days } : {}) })).then((r) => r.data),

  // Pièces & équipements
  rooms: (homeId, days = 30) => api.get("/rooms", withHome(homeId, { days })).then((r) => r.data),
  equipments: (homeId, roomId) =>
    api.get("/equipments", withHome(homeId, roomId ? { room_id: roomId } : {})).then((r) => r.data),
  updateEquipment: (id, patch) => api.patch(`/equipments/${id}`, patch).then((r) => r.data),

  // KPI & IA
  kpis: (homeId) => api.get("/kpis", withHome(homeId)).then((r) => r.data),
  predictions: (homeId, horizon = 7) =>
    api.get("/predictions", withHome(homeId, { horizon })).then((r) => r.data),
  anomalies: (homeId, days = 30) => api.get("/anomalies", withHome(homeId, { days })).then((r) => r.data),

  // Alertes & recommandations
  alerts: (homeId, level) => api.get("/alerts", withHome(homeId, level ? { level } : {})).then((r) => r.data),
  refreshAlerts: (homeId) => api.post("/alerts/refresh", null, withHome(homeId)).then((r) => r.data),
  resolveAlert: (id) => api.patch(`/alerts/${id}/resolve`).then((r) => r.data),
  recommendations: (homeId) => api.get("/recommendations", withHome(homeId)).then((r) => r.data),
  refreshRecommendations: (homeId) =>
    api.post("/recommendations/refresh", null, withHome(homeId)).then((r) => r.data),

  // Simulations
  scenarios: () => api.get("/simulations/scenarios").then((r) => r.data),
  simulate: (homeId, scenario, params = {}) =>
    api.post("/simulations", { scenario, params }, withHome(homeId)).then((r) => r.data),
};

export default Api;
