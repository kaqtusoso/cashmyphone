import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import CheckoutContent, { dealerConfig } from "@/components/CheckoutContent";

const Checkout = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
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
      params.set("price", offerToUse.pris.toString());

      const companyLower = offerToUse.företag.toLowerCase();
      let dealerId = "swappie";
      if (companyLower.includes("swappie")) dealerId = "swappie";
      else if (companyLower.includes("fixmyphone")) dealerId = "fixmyphone";
      else if (companyLower.includes("happyphone")) dealerId = "happyphone";
      else if (companyLower.includes("telestore")) dealerId = "telestore";

      params.set("dealer", dealerId);
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
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 pt-24 pb-12 px-4 bg-background">
        <CheckoutContent
          dealer={dealerKey}
          model={model || ""}
          storage={storage || ""}
          price={price || ""}
          conditionAnswers={conditionAnswers}
          savedOfferId={savedOfferId}
          showRestoredBanner={isRestoredFromSaved}
        />
      </main>
      <Footer />
    </div>
  );
};

export default Checkout;
