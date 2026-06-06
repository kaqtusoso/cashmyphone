import { ConditionAnswers } from "./condition";
import { CompanyOffer } from "@/types/offers";

export interface SavedOffer {
  id: string;
  model: string;
  storage: string;
  condition: ConditionAnswers;
  offers: CompanyOffer[] | null;
  selectedOffer?: CompanyOffer | null;
  timestamp: number;
}

export interface SavedOffersContextType {
  savedOffers: SavedOffer[];
  addSavedOffer: (offer: SavedOffer) => void;
  removeSavedOffer: (id: string) => void;
  clearAllSavedOffers: () => void;
  getSavedOffers: () => SavedOffer[];
}
