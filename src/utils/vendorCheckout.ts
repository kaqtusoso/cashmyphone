import type { PaymentMethod } from "@/utils/checkoutValidation";

export type PersonalNumberRequirement = "never" | "swish" | "always";

export type ShippingOption = {
  id: string;
  label: string;
  description?: string;
  bullets?: string[];
  features?: string[];
  feeSek?: number;
  feeLabel?: string;
  stores?: string[];
};

export type PaymentOption = {
  id: PaymentMethod | "bank-iban";
  label: string;
  requiresBankDetails: boolean;
};

export type DealerConfig = {
  name: string;
  shippingOptions: ShippingOption[];
  paymentOptions: PaymentOption[];
  personalNumberRequirement: PersonalNumberRequirement;
};

const fixMyPhoneStores = [
  "Hemvägen 19, Alingsås",
  "Stora Brogatan 14, Borås",
  "Valbovägen 307-309, Valbo",
  "Östra Hamngatan, Göteborg",
  "Frölunda torg 2, Västra Frölunda",
  "Kyrktorget 19-21, Partille",
  "Prästvägen 1, Halmstad",
  "Väla Centrum, Ödåkra",
  "Älvebacken 31, Kungälv",
  "Borgmästaregatan 5, Kungsbacka",
  "Storgatan 28, Linköping",
  "Jerikodalsgatan 3, Mjölby",
  "Koppargatan 20, Norrköping",
  "Västerleden, Örebro",
  "Köpmannagatan 3, Skövde",
  "Golfvägen 4, Danderyd",
  "Hamngatan 37, Stockholm",
  "Hanstavägen 55F, Kista",
  "Kungsgatan 35, Stockholm",
  "Forumvägen 12, Nacka",
  "Sollentunavägen 163C, Sollentuna",
  "Stora Marknadsvägen 15, Täby",
  "Gesällvägen 1, Sundsvall",
  "Ladugårdsvägen 14, Trollhättan",
  "Torp, Uddevalla",
  "Marknadsgatan 3, Umeå",
  "Svartbäcksgatan 7-11, Uppsala",
  "Mörners väg 122, Växjö",
];

const fixiphoneStores = [
  "Nygatan 37, Gävle",
  "Hantverkargatan 9, Västerås",
  "Kungsgatan 24, Eskilstuna",
  "Kungsgatan 53, Umeå",
  "Filbytergallerian, Linköping",
  "Kungsgatan 59, Uppsala",
  "Storgatan 50E, Luleå",
  "Storgatan 20E, Örnsköldsvik",
  "Nygatan 51, Skellefteå",
  "Nygatan 93, Norrköping",
  "Storgatan 23, Sundsvall",
  "Östra Storgatan 14, Jönköping",
  "Lilla Fiskaregatan 8A, Lund",
  "Drottninggatan 69, Göteborg",
];

const storeOption = (id: string, label: string, stores: string[]): ShippingOption => ({
  id,
  label,
  description: stores.length === 1 ? stores[0] : `${stores.length} butiker`,
  features: ["Lämna in mobilen själv", "Ingen frakt behövs", "Gratis"],
  stores,
});

