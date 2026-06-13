// Contexte global : liste des logements + logement sélectionné (partagé par toutes les pages).
import { createContext, useContext, useEffect, useState } from "react";
import Api from "../api/client";

const HomeContext = createContext(null);

export function HomeProvider({ children }) {
  const [homes, setHomes] = useState([]);
  const [homeId, setHomeId] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Api.listHomes()
      .then((data) => {
        setHomes(data);
        if (data.length) setHomeId(data[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  const currentHome = homes.find((h) => h.id === homeId) || null;

  return (
    <HomeContext.Provider value={{ homes, homeId, setHomeId, currentHome, loading }}>
      {children}
    </HomeContext.Provider>
  );
}

export const useHome = () => useContext(HomeContext);
