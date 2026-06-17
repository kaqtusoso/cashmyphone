export const SITE_URL = "https://televera.se";
export const SITE_NAME = "Televera";
export const DEFAULT_OG_IMAGE = `${SITE_URL}/televera-logo-box.png`;
export const DEFAULT_OG_IMAGE_ALT = "Televera logotyp";

export const absoluteUrl = (path: string) => `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
