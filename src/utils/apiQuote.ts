/**
 * apiQuote.ts
 *
 * Anropar Televera backend (/api/quote) och mappar svaret till
 * CompanyOffer[] som resten av appen förväntar sig.
 */
import { ConditionAnswers, WearLevel, WearLevelWithCrack } from "@/types/condition";
import { CompanyOffer } from "@/types/offers";
import { API_URL } from "@/utils/apiClient";

// ─── Displayinfo per återförsäljare ──────────────────────────────────────────

const RETAILER_INFO: Record<
  string,
  {
    name: string;
    leverans: string;
    utbetalningstid: string;
    trustpilotScore: string;
    trustpilotReviews: string;
    trustpilotUrl: string;
    paymentMethods: string[];
  }
> = {
  swappie: {
    name: "Swappie",
    leverans: "Gratis försäljningspaket",
    utbetalningstid: "3-6 bankdagar",
    trustpilotScore: "4.4",
    trustpilotReviews: "65 045",
    trustpilotUrl: "https://se.trustpilot.com/review/swappie.com",
    paymentMethods: ["PayPal", "Banköverföring"],
  },
  phonehero: {
    name: "PhoneHero",
    leverans: "Digital fraktsedel",
    utbetalningstid: "2-4 bankdagar",
    trustpilotScore: "4.7",
    trustpilotReviews: "13 815",
    trustpilotUrl: "https://se.trustpilot.com/review/phonehero.se",
    paymentMethods: ["Swish", "Banköverföring"],
  },
  telestore: {
    name: "Telestore",
    leverans: "Digital fraktsedel",
    utbetalningstid: "1-3 bankdagar",
    trustpilotScore: "4.7",
    trustpilotReviews: "1 753",
    trustpilotUrl: "https://se.trustpilot.com/review/telestore.se",
    paymentMethods: ["Swish", "Banköverföring"],
  },
  fixmyphone: {
    name: "FixMyPhone",
    leverans: "Gratis försäljningspaket",
    utbetalningstid: "2-4 bankdagar",
    trustpilotScore: "3.1",
    trustpilotReviews: "1 385",
    trustpilotUrl: "https://se.trustpilot.com/review/fixmyphone.se",
    paymentMethods: ["Swish", "Banköverföring"],
  },
  happyphone: {
    name: "HappyPhone",
    leverans: "Gratis försäljningspaket",
    utbetalningstid: "2-4 bankdagar",
    trustpilotScore: "2.2",
    trustpilotReviews: "42",
    trustpilotUrl: "https://se.trustpilot.com/review/happyphone.se",
    paymentMethods: ["Swish", "Banköverföring"],
  },
  renewed: {
    name: "ReNewed",
    leverans: "Digital fraktsedel",
    utbetalningstid: "2-4 bankdagar",
    trustpilotScore: "4.1",
    trustpilotReviews: "32",
    trustpilotUrl: "https://se.trustpilot.com/review/renewed.se",
    paymentMethods: ["Banköverföring"],
  },
  fixiphone: {
    name: "FixiPhone",
    leverans: "Digital fraktsedel / butik",
    utbetalningstid: "2-4 bankdagar",
    trustpilotScore: "3.9",
    trustpilotReviews: "168",
    trustpilotUrl: "https://se.trustpilot.com/review/fixiphone.se",
    paymentMethods: ["Banköverföring"],
  },
  fixphonepro: {
    name: "FixTech",
    leverans: "Digital fraktsedel / butik",
    utbetalningstid: "2-4 bankdagar",
    trustpilotScore: "4.0",
    trustpilotReviews: "3",
    trustpilotUrl: "https://se.trustpilot.com/review/fixtech.se",
    paymentMethods: ["Swish", "Banköverföring"],
  },
};

// ─── Hjälpare: yta → surface-nyckel ──────────────────────────────────────────

const SURFACE_RANK: Record<string, number> = {
  LIKE_NEW: 0,
  ALMOST_NEW: 1,
  GOOD: 2,
  MODERATE: 3,
};

const worstSurface = (a: string, b: string) => (SURFACE_RANK[a] >= SURFACE_RANK[b] ? a : b);

const wearToSurface = (w: WearLevelWithCrack | WearLevel | null): string => {
  switch (w) {
    case "none":
    case "minimal":
      return "LIKE_NEW";
    case "some":
      return "ALMOST_NEW";
    case "visible":
      return "GOOD";
    case "cracked":
      return "MODERATE";
    default:
      return "LIKE_NEW";
  }
};

// ─── Lagring → GB ────────────────────────────────────────────────────────────

const storageToGb = (s: string): number => {
  const normalized = s.toUpperCase().replace(/\s/g, "");

  if (normalized === "1TB") return 1024;
  if (normalized === "2TB") return 2048;

  return parseInt(normalized, 10);
};

// ─── Datum/tid från backend ──────────────────────────────────────────────────

