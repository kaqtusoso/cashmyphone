import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, useLocation } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import CheckoutContent, { dealerConfig } from "@/components/CheckoutContent";

const CHECKOUT_STEP_SLUGS: Record<string, number> = {
  uppgifter: 1,
  "frakt-betalning": 2,
  bekrafta: 3,
};

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

const Checkout = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const checkoutStep = location.pathname.split("/")[2];
  const [isRestoredFromSaved, setIsRestoredFromSaved] = useState(false);
  const savedOfferId = location.state?.restoreFromSavedOffer?.id || location.state?.savedOfferId;

  // Handle restore from saved offer
  useEffect(() => {
    const savedOffer = location.state?.restoreFromSavedOffer;
    if (savedOffer) {
      if (!savedOffer.selectedOffer) {
        toast.error("Ingen erbjudande valt. Återgår till jämförelse.");
        navigate("/", { state: { restoreFromSavedOffer: savedOffer }, replace: true });
        return;
      }
      setIsRestoredFromSaved(true);
      const offerToUse = savedOffer.selectedOffer;
      const params = new URLSearchParams(searchParams);
      params.set("model", savedOffer.model);
      params.set("storage", savedOffer.storage);
      if (savedOffer.color) params.set("color", savedOffer.color);
      params.set("price", offerToUse.pris.toString());

      params.set("dealer", getDealerId(offerToUse.företag));
      setSearchParams(params, { replace: true });

      toast.success("Värdering återställd från sparade", {
        description: `${savedOffer.model} ${savedOffer.storage}`,
      });
    }
  }, [location.state, setSearchParams, searchParams, navigate]);

  const conditionAnswers =
    location.state?.conditionAnswers || JSON.parse(localStorage.getItem("conditionAnswers") || "{}");

  const dealer = searchParams.get("dealer") || "swappie";
  const model = searchParams.get("model");
  const storage = searchParams.get("storage");
  const color = searchParams.get("color") || location.state?.restoreFromSavedOffer?.color || "";
  const price = searchParams.get("price");

  if ((!model || !storage || !price) && !location.state?.restoreFromSavedOffer) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-background to-muted/30 flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-foreground mb-4">Ogiltig värdering</h1>
          <p className="text-muted-foreground mb-6">Värderingsinformation saknas. Vänligen gör en ny värdering.</p>
          <Button onClick={() => navigate("/")}>Gå till startsidan</Button>
        </div>
      </div>
    );
  }

  // Validate dealer
  const dealerKey = dealerConfig[dealer] ? dealer : "swappie";

  return (
    <div className="min-h-full">
      <Helmet>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      <main className="pt-10 pb-12 px-4 bg-background">
        <CheckoutContent
          dealer={dealerKey}
          model={model || ""}
          storage={storage || ""}
          color={color}
          price={price || ""}
          conditionAnswers={conditionAnswers}
          savedOfferId={savedOfferId}
          showRestoredBanner={isRestoredFromSaved}
          initialStep={checkoutStep ? CHECKOUT_STEP_SLUGS[checkoutStep] ?? 1 : 1}
        />
      </main>
    </div>
  );
};

export default Checkout;
