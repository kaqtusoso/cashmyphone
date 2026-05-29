import { createContext, useState, useEffect, ReactNode } from "react";
import { SavedOffer, SavedOffersContextType } from "@/types/savedOffers";

const STORAGE_KEY = "cashmyphone_savedOffers";
const MAX_OFFERS = 20;
const EXPIRY_TIME = 4 * 60 * 60 * 1000; // 4 hours

export const SavedOffersContext = createContext<SavedOffersContextType | undefined>(undefined);

const isExpired = (timestamp: number): boolean => {
  return Date.now() - timestamp > EXPIRY_TIME;
};

const loadFromStorage = (): SavedOffer[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    
    const parsed = JSON.parse(stored) as SavedOffer[];
    
    // Migrate old data + filter expired
    const valid = parsed
      .map(offer => ({
        ...offer,
        offers: offer.offers || null,
        selectedOffer: offer.selectedOffer || null,
      }))
      .filter(offer => !isExpired(offer.timestamp));
    
    // If we migrated or filtered any, update storage
    if (valid.length !== parsed.length) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(valid));
    }
    
    return valid;
  } catch (error) {
    console.error("Failed to load saved offers:", error);
    return [];
  }
};

const saveToStorage = (offers: SavedOffer[]): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(offers));
  } catch (error) {
    console.error("Failed to save offers:", error);
  }
};

export const SavedOffersProvider = ({ children }: { children: ReactNode }) => {
  const [savedOffers, setSavedOffers] = useState<SavedOffer[]>(() => loadFromStorage());

  useEffect(() => {
    saveToStorage(savedOffers);
  }, [savedOffers]);

  const addSavedOffer = (offer: SavedOffer) => {
    setSavedOffers(prev => {
      // Check for duplicate (same model + storage)
      const duplicateIndex = prev.findIndex(
        o => o.model === offer.model && o.storage === offer.storage
      );

      let updated: SavedOffer[];
      
      if (duplicateIndex !== -1) {
        // Replace existing
        updated = [...prev];
        updated[duplicateIndex] = offer;
      } else {
        // Add new
        updated = [offer, ...prev];
        
        // Keep only MAX_OFFERS (FIFO)
        if (updated.length > MAX_OFFERS) {
          updated = updated.slice(0, MAX_OFFERS);
        }
      }

      return updated;
    });
  };

  const removeSavedOffer = (id: string) => {
    setSavedOffers(prev => prev.filter(offer => offer.id !== id));
  };

  const clearAllSavedOffers = () => {
    setSavedOffers([]);
  };

  const getSavedOffers = (): SavedOffer[] => {
    return savedOffers;
  };

  return (
    <SavedOffersContext.Provider
      value={{
        savedOffers,
        addSavedOffer,
        removeSavedOffer,
        clearAllSavedOffers,
        getSavedOffers,
      }}
    >
      {children}
    </SavedOffersContext.Provider>
  );
};