const SCRAPE_DISPLAY_HOURS = [0, 6, 12, 18];

const stockholmDateParts = (date: Date) => {
  const parts = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Europe/Stockholm",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);

  const value = (type: Intl.DateTimeFormatPartTypes) => parts.find((part) => part.type === type)?.value ?? "";

  return {
    year: Number(value("year")),
    month: Number(value("month")),
    day: Number(value("day")),
    hour: Number(value("hour")),
    minute: Number(value("minute")),
  };
};

const scheduledScrapeDisplayTime = (date: Date): string => {
  const parts = stockholmDateParts(date);
  const current = Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute);

  const nearest = SCRAPE_DISPLAY_HOURS.flatMap((hour) => [
    Date.UTC(parts.year, parts.month - 1, parts.day - 1, hour, 0),
    Date.UTC(parts.year, parts.month - 1, parts.day, hour, 0),
    Date.UTC(parts.year, parts.month - 1, parts.day + 1, hour, 0),
  ]).reduce((best, candidate) => (
    Math.abs(candidate - current) < Math.abs(best - current) ? candidate : best
  ));

  const snapped = new Date(nearest);
  const pad = (value: number) => String(value).padStart(2, "0");

  return [
    snapped.getUTCFullYear(),
    pad(snapped.getUTCMonth() + 1),
    pad(snapped.getUTCDate()),
  ].join("-") + ` ${pad(snapped.getUTCHours())}:00`;
};

const formatUpdatedAt = (value?: string | null): string => {
  if (!value) return "";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "";

  return scheduledScrapeDisplayTime(date);
};

// ─── Bygg QuoteRequest från frontend-svar ────────────────────────────────────

const buildPayload = (model: string, storage: string, a: ConditionAnswers) => {
  const f = a.functional;
  const sf = a.screenFunction;

  const isBroken =
    f.powersOn === false ||
    f.network === false ||
    f.faceId === false ||
    f.selfieCamera === false ||
    f.speaker === false ||
    f.chargingOrButtons === false ||
    f.other === false;

  const isWaterDamaged = f.bentOrWaterDamaged === true || a.critical?.bent === true || a.critical?.waterDamaged === true;
  const isScreenBroken = !sf.allWorks && (sf.brightSpots || sf.deadPixels || sf.linesOrBurnIn || sf.touchIssue);
  const isGlassBroken = a.screenGlass === "chipped" || a.screenGlass === "scratched";
  const isFrameBroken = a.sidesWear === "cracked" || a.backWear === "cracked";
  const isBackCameraBroken = f.rearCamera === false;
  const isBatteryLow = a.batteryHealth !== null && a.batteryHealth < 85;

  const screenSurface = wearToSurface(a.screenWear);

  return {
    model,
    storage_gb: storageToGb(storage),
    battery_health_percent: a.batteryHealth,
    screen_surface: screenSurface,
    sides_surface: wearToSurface(a.sidesWear),
    back_surface: wearToSurface(a.backWear),
    is_broken: isBroken,
    is_screen_broken: isScreenBroken,
    is_glass_broken: isGlassBroken,
    is_frame_broken: isFrameBroken,
    is_back_camera_broken: isBackCameraBroken,
    is_battery_low: isBatteryLow,
    is_water_damaged: isWaterDamaged,
  };
};

// ─── Huvudfunktion ───────────────────────────────────────────────────────────

export const fetchQuotes = async (
  model: string,
  storage: string,
  answers: ConditionAnswers,
): Promise<CompanyOffer[]> => {
  const payload = buildPayload(model, storage, answers);

  const resp = await fetch(`${API_URL}/api/quote`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    throw new Error(`API-fel: ${resp.status}`);
  }

  const data = await resp.json();
  const updatedAt = formatUpdatedAt(data.prices_updated_at);

  return (
    data.quotes as {
      retailer: string;
      condition_key: string;
      price_sek: number;
      url: string | null;
      scraped_at?: string;
    }[]
  ).map((q) => {
    const info = RETAILER_INFO[q.retailer] ?? {
      name: q.retailer,
      leverans: "—",
      utbetalningstid: "—",
      trustpilotScore: "",
      trustpilotReviews: "",
      trustpilotUrl: "",
      paymentMethods: ["Banköverföring"],
    };

    return {
      företag: info.name,
      modell: model,
      lagring: storage,
      skick: q.condition_key,
      pris: q.price_sek,
      url: q.url ?? "#",
      leverans: info.leverans,
      utbetalningstid: info.utbetalningstid,
      uppdaterad: updatedAt,
      notPurchased: false,
      trustpilotScore: info.trustpilotScore,
      trustpilotReviews: info.trustpilotReviews,
      trustpilotUrl: info.trustpilotUrl,
      paymentMethods: info.paymentMethods,
    } satisfies CompanyOffer;
  });
};
