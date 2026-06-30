import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import CheckoutContent from "@/components/CheckoutContent";
import { CompanyOffer } from "@/types/offers";
import { ConditionAnswers } from "@/types/condition";

interface SellOfferDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  offer: CompanyOffer | null;
  model: string;
  storage: string;
  color?: string;
  conditionAnswers?: ConditionAnswers;
  savedOfferId?: string;
}

const getDealerId = (companyName: string): string => {
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

const SellOfferDialog = ({
  open,
  onOpenChange,
  offer,
  model,
  storage,
  color,
  conditionAnswers,
  savedOfferId,
}: SellOfferDialogProps) => {
  if (!offer) return null;
  const dealerId = getDealerId(offer.företag);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[92vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">
            Sälj till <span className="text-primary">{offer.företag}</span>
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            {model} {storage} ·{" "}
            <span className="font-semibold text-foreground">
              {offer.pris.toLocaleString("sv-SE")} kr
            </span>
          </p>
        </DialogHeader>

        <div className="pt-2">
          <CheckoutContent
            dealer={dealerId}
            model={model}
            storage={storage}
            color={color}
            price={String(offer.pris)}
            conditionAnswers={conditionAnswers as unknown as Record<string, unknown>}
            savedOfferId={savedOfferId}
            compact
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SellOfferDialog;
