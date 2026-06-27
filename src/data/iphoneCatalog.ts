export const iphoneModels = [
  "iPhone 17",
  "iPhone 17 Pro",
  "iPhone 17 Pro Max",
  "iPhone 17e",
  "iPhone Air",
  "iPhone 16",
  "iPhone 16 Plus",
  "iPhone 16 Pro",
  "iPhone 16 Pro Max",
  "iPhone 16e",
  "iPhone 15",
  "iPhone 15 Plus",
  "iPhone 15 Pro",
  "iPhone 15 Pro Max",
  "iPhone 14",
  "iPhone 14 Plus",
  "iPhone 14 Pro",
  "iPhone 14 Pro Max",
  "iPhone 13",
  "iPhone 13 Mini",
  "iPhone 13 Pro",
  "iPhone 13 Pro Max",
  "iPhone 12",
  "iPhone 12 Mini",
  "iPhone 12 Pro",
  "iPhone 12 Pro Max",
  "iPhone 11",
  "iPhone 11 Pro",
  "iPhone 11 Pro Max",
  "iPhone SE 2022",
  "iPhone SE 2020",
  "iPhone XS",
  "iPhone XS Max",
  "iPhone XR",
  "iPhone X",
  "iPhone 8",
  "iPhone 8 Plus",
  "iPhone 7",
  "iPhone 7 Plus",
];

export const storageOptions = ["32GB", "64GB", "128GB", "256GB", "512GB", "1TB", "2TB"];

export const storageByModel: Record<string, string[]> = {
  "iPhone 17e": ["256GB", "512GB"],
  "iPhone Air": ["256GB", "512GB", "1TB"],

  "iPhone 17 Pro Max": ["256GB", "512GB", "1TB", "2TB"],
  "iPhone 17 Pro": ["256GB", "512GB", "1TB"],
  "iPhone 17": ["256GB", "512GB"],

  "iPhone 16e": ["128GB", "256GB", "512GB"],
  "iPhone 16 Pro Max": ["256GB", "512GB", "1TB"],
  "iPhone 16 Pro": ["128GB", "256GB", "512GB", "1TB"],
  "iPhone 16 Plus": ["128GB", "256GB", "512GB"],
  "iPhone 16": ["128GB", "256GB", "512GB"],

  "iPhone 15 Pro Max": ["256GB", "512GB", "1TB"],
  "iPhone 15 Pro": ["128GB", "256GB", "512GB", "1TB"],
  "iPhone 15 Plus": ["128GB", "256GB", "512GB"],
  "iPhone 15": ["128GB", "256GB", "512GB"],

  "iPhone 14 Pro Max": ["128GB", "256GB", "512GB", "1TB"],
  "iPhone 14 Pro": ["128GB", "256GB", "512GB", "1TB"],
  "iPhone 14 Plus": ["128GB", "256GB", "512GB"],
  "iPhone 14": ["128GB", "256GB", "512GB"],

  "iPhone 13 Pro Max": ["128GB", "256GB", "512GB", "1TB"],
  "iPhone 13 Pro": ["128GB", "256GB", "512GB", "1TB"],
  "iPhone 13": ["128GB", "256GB", "512GB"],
  "iPhone 13 Mini": ["128GB", "256GB", "512GB"],

  "iPhone 12 Pro Max": ["128GB", "256GB", "512GB"],
  "iPhone 12 Pro": ["128GB", "256GB", "512GB"],
  "iPhone 12": ["64GB", "128GB", "256GB"],
  "iPhone 12 Mini": ["64GB", "128GB", "256GB"],

  "iPhone 11 Pro Max": ["64GB", "256GB", "512GB"],
  "iPhone 11 Pro": ["64GB", "256GB", "512GB"],
  "iPhone 11": ["64GB", "128GB", "256GB"],

  "iPhone SE 2022": ["64GB", "128GB", "256GB"],
  "iPhone SE 2020": ["64GB", "128GB", "256GB"],

  "iPhone XS Max": ["64GB", "256GB", "512GB"],
  "iPhone XS": ["64GB", "256GB", "512GB"],
  "iPhone XR": ["64GB", "128GB", "256GB"],
  "iPhone X": ["64GB", "256GB"],
  "iPhone 8 Plus": ["64GB", "128GB", "256GB"],
  "iPhone 8": ["64GB", "128GB", "256GB"],
  "iPhone 7 Plus": ["32GB", "128GB", "256GB"],
  "iPhone 7": ["32GB", "128GB", "256GB"],
};

const referenceBaseModelPrice: Record<string, number> = {
  "iPhone 17e": 5400,
  "iPhone Air": 10500,

  "iPhone 17 Pro Max": 14500,
  "iPhone 17 Pro": 12500,
  "iPhone 17": 9500,

  "iPhone 16e": 5200,
  "iPhone 16 Pro Max": 12500,
  "iPhone 16 Pro": 10800,
  "iPhone 16 Plus": 8500,
  "iPhone 16": 7500,

  "iPhone 15 Pro Max": 10500,
  "iPhone 15 Pro": 9000,
  "iPhone 15 Plus": 7000,
  "iPhone 15": 6000,

  "iPhone 14 Pro Max": 8500,
  "iPhone 14 Pro": 7000,
  "iPhone 14 Plus": 5500,
  "iPhone 14": 4800,

  "iPhone 13 Pro Max": 6500,
  "iPhone 13 Pro": 5500,
  "iPhone 13 Mini": 3600,
  "iPhone 13": 4200,

  "iPhone 12 Pro Max": 4800,
  "iPhone 12 Pro": 4000,
  "iPhone 12 Mini": 2700,
  "iPhone 12": 3200,

  "iPhone 11 Pro Max": 3600,
  "iPhone 11 Pro": 3000,
  "iPhone 11": 2400,

  "iPhone SE 2022": 1800,
  "iPhone SE 2020": 1200,
  "iPhone XS Max": 2300,
  "iPhone XS": 1900,
  "iPhone XR": 1700,
  "iPhone X": 1600,
  "iPhone 8 Plus": 1200,
  "iPhone 8": 900,
  "iPhone 7 Plus": 800,
  "iPhone 7": 600,
};

const storageMultiplier: Record<string, number> = {
  "32GB": 0.9,
  "64GB": 1.0,
  "128GB": 1.05,
  "256GB": 1.15,
  "512GB": 1.3,
  "1TB": 1.45,
  "2TB": 1.65,
};

export const getReferenceBasePrice = (model: string, storage: string): number => {
  const base = referenceBaseModelPrice[model] ?? 2000;
  const multiplier = storageMultiplier[storage] ?? 1;
  return Math.round(base * multiplier);
};

export const conditionOptions = [
  { value: "Nyskick", label: "Nyskick", description: "ser ut som ny, inga repor" },
  { value: "Bra skick", label: "Bra skick", description: "små repor, inga sprickor" },
  { value: "Okej skick", label: "Okej skick", description: "märkbara repor eller små sprickor" },
  { value: "Trasig", label: "Trasig", description: "ej fullt fungerande" },
];
