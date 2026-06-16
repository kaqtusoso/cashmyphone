type TrackingProperties = Record<string, string | number | boolean | null | undefined>;

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (command: "event", eventName: string, properties?: TrackingProperties) => void;
    fbq?: (command: "trackCustom", eventName: string, properties?: TrackingProperties) => void;
  }
}

const FIRST_TOUCH_KEY = "televera:first-touch";
const LAST_TOUCH_KEY = "televera:last-touch";

const CAMPAIGN_KEYS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_term",
  "utm_content",
  "gclid",
  "fbclid",
  "msclkid",
] as const;

const compactProperties = (properties: TrackingProperties = {}) =>
  Object.fromEntries(Object.entries(properties).filter(([, value]) => value !== undefined && value !== null));

const safeSessionSet = (key: string, value: unknown) => {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage may be unavailable in private browsing or restricted contexts.
  }
};

const safeSessionGet = <T>(key: string): T | null => {
  try {
    const value = sessionStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : null;
  } catch {
    return null;
  }
};

export const persistCampaignParams = (search: string) => {
  const params = new URLSearchParams(search);
  const campaign = CAMPAIGN_KEYS.reduce<TrackingProperties>((acc, key) => {
    const value = params.get(key);
    if (value) acc[key] = value;
    return acc;
  }, {});

  if (!Object.keys(campaign).length) return;

  const payload = {
    ...campaign,
    landing_path: window.location.pathname,
    captured_at: new Date().toISOString(),
  };

  if (!safeSessionGet(FIRST_TOUCH_KEY)) safeSessionSet(FIRST_TOUCH_KEY, payload);
  safeSessionSet(LAST_TOUCH_KEY, payload);
};

export const getCampaignAttribution = () => ({
  first_touch: safeSessionGet<TrackingProperties>(FIRST_TOUCH_KEY),
  last_touch: safeSessionGet<TrackingProperties>(LAST_TOUCH_KEY),
});

const attributionProperties = () => {
  const { first_touch: firstTouch, last_touch: lastTouch } = getCampaignAttribution();
  const props: TrackingProperties = {};

  CAMPAIGN_KEYS.forEach((key) => {
    props[key] = lastTouch?.[key] ?? firstTouch?.[key];
    props[`first_${key}`] = firstTouch?.[key];
    props[`last_${key}`] = lastTouch?.[key];
  });

  props.first_landing_path = firstTouch?.landing_path;
  props.last_landing_path = lastTouch?.landing_path;
  return props;
};

export const trackEvent = (eventName: string, properties: TrackingProperties = {}) => {
  const payload = compactProperties({
    ...attributionProperties(),
    ...properties,
    path: window.location.pathname,
  });

  window.dataLayer?.push({ event: eventName, ...payload });
  window.gtag?.("event", eventName, payload);
  window.fbq?.("trackCustom", eventName, payload);
};

export const trackStepView = (eventName: string, properties: TrackingProperties) => {
  trackEvent(eventName, properties);
};
