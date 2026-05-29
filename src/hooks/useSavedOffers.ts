import { useContext } from "react";
import { SavedOffersContext } from "@/contexts/SavedOffersContext";

export const useSavedOffers = () => {
  const context = useContext(SavedOffersContext);
  if (!context) {
    throw new Error("useSavedOffers must be used within SavedOffersProvider");
  }
  return context;
};
