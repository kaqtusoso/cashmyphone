import { Bookmark, X, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSavedOffers } from "@/hooks/useSavedOffers";
import { useNavigate } from "react-router-dom";
import { useIsMobile } from "@/hooks/use-mobile";
import { ConditionAnswers } from "@/types/condition";
import { getConditionSummary as computeConditionSummary } from "@/utils/priceAdjustment";
import {
  Drawer,
  DrawerClose,
  DrawerContent,
  DrawerDescription,
  DrawerFooter,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

// Company logos mapping
const companyLogos: Record<string, string> = {
  Swappie: "/src/assets/swappie-logo.png",
  FixMyPhone: "/src/assets/fixmyphone-logo.png",
  HappyPhone: "/src/assets/happyphone-logo.png",
  Telestore: "/src/assets/telestore-logo.png",
};

const getTimeAgo = (timestamp: number): string => {
  const minutes = Math.floor((Date.now() - timestamp) / 60000);
  if (minutes < 60) return `${minutes} min sedan`;
  const hours = Math.floor(minutes / 60);
  return `${hours} tim sedan`;
};

// Compute condition summary from new answers shape
const getConditionSummary = (condition: ConditionAnswers) => computeConditionSummary(condition);

interface SavedOffersPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const SavedOffersPanel = ({ open, onOpenChange }: SavedOffersPanelProps) => {
  const { savedOffers, removeSavedOffer, clearAllSavedOffers } = useSavedOffers();
  const navigate = useNavigate();
  const isMobile = useIsMobile();

  const handleViewOffer = (offerId: string) => {
    const offer = savedOffers.find((o) => o.id === offerId);
    if (!offer) return;

    onOpenChange(false);

    // If selectedOffer exists, go to checkout
    if (offer.selectedOffer) {
      navigate("/checkout", {
        state: { restoreFromSavedOffer: offer },
      });
    } else {
      // If no selectedOffer, go to homepage to restore valuation
      navigate("/", {
        state: {
          restoreFromSavedOffer: offer,
        },
      });
    }
  };

  const handleRemove = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    removeSavedOffer(id);
  };

  const handleClearAll = () => {
    clearAllSavedOffers();
  };

  const panelContent = (
    <>
      <div className="overflow-y-auto flex-1 p-4">
        {savedOffers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <h3 className="text-lg font-medium text-foreground mb-2">Du har inga sparade värderingar ännu</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              När du väljer ett erbjudande sparas det här så du kan komma tillbaka till det senare
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {savedOffers.map((offer) => {
              const hasOffers = offer.offers && offer.offers.length > 0;
              const bestPrice = hasOffers ? Math.max(...offer.offers.map((o) => o.pris)) : 0;

              return (
                <div
                  key={offer.id}
                  className="bg-[#F5FFF7] rounded-2xl p-4 border border-border/30 hover:border-primary/30 transition-all"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-foreground mb-1 truncate">
                        📱 {offer.model} • {offer.storage}
                      </h3>

                      {/* Condition Summary */}
                      <div className="bg-muted/20 rounded-md py-2 mb-3">
                        <div className="space-y-1 text-xs text-muted-foreground">
                          {(() => {
                            const summary = getConditionSummary(offer.condition);
                            return (
                              <>
                                <div>
                                  <span className="font-semibold text-foreground">Skick:</span> {summary.condition}
                                </div>
                                <div>
                                  <span className="font-semibold text-foreground">Batteri:</span> {summary.battery}%
                                </div>
                                <div>
                                  <span className="font-semibold text-foreground">Spricka:</span>{" "}
                                  {summary.cracks ? "Ja" : "Nej"}
                                </div>
                                <div>
                                  <span className="font-semibold text-foreground">Vattenskada:</span>{" "}
                                  {summary.waterDamage ? "Ja" : "Nej"}
                                </div>
                              </>
                            );
                          })()}
                        </div>
                      </div>

                      {hasOffers && offer.selectedOffer ? (
                        <>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-2xl font-bold text-primary">
                              {offer.selectedOffer.pris.toLocaleString("sv-SE")} kr
                            </span>
                          </div>

                          {offer.selectedOffer && (
                            <p className="text-sm font-medium text-foreground mb-2">{offer.selectedOffer.företag}</p>
                          )}
                        </>
                      ) : (
                        <p className="text-sm text-muted-foreground mb-2">Inga erbjudanden tillgängliga</p>
                      )}

                      <p className="text-xs text-muted-foreground">Sparad {getTimeAgo(offer.timestamp)}</p>
                    </div>

                    <div className="flex flex-col gap-2">
                      <Button size="sm" onClick={() => handleViewOffer(offer.id)} className="whitespace-nowrap">
                        ➜
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => handleRemove(offer.id, e)}
                        className="text-destructive bg-destructive/10 hover:bg-destructive/10 hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {savedOffers.length > 0 && (
        <div className="border-t border-border/50 p-4">
          <Button variant="destructive" onClick={handleClearAll} className="w-full">
            Rensa alla värderingar
          </Button>
        </div>
      )}
    </>
  );

  return (
    <>
      {isMobile ? (
        // Mobile & Tablet (< 768px): Drawer from bottom
        <Drawer open={open} onOpenChange={onOpenChange}>
          <DrawerContent className="max-h-[85vh]">
            <DrawerHeader className="border-b border-border/50">
              <div className="flex items-center justify-between">
                <DrawerTitle className="text-xl font-semibold">Värderingar</DrawerTitle>
                <DrawerClose asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <X className="h-4 w-4" />
                  </Button>
                </DrawerClose>
              </div>
              <DrawerDescription className="text-left">
                {savedOffers.length > 0
                  ? `Du har ${savedOffers.length} sparad${savedOffers.length > 1 ? "e" : ""} värdering${savedOffers.length > 1 ? "ar" : ""}`
                  : "Inga sparade värderingar ännu"}
              </DrawerDescription>
            </DrawerHeader>
            {panelContent}
          </DrawerContent>
        </Drawer>
      ) : (
        // Desktop (>= 768px): Sheet sliding from right
        <Sheet open={open} onOpenChange={onOpenChange}>
          <SheetContent side="right" className="w-full sm:max-w-md flex flex-col">
            <SheetHeader className="border-b border-border/50 pb-4">
              <SheetTitle className="text-xl font-semibold">Värderingar</SheetTitle>
              <SheetDescription className="text-left">
                {savedOffers.length > 0
                  ? `Du har ${savedOffers.length} sparad${savedOffers.length > 1 ? "e" : ""} värdering${savedOffers.length > 1 ? "ar" : ""}`
                  : "Inga sparade värderingar ännu"}
              </SheetDescription>
            </SheetHeader>
            {panelContent}
          </SheetContent>
        </Sheet>
      )}
    </>
  );
};
