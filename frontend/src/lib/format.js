// Helpers de formatage (FR).
export const fmt = (n, d = 1) =>
  n == null || isNaN(n) ? "—" : Number(n).toLocaleString("fr-FR", { maximumFractionDigits: d, minimumFractionDigits: 0 });

export const eur = (n, d = 2) => `${fmt(n, d)} €`;
export const kwh = (n, d = 1) => `${fmt(n, d)} kWh`;

// Date courte "12 juin" depuis une chaîne ISO/date.
export const shortDate = (s) => {
  const dt = new Date(s);
  if (isNaN(dt)) return s;
  return dt.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
};

export const dateTime = (s) =>
  new Date(s).toLocaleString("fr-FR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

// Couleur associée à un niveau de pièce / d'alerte.
export const levelColor = { vert: "#10b981", orange: "#f59e0b", rouge: "#ef4444" };
