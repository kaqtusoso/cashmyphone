import { ConditionAnswers, ScreenGlass, WearLevel, WearLevelWithCrack } from "@/types/condition";
import { getReferenceBasePrice } from "@/data/iphoneCatalog";
import { CompanyOffer } from "@/types/offers";

// =====================================================
// Helpers
// =====================================================

const wearScore = (w: WearLevelWithCrack): number => {
  switch (w) {
    case "cracked":
      return 5;
    case "visible":
      return 4;
    case "some":
      return 3;
    case "minimal":
      return 2;
    case "none":
    default:
      return 1;
  }
};

const worstWear = (...levels: WearLevelWithCrack[]): WearLevelWithCrack => {
  return levels.reduce((worst, l) => (wearScore(l) > wearScore(worst) ? l : worst), "none");
};

// Count failed functional checks (excluding the bent/water question, which is special)
// A `null` answer is treated as OK (no issue) — UI guarantees all answers exist
// before pricing is computed.
const countFunctionalIssues = (a: ConditionAnswers): number => {
  const f = a.functional;
  let n = 0;
  if (f.powersOn === false) n++;
  if (f.network === false) n++;
  if (f.faceId === false) n++;
  if (f.selfieCamera === false) n++;
  if (f.speaker === false) n++;
  return n;
};

const hasScreenIssues = (a: ConditionAnswers): boolean => {
  const s = a.screenFunction;
  return !s.allWorks && (s.brightSpots || s.deadPixels || s.linesOrBurnIn);
};

const battery = (a: ConditionAnswers): number => a.batteryHealth ?? 100;
const glass = (a: ConditionAnswers): ScreenGlass => a.screenGlass ?? "none";
const screenWearOf = (a: ConditionAnswers): WearLevel => a.screenWear ?? "none";
const sidesOf = (a: ConditionAnswers): WearLevelWithCrack => a.sidesWear ?? "none";
const backOf = (a: ConditionAnswers): WearLevelWithCrack => a.backWear ?? "none";

// =====================================================
// Generic dealer pricing
// =====================================================

interface DealerSpec {
  name: string;
  multiplier: number; // baseline appetite vs. reference
  leverans: string;
  utbetalningstid: string;
  url: string;
  // Some dealers refuse if phone is bent/water-damaged
  refuseOnBentOrWater?: boolean;
}

const generalDealers: DealerSpec[] = [
  {
    name: "Swappie",
    multiplier: 1.0,
    leverans: "Gratis försäljningspaket",
    utbetalningstid: "3-6 bankdagar",
    url: "https://swappie.com/se",
  },
  {
    name: "FixMyPhone",
    multiplier: 0.96,
    leverans: "Gratis försäljningspaket",
    utbetalningstid: "2-4 bankdagar",
    url: "https://www.fixmyphone.se",
  },
  {
    name: "HappyPhone",
    multiplier: 0.93,
    leverans: "Gratis försäljningspaket",
    utbetalningstid: "2-4 bankdagar",
    url: "https://www.happyphone.se",
  },
  {
    name: "Renewed",
    multiplier: 0.9,
    leverans: "Digital fraktsedel",
    utbetalningstid: "2-4 bankdagar",
    url: "https://renewed.se",
  },
  {
    name: "CleverBuy",
    multiplier: 0.87,
    leverans: "Digital fraktsedel",
    utbetalningstid: "2-4 bankdagar",
    url: "https://cleverbuy.se",
    refuseOnBentOrWater: true,
  },
];

const computeGeneralFactor = (a: ConditionAnswers): number => {
  let f = 1.0;
  const bh = battery(a);

  // Battery health
  if (bh >= 95) f -= 0;
  else if (bh >= 90) f -= 0.03;
  else if (bh >= 85) f -= 0.06;
  else if (bh >= 80) f -= 0.1;
  else if (bh >= 70) f -= 0.18;
  else f -= 0.28;

  // Functional issues (excl. bent/water)
  const issues = countFunctionalIssues(a);
  f -= issues * 0.12;

  // Screen function
  if (hasScreenIssues(a)) f -= 0.15;

  // Screen glass
  const g = glass(a);
  if (g === "scratched") f -= 0.08;
  if (g === "chipped") f -= 0.25;

  // Screen wear
  switch (screenWearOf(a)) {
    case "visible":
      f -= 0.12;
      break;
    case "some":
      f -= 0.06;
      break;
    case "minimal":
      f -= 0.02;
      break;
  }

  // Sides
  switch (sidesOf(a)) {
    case "cracked":
      f -= 0.2;
      break;
    case "visible":
      f -= 0.1;
      break;
    case "some":
      f -= 0.04;
      break;
    case "minimal":
      f -= 0.01;
      break;
  }

  // Back
  switch (backOf(a)) {
    case "cracked":
      f -= 0.2;
      break;
    case "visible":
      f -= 0.1;
      break;
    case "some":
      f -= 0.04;
      break;
    case "minimal":
      f -= 0.01;
      break;
  }

  return Math.max(0.05, f);
};

