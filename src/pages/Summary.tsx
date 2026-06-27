import { useEffect, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowRight, Mail, PackageCheck, Truck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatOrderPrice, IntegrationStatus, Order } from "@/utils/orders";

interface SummaryState {
  order?: Order;
  integrations?: Record<"google_sheets" | "email", IntegrationStatus>;
}

const readStoredOrder = (): Order | null => {
  try {
    const raw = sessionStorage.getItem("televera:last-order");
    return raw ? (JSON.parse(raw) as Order) : null;
  } catch {
    return null;
  }
};

const Summary = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const summaryState = (state || {}) as SummaryState;
  const order = useMemo(() => summaryState.order || readStoredOrder(), [summaryState.order]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (!order) navigate("/", { replace: true });
  }, [order, navigate]);

  if (!order) return null;

  const customerName = `${order.customer.first_name} ${order.customer.last_name}`;
  const createdAt = new Date(order.created_at);
  const createdLabel = Number.isNaN(createdAt.getTime())
    ? ""
    : createdAt.toLocaleString("sv-SE", {
        dateStyle: "medium",
        timeStyle: "short",
      });
  const emailStatus = summaryState.integrations?.email;
  const nextStepTextClass = "mt-2 text-sm leading-relaxed text-muted-foreground";
  const nextStepCardClass =
    "rounded-xl border border-primary/20 bg-background/90 p-5 shadow-sm shadow-foreground/5 transition-colors hover:border-primary/35";

  return (
    <>
      <Helmet>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
      <main className="bg-background px-4 py-10 md:py-12">
        <div className="mx-auto max-w-3xl">
        <div className="mb-8 text-center md:mb-10">
          <h1 className="font-heading text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Tack, {order.customer.first_name}
          </h1>
          <p className="mt-3 text-muted-foreground">
            Din order är registrerad. Spara ordernumret om du behöver kontakta oss.
          </p>
        </div>

        <Card className="mb-6 overflow-hidden rounded-2xl border-border shadow-lg shadow-foreground/5">
          <div className="border-b border-border bg-muted/40 p-5 md:p-6">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Ordernummer</p>
                <p className="font-mono text-xl font-bold text-foreground">{order.order_id}</p>
              </div>
              {createdLabel && <p className="text-sm text-muted-foreground">{createdLabel}</p>}
            </div>
          </div>

          <div className="grid gap-6 p-5 md:grid-cols-2 md:p-6">
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Mobil</p>
                <p className="font-semibold text-foreground">
                  {order.model} {order.storage}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Köpare</p>
                <p className="font-semibold text-foreground">{order.dealer_name}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Uppskattat pris</p>
                <p className="text-2xl font-bold text-primary">{formatOrderPrice(order.price_sek)}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Kund</p>
                <p className="font-semibold text-foreground">{customerName}</p>
                <p className="text-sm text-muted-foreground">{order.customer.email}</p>
                <p className="text-sm text-muted-foreground">{order.customer.phone}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Frakt</p>
                <p className="font-semibold text-foreground">{order.shipping_label}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Betalning</p>
                <p className="font-semibold text-foreground">{order.payment.label}</p>
              </div>
            </div>
          </div>
        </Card>

        <Card className="mb-8 rounded-2xl border-primary/20 bg-primary/5 p-5 shadow-md shadow-primary/5 md:p-6">
          <div className="mb-5">
            <h2 className="font-heading text-xl font-bold text-foreground">Vad händer nu?</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <div className={nextStepCardClass}>
              <Mail className="mb-4 h-5 w-5 text-foreground" />
              <p className="text-base font-semibold text-foreground">Bekräftelse</p>
              <p className={nextStepTextClass}>
                {emailStatus?.configured === false
                  ? "Klart! Din order är sparad och ordernumret finns ovan."
                  : "En bekräftelse skickas till din e-postadress."}
              </p>
            </div>
            <div className={nextStepCardClass}>
              <Truck className="mb-4 h-5 w-5 text-foreground" />
              <p className="text-base font-semibold text-foreground">Frakt</p>
              <p className={nextStepTextClass}>
                Du får fraktinstruktioner och skickar mobilen när du är redo.
              </p>
            </div>
            <div className={nextStepCardClass}>
              <PackageCheck className="mb-4 h-5 w-5 text-foreground" />
              <p className="text-base font-semibold text-foreground">Kontroll & betalning</p>
              <p className={nextStepTextClass}>
                {order.dealer_name} kontrollerar mobilen och betalar ut enligt valt betalningssätt.
              </p>
            </div>
          </div>
        </Card>

        <div className="flex justify-center">
          <Button onClick={() => navigate("/")} size="lg" variant="outline">
            Till startsidan
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
        </div>
      </main>
    </>
  );
};

export default Summary;
