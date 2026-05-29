import { Package, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CompanyOffer } from "@/data/mockData";
import trustpilotLogo from "@/assets/trustpilot-logo.png";

interface ComparisonTableProps {
  offers: CompanyOffer[];
  loading?: boolean;
  onSelectOffer?: (offer: CompanyOffer) => void;
}

const ComparisonTable = ({ offers, loading, onSelectOffer }: ComparisonTableProps) => {
  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block animate-pulse-soft mb-4">
          <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
            <Package className="w-8 h-8 text-primary" />
          </div>
        </div>
        <p className="text-muted-foreground">Jämför priser...</p>
      </div>
    );
  }

  if (offers.length === 0) return null;

  const sorted = [...offers]
    .filter((o) => o.pris != null && !isNaN(o.pris))
    .sort((a, b) => b.pris - a.pris);

  const lowest = sorted[sorted.length - 1]?.pris ?? 0;

  return (
    <div className="space-y-3">
      {sorted.map((offer, index) => {
        const isBest = index === 0;
        const diff = offer.pris - lowest;
        return (
          <div
            key={`${offer.företag}-${index}`}
            className={`group bg-card rounded-xl p-3 sm:p-5 transition-all duration-200 hover:shadow-md ${
              isBest ? "border-2 border-primary" : "border border-border"
            }`}
          >
            <div className="flex items-center gap-3 sm:gap-4">
              {/* Rank */}
              <div
                className={`flex-shrink-0 w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                  isBest
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {index + 1}
              </div>

              {/* Company + price (mobile compact) */}
              <div className="min-w-0 flex-1">
                <p className="font-bold text-base sm:text-lg text-foreground truncate">
                  {offer.företag}
                </p>
                <p className="text-[11px] sm:text-xs text-muted-foreground truncate flex items-center gap-1.5">
                  {offer.trustpilotScore ? (
                    <>
                      <span className="font-medium text-foreground">
                        {offer.trustpilotScore.replace(",", ".")}
                      </span>
                      <span>på</span>
                      <a
                        href={offer.trustpilotUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center hover:opacity-80 transition-opacity"
                        onClick={(e) => e.stopPropagation()}
                        aria-label="Trustpilot"
                      >
                        <img
                          src={trustpilotLogo}
                          alt="Trustpilot"
                          className="h-3 sm:h-3.5 w-auto dark:invert"
                          loading="lazy"
                        />
                      </a>
                      <span>· {offer.trustpilotReviews} omdömen</span>
                    </>
                  ) : (
                    <span className="truncate">{offer.leverans} · {offer.utbetalningstid}</span>
                  )}
                </p>
                <div className="flex items-baseline gap-2 sm:hidden mt-1">
                  <span className="font-bold text-base text-foreground whitespace-nowrap">
                    {offer.pris.toLocaleString("sv-SE")} kr
                  </span>
                  {diff > 0 && (
                    <span className="text-[11px] font-semibold text-primary whitespace-nowrap">
                      +{diff.toLocaleString("sv-SE")} kr
                    </span>
                  )}
                </div>
              </div>

              {/* Desktop price */}
              <div className="hidden sm:block text-right">
                <div className="font-bold text-xl text-foreground whitespace-nowrap leading-tight">
                  {offer.pris.toLocaleString("sv-SE")} kr
                </div>
                {diff > 0 && (
                  <div className="text-xs font-semibold text-primary whitespace-nowrap">
                    +{diff.toLocaleString("sv-SE")} kr
                  </div>
                )}
              </div>

              <Button
                size="sm"
                onClick={() => onSelectOffer?.(offer)}
                className="bg-primary hover:bg-primary/90 text-primary-foreground px-4 sm:px-5 flex-shrink-0"
              >
                Sälj
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ComparisonTable;