// =====================================================
// Telestore-specific mapping (per spec)
// =====================================================

type TelestoreCondition =
  | "nyskick"
  | "utmarkt"
  | "bra"
  | "okej"
  | "sprickor_fram";

const telestoreConditionMultiplier: Record<TelestoreCondition, number> = {
  nyskick: 1.0,
  utmarkt: 0.92,
  bra: 0.8,
  okej: 0.65,
  sprickor_fram: 0.4,
};

interface TelestoreResult {
  notPurchased: boolean;
  price: number;
  conditionKey: string;
}

export const computeTelestore = (model: string, storage: string, a: ConditionAnswers): TelestoreResult => {
  // Refuse if bent or water-damaged
  if (a.functional.bentOrWaterDamaged === true) {
    return { notPurchased: true, price: 0, conditionKey: "köper_ej" };
  }

  // Any other functional issue → minimum bid 60 kr
  if (countFunctionalIssues(a) > 0) {
    return { notPurchased: false, price: 60, conditionKey: "minimum" };
  }

  // Determine main condition key
  const g = glass(a);
  const screenBroken = g !== "none" || hasScreenIssues(a);
  let baseKey: TelestoreCondition;

  if (screenBroken) {
    baseKey = "sprickor_fram";
  } else {
    const sides = sidesOf(a);
    const back = backOf(a);
    const filteredSides: WearLevel = sides === "cracked" ? "visible" : sides;
    const filteredBack: WearLevel = back === "cracked" ? "visible" : back;
    const worst = worstWear(screenWearOf(a), filteredSides, filteredBack);
    switch (worst) {
      case "visible":
        baseKey = "okej";
        break;
      case "some":
        baseKey = "bra";
        break;
      case "minimal":
        baseKey = "utmarkt";
        break;
      case "none":
      default:
        baseKey = "nyskick";
        break;
    }
  }

  let multiplier = telestoreConditionMultiplier[baseKey];
  let key: string = baseKey;

  // :sidor suffix if sides or back are cracked
  if (sidesOf(a) === "cracked" || backOf(a) === "cracked") {
    multiplier -= 0.1;
    key += ":sidor";
  }

  // :bat suffix if battery < 85%
  if (battery(a) < 85) {
    multiplier -= 0.05;
    key += ":bat";
  }

  multiplier = Math.max(0.05, multiplier);
  const price = Math.round(getReferenceBasePrice(model, storage) * 0.92 * multiplier);

  return { notPurchased: false, price: Math.max(60, price), conditionKey: key };
};

// =====================================================
// Public: compute all dealer offers
// =====================================================

export const computeOffers = (model: string, storage: string, a: ConditionAnswers): CompanyOffer[] => {
  const today = new Date().toLocaleDateString("sv-SE");
  const base = getReferenceBasePrice(model, storage);
  const generalFactor = computeGeneralFactor(a);

  const offers: CompanyOffer[] = generalDealers.map((d) => {
    const refuses = !!(d.refuseOnBentOrWater && a.functional.bentOrWaterDamaged === true);
    const price = refuses ? 0 : Math.round(base * d.multiplier * generalFactor);
    return {
      företag: d.name,
      modell: model,
      lagring: storage,
      skick: "Beräknat skick",
      pris: price,
      url: d.url,
      leverans: d.leverans,
      utbetalningstid: d.utbetalningstid,
      uppdaterad: today,
      notPurchased: refuses,
    };
  });

  // Telestore (special logic)
  const tele = computeTelestore(model, storage, a);
  offers.push({
    företag: "Telestore",
    modell: model,
    lagring: storage,
    skick: tele.conditionKey,
    pris: tele.price,
    url: "https://telestore.se",
    leverans: "Digital fraktsedel",
    utbetalningstid: "1-3 bankdagar",
    uppdaterad: today,
    notPurchased: tele.notPurchased,
  });

  return offers;
};

// =====================================================
// Backwards-compat: small summary used by SavedOffersPanel
// =====================================================

export interface ConditionSummary {
  condition: string;
  battery: number;
  cracks: boolean;
  waterDamage: boolean;
}

export const getConditionSummary = (a: ConditionAnswers): ConditionSummary => {
  const cracks =
    a.screenGlass === "chipped" || a.sidesWear === "cracked" || a.backWear === "cracked";
  const waterDamage = a.functional.bentOrWaterDamaged === true;

  const worst = worstWear(screenWearOf(a), sidesOf(a), backOf(a));
  let label = "Som ny";
  if (cracks || worst === "cracked" || worst === "visible") label = "Okej";
  else if (worst === "some") label = "Bra";
  else if (worst === "minimal") label = "Mycket bra";

  return {
    condition: label,
    battery: a.batteryHealth ?? 0,
    cracks,
    waterDamage,
  };
};