export const dealerConfig: Record<string, DealerConfig> = {
  swappie: {
    name: "Swappie",
    personalNumberRequirement: "never",
    shippingOptions: [
      {
        id: "sales-package",
        label: "Försäljningspaket",
        description: "Levereras hem till dig inom 3-5 arbetsdagar",
        features: ["Paket skickas hem", "Fraktinstruktioner ingår", "Gratis"],
      },
      {
        id: "email-label",
        label: "Fraktetikett via e-post",
        description: "Gratis",
        features: ["Fraktsedel skickas via e-post", "Skriv ut och fäst på paketet", "Lämna hos ombud"],
      },
    ],
    paymentOptions: [
      { id: "paypal", label: "PayPal", requiresBankDetails: false },
      { id: "bank", label: "Banköverföring", requiresBankDetails: true },
    ],
  },
  fixphonepro: {
    name: "FixTech",
    personalNumberRequirement: "never",
    shippingOptions: [
      {
        id: "email-label",
        label: "Fraktetikett via e-post",
        description: "Gratis",
        features: ["Fraktsedel skickas via e-post", "Följ instruktionerna i mejlet", "Gratis"],
      },
      storeOption("store-dropoff", "Inlämning via butik", ["Hantverkargatan 2B, Västerås"]),
    ],
    paymentOptions: [{ id: "bank", label: "Banköverföring", requiresBankDetails: true }],
  },
  phonehero: {
    name: "PhoneHero",
    personalNumberRequirement: "swish",
    shippingOptions: [
      {
        id: "email-label",
        label: "Fraktetikett via e-post",
        description: "Gratis",
        features: ["QR-kod skickas via e-post", "Visa koden hos PostNord", "Ombudet skriver ut etiketten"],
      },
      storeOption("store-dropoff", "Inlämning via butik", [
        "Sankt Eriksgatan 28, Stockholm",
        "Linnégatan 47, Göteborg",
        "Baltzarsgatan 37, Malmö",
      ]),
    ],
    paymentOptions: [
      { id: "swish", label: "Swish", requiresBankDetails: false },
      { id: "bank", label: "Banköverföring", requiresBankDetails: true },
    ],
  },
  fixiphone: {
    name: "FixiPhone",
    personalNumberRequirement: "never",
    shippingOptions: [
      {
        id: "email-label",
        label: "Fraktetikett via e-post",
        description: "Gratis, 190 kr debiteras om du vill få tillbaka telefonen efter inlämning",
        features: ["Utskrivbar fraktsedel", "Skriv ut och fäst på paketet", "Retur kostar 190 kr"],
      },
      storeOption("store-dropoff", "Inlämning via butik", fixiphoneStores),
    ],
    paymentOptions: [{ id: "bank", label: "Banköverföring", requiresBankDetails: true }],
  },
  telestore: {
    name: "Telestore",
    personalNumberRequirement: "always",
    shippingOptions: [
      {
        id: "email-label",
        label: "Fraktetikett via e-post",
        description: "99 kr fraktavgift dras av från priset",
        features: ["QR-kod via SMS eller mejl", "Visa koden hos PostNord"],
        feeSek: 99,
        feeLabel: "fraktavgift",
      },
      storeOption("store-dropoff", "Inlämning via butik", ["Skrantahöjdsvägen 40, Karlskoga"]),
    ],
    paymentOptions: [
      { id: "swish", label: "Swish", requiresBankDetails: false },
      { id: "bank", label: "Banköverföring", requiresBankDetails: true },
    ],
  },
  happyphone: {
    name: "HappyPhone",
    personalNumberRequirement: "swish",
    shippingOptions: [
      {
        id: "sales-package",
        label: "Försäljningspaket",
        description: "Gratis",
        features: ["Paket skickas hem", "Fraktmaterial ingår", "Gratis"],
      },
      storeOption("store-dropoff", "Inlämning via butik", fixMyPhoneStores),
    ],
    paymentOptions: [
      { id: "swish", label: "Swish", requiresBankDetails: false },
      { id: "bank", label: "Banköverföring", requiresBankDetails: true },
    ],
  },
  fixmyphone: {
    name: "FixMyPhone",
    personalNumberRequirement: "swish",
    shippingOptions: [
      {
        id: "sales-package",
        label: "Försäljningspaket",
        description: "Gratis",
        features: ["Paket skickas hem", "Fraktmaterial ingår", "Gratis"],
      },
      storeOption("store-dropoff", "Inlämning via butik", fixMyPhoneStores),
    ],
    paymentOptions: [
      { id: "swish", label: "Swish", requiresBankDetails: false },
      { id: "bank", label: "Banköverföring", requiresBankDetails: true },
    ],
  },
  renewed: {
    name: "ReNewed",
    personalNumberRequirement: "never",
    shippingOptions: [
      {
        id: "email-label",
        label: "Fraktetikett via e-post",
        description: "Gratis",
        features: ["Fraktsedel skickas via e-post", "Skriv ut och fäst på paketet", "Lämna hos ombud"],
      },
    ],
    paymentOptions: [{ id: "bank", label: "Banköverföring", requiresBankDetails: true }],
  },
  cleverbuy: {
    name: "CleverBuy",
    personalNumberRequirement: "never",
    shippingOptions: [
      {
        id: "email-label",
        label: "Digital fraktsedel via e-post",
        description: "Få fraktsedeln direkt till din inkorg",
        features: ["Fraktsedel skickas via e-post", "Skriv ut och fäst på paketet", "Lämna hos ombud"],
      },
    ],
    paymentOptions: [{ id: "bank-iban", label: "Banköverföring (IBAN)", requiresBankDetails: true }],
  },
};

export const dealerIdFromName = (companyName: string): string => {
  const name = companyName.toLowerCase();
  if (name.includes("swappie")) return "swappie";
  if (name.includes("fixmyphone") || name.includes("fix my phone")) return "fixmyphone";
  if (name.includes("happyphone") || name.includes("happy phone")) return "happyphone";
  if (name.includes("telestore")) return "telestore";
  if (name.includes("renewed")) return "renewed";
  if (name.includes("phonehero") || name.includes("phone hero")) return "phonehero";
  if (name.includes("fixiphone") || name.includes("fix iphone")) return "fixiphone";
  if (name.includes("fixtech") || name.includes("fix tech") || name.includes("fixphonepro")) return "fixphonepro";
  if (name.includes("cleverbuy") || name.includes("clever buy")) return "cleverbuy";
  return "swappie";
};

export const getDealerConfig = (dealerIdOrName: string): DealerConfig => {
  const direct = dealerConfig[dealerIdOrName.toLowerCase()];
  return direct ?? dealerConfig[dealerIdFromName(dealerIdOrName)];
};

export const requiresPersonalNumber = (
  config: DealerConfig,
  payment: PaymentMethod | "bank-iban" | string | null | undefined,
) => config.personalNumberRequirement === "always" || (config.personalNumberRequirement === "swish" && payment === "swish");
