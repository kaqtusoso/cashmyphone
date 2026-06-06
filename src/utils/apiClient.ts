const PRODUCTION_API_URL = "https://cashmyphone-production.up.railway.app";

export const API_URL = import.meta.env.VITE_API_URL ?? PRODUCTION_API_URL;
