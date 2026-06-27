type HeroModule = Record<string, string>;

export interface IphoneColorOption {
  value: string;
  label: string;
  image: string;
  swatch: string;
}

const heroModules = import.meta.glob("/src/assets/phonehero_heroes/*.png", {
  eager: true,
  query: "?url",
  import: "default",
}) as HeroModule;

const modelHeroKeys: Record<string, string> = {
  "iPhone 17e": "iphone_17e",
  "iPhone Air": "iphone_air",
  "iPhone 17 Pro Max": "iphone_17_pro_max",
  "iPhone 17 Pro": "iphone_17_pro",
  "iPhone 17": "iphone_17",
  "iPhone 16e": "iphone_16e",
  "iPhone 16 Pro Max": "iphone_16_pro_max",
  "iPhone 16 Pro": "iphone_16_pro",
  "iPhone 16 Plus": "iphone_16_plus",
  "iPhone 16": "iphone_16",
  "iPhone 15 Pro Max": "iphone_15_pro_max",
  "iPhone 15 Pro": "iphone_15_pro",
  "iPhone 15 Plus": "iphone_15_plus",
  "iPhone 15": "iphone_15",
  "iPhone 14 Pro Max": "iphone_14_pro_max",
  "iPhone 14 Pro": "iphone_14_pro",
  "iPhone 14 Plus": "iphone_14_plus",
  "iPhone 14": "iphone_14",
  "iPhone 13 Pro Max": "iphone_13_pro_max",
  "iPhone 13 Pro": "iphone_13_pro",
  "iPhone 13 mini": "iphone_13_mini",
  "iPhone 13 Mini": "iphone_13_mini",
  "iPhone 13": "iphone_13",
  "iPhone 12 Pro Max": "iphone_12_pro_max",
  "iPhone 12 Pro": "iphone_12_pro",
  "iPhone 12 mini": "iphone_12_mini",
  "iPhone 12 Mini": "iphone_12_mini",
  "iPhone 12": "iphone_12",
  "iPhone 11 Pro Max": "iphone_11_pro_max",
  "iPhone 11 Pro": "iphone_11_pro",
  "iPhone 11": "iphone_11",
  "iPhone SE 2022": "iphone_11",
  "iPhone SE 2020": "iphone_11",
};

const colorLabels: Record<string, string> = {
  black: "Svart",
  black_titanium: "Svart titan",
  blue: "Blå",
  blue_titanium: "Blå titan",
  cloud_white: "Molnvit",
  cosmic_orange: "Cosmic Orange",
  deep_blue: "Deep Blue",
  deep_purple: "Deep Purple",
  desert_titanium: "Desert Titanium",
  gold: "Guld",
  graphite: "Grafit",
  green: "Grön",
  lavender: "Lavendel",
  light_gold: "Ljust guld",
  midnight: "Midnatt",
  midnight_green: "Midnattsgrön",
  mist_blue: "Mist Blue",
  natural_titanium: "Natural Titanium",
  pacific_blue: "Pacific Blue",
  pink: "Rosa",
  purple: "Lila",
  red: "Röd",
  sage: "Sage",
  sierra_blue: "Sierra Blue",
  silver: "Silver",
  sky_blue: "Sky Blue",
  soft_pink: "Soft Pink",
  space_black: "Space Black",
  space_grey: "Rymdgrå",
  starlight: "Stjärnglans",
  teal: "Teal",
  ultramarine: "Ultramarine",
  white: "Vit",
  white_titanium: "Vit titan",
  yellow: "Gul",
};

const swatches: Record<string, string> = {
  black: "#171717",
  black_titanium: "#2e2c29",
  blue: "#8fb4d8",
  blue_titanium: "#4f6478",
  cloud_white: "#f3f4ef",
  cosmic_orange: "#d86626",
  deep_blue: "#27364f",
  deep_purple: "#5d5369",
  desert_titanium: "#c8a47e",
  gold: "#f2d7a3",
  graphite: "#5c5a55",
  green: "#9fb8a3",
  lavender: "#c8b6dc",
  light_gold: "#ead6a9",
  midnight: "#242a31",
  midnight_green: "#4e5d55",
  mist_blue: "#c7d9e9",
  natural_titanium: "#b8b1a8",
  pacific_blue: "#3d6176",
  pink: "#f4b8c6",
  purple: "#b7a7d6",
  red: "#c91f2f",
  sage: "#9caf9b",
  sierra_blue: "#9bb2c8",
  silver: "#e4e4df",
  sky_blue: "#b9d7ee",
  soft_pink: "#efbdc7",
  space_black: "#232323",
  space_grey: "#60605c",
  starlight: "#f0eadf",
  teal: "#5ba6a5",
  ultramarine: "#5b70d6",
  white: "#f7f6ef",
  white_titanium: "#eeeae1",
  yellow: "#f2dc7a",
};

const neutralPreference = [
  "black",
  "space_black",
  "black_titanium",
  "graphite",
  "space_grey",
  "midnight",
  "natural_titanium",
  "deep_blue",
  "blue",
];

const titleCase = (value: string) =>
  value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const heroKeyForModel = (model: string) => modelHeroKeys[model] ?? "iphone_15";

const parseHeroPath = (path: string) => {
  const file = path.split("/").pop()?.replace(/\.png$/, "") ?? "";
  const [modelKey, color] = file.split("__");
  if (!modelKey || !color) return null;
  return { modelKey, color };
};

const colorOptionsByModel = Object.entries(heroModules).reduce<Record<string, IphoneColorOption[]>>((acc, [path, image]) => {
  const parsed = parseHeroPath(path);
  if (!parsed) return acc;
  acc[parsed.modelKey] ??= [];
  acc[parsed.modelKey].push({
    value: parsed.color,
    label: colorLabels[parsed.color] ?? titleCase(parsed.color),
    image,
    swatch: swatches[parsed.color] ?? "#d8d5cb",
  });
  return acc;
}, {});

Object.values(colorOptionsByModel).forEach((options) => {
  options.sort((a, b) => a.label.localeCompare(b.label, "sv-SE"));
});

export const getIphoneColorOptions = (model: string): IphoneColorOption[] => {
  const options = colorOptionsByModel[heroKeyForModel(model)];
  return options?.length ? options : colorOptionsByModel.iphone_15 ?? [];
};

export const getDefaultIphoneColor = (model: string) => {
  const options = getIphoneColorOptions(model);
  return neutralPreference.find((color) => options.some((option) => option.value === color)) ?? options[0]?.value ?? "";
};

export const getIphoneImage = (model: string, color?: string) => {
  const options = getIphoneColorOptions(model);
  const selectedColor = color || getDefaultIphoneColor(model);
  return options.find((option) => option.value === selectedColor)?.image ?? options[0]?.image ?? "";
};
