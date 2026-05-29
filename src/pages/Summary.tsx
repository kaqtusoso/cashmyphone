import { useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2 } from "lucide-react";
import Header from "@/components/Header";
import Footer from "@/components/Footer";

const Summary = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const data = state || {};

  useEffect(() => {
    const timeout = setTimeout(() => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }, 100); // liten delay för att vänta på DOM-rendern

    return () => clearTimeout(timeout);
  }, []);

  // Om ingen data finns, redirecta tillbaka till startsidan
  useEffect(() => {
    if (!state) {
      navigate("/");
    }
  }, [state, navigate]);

  if (!state) {
    return null;
  }

  // Översätt betalningsmetod
  const getPaymentMethodLabel = (method: string) => {
    if (method === "bank") return "Banköverföring";
    if (method === "swish") return "Swish";
    return method;
  };

  // Översätt fraktmetod
  const getShippingLabel = (option: string) => {
    const labels: Record<string, string> = {
      "sales-package": "Försäljningspaket",
      "email-label": "Fraktsedel via e-post",
      "own-material": "Eget packmaterial + e-fraktsedel",
    };
    return labels[option] || option;
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 pt-24 pb-6 px-4 bg-background">
        <div className="max-w-md mx-auto animate-fade-in">
          {/* Sammanfattningsruta */}
          <Card
            className="p-6 shadow-card mb-8 space-y-4 animate-fade-in"
            style={{ animationDelay: "0.1s", animationFillMode: "both" }}
          >
            <h2 className="font-semibold text-lg border-b pb-2">Sammanfattning</h2>

            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Modell:</span>
                <span className="font-medium">{data.model || "–"}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-muted-foreground">Lagring:</span>
                <span className="font-medium">{data.storage || "–"}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-muted-foreground">Köpare:</span>
                <span className="font-medium">{data.dealer || "–"}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-muted-foreground">Fraktmetod:</span>
                <span className="font-medium">{getShippingLabel(data.shippingOption)}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-muted-foreground">Betalningsmetod:</span>
                <span className="font-medium">{getPaymentMethodLabel(data.paymentMethod)}</span>
              </div>

              <div className="flex justify-between border-t pt-3 mt-3">
                <span className="text-muted-foreground font-semibold">Uppskattat pris:</span>
                <span className="font-bold text-primary text-lg">{data.price || "–"}</span>
              </div>
            </div>
          </Card>

          {/* Vad händer nu? */}
          <Card
            className="p-6 shadow-card mb-8 bg-primary/5 border-primary/20 animate-fade-in"
            style={{ animationDelay: "0.2s", animationFillMode: "both" }}
          >
            <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <span className="text-primary">📦</span> Vad händer nu?
            </h2>
            <ul className="space-y-3 text-sm text-foreground/90">
              <li className="flex gap-2">
                <span className="text-primary font-bold">1.</span>
                <span>Du får snart ett mejl med instruktioner om frakten.</span>
              </li>
              <li className="flex gap-2">
                <span className="text-primary font-bold">2.</span>
                <span>När {data.dealer} har mottagit din mobil sker betalningen inom 1–3 arbetsdagar.</span>
              </li>
            </ul>
          </Card>

          {/* Knapp tillbaka */}
          <div className="animate-fade-in" style={{ animationDelay: "0.3s", animationFillMode: "both" }}>
            <Button onClick={() => navigate("/")} className="w-full" size="lg">
              Tillbaka till startsidan
            </Button>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Summary;
