import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  Check,
  ChevronLeft,
  Landmark,
  Mail,
  Package,
  Shield,
  Star,
  WalletCards,
} from "lucide-react";

import SiteFooter from "@/components/SiteFooter";
import { CompanyOffer } from "@/types/offers";
import { makeOptimisticOrder, Order, submitOrder } from "@/utils/orders";
import { getIphoneImage } from "@/utils/iphoneImage";
import {
  CheckoutErrors,
  CheckoutField,
  emptyCheckoutForm,
  formatPersonalNumber,
  formatPhone,
  hasErrors,
  PaymentMethod,
  validateCustomerDetails,
  validatePaymentDetails,
} from "@/utils/checkoutValidation";
import swishLogo from "@/assets/swish-logo.webp";
import paypalLogo from "@/assets/paypal-logo.svg";
import "./MobileCommerceFlow.css";

type MobileCommerceStep = "results" | "co1" | "co2" | "co3" | "done";

interface MobileCommerceFlowProps {
  offers: CompanyOffer[];
  model: string;
  storage: string;
  color?: string;
  conditionAnswers?: Record<string, unknown>;
  onBack: () => void;
}

const fmt = (value: number) => value.toLocaleString("sv-SE");
const ORDER_SUBMIT_ANIMATION_MS = 800;
const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

const Squiggle = () => (
  <svg className="cmp-mcommerce-squiggle" viewBox="0 0 200 12" preserveAspectRatio="none" aria-hidden>
    <path d="M3 8 C 45 3, 90 3, 130 6 S 185 9, 197 5" />
  </svg>
);

const Rating = ({ rating, dark = false }: { rating?: string; dark?: boolean }) => (
  <span className={`cmp-mcommerce-rating ${dark ? "dark" : ""}`}>
    <Star aria-hidden />
    <span>Trustpilot</span>
    <strong>{rating ?? "-"}</strong>
  </span>
);

const prettyScore = (rating?: string) => rating?.replace(".", ",") ?? "-";
const paymentMethods = (offer: CompanyOffer) => (offer.paymentMethods?.length ? offer.paymentMethods : ["Banköverföring"]);
const paypalFee = (priceSek: number) => (priceSek >= 5000 ? 100 : Math.round(priceSek * 0.02));
const payoutAmount = (offer: CompanyOffer, payment: PaymentMethod | null) =>
  payment === "paypal" ? Math.max(0, offer.pris - paypalFee(offer.pris)) : offer.pris;
const methodId = (method: string): PaymentMethod => {
  const normalized = method.toLowerCase();
  if (normalized.includes("swish")) return "swish";
  if (normalized.includes("paypal")) return "paypal";
  return "bank";
};
const methodPriority = (method: string) => {
  const id = methodId(method);
  if (id === "swish") return 0;
  if (id === "paypal") return 1;
  return 2;
};
const sortedPaymentMethods = (offer: CompanyOffer) =>
  [...paymentMethods(offer)].sort((a, b) => methodPriority(a) - methodPriority(b));
const paymentCopy = (method: PaymentMethod, priceSek: number) => {
  if (method === "swish") return "Telefonnummer";
  if (method === "paypal") return "PayPal-e-post";
  return "Clearing- och kontonummer";
};
const paymentLabelFor = (payment: PaymentMethod | null) => {
  if (payment === "swish") return "Swish";
  if (payment === "paypal") return "PayPal";
  return "Banköverföring";
};

const TrustpilotBadge = ({ offer, compact = false }: { offer: CompanyOffer; compact?: boolean }) => {
  const rating = Number.parseFloat(offer.trustpilotScore ?? "0");
  const content = (
    <>
      <span className="cmp-mcommerce-trust-score">{prettyScore(offer.trustpilotScore)}{compact ? "/5" : ""}</span>
      {!compact ? (
        <span className="cmp-mcommerce-trust-stars" aria-hidden>
          {[0, 1, 2, 3, 4].map((index) => (
            <Star key={index} className={rating >= index + 0.75 ? "filled" : ""} />
          ))}
        </span>
      ) : null}
      {!compact ? <span className="cmp-mcommerce-trust-text">
        {prettyScore(offer.trustpilotScore)} av 5 ({offer.trustpilotReviews ?? "0"} omdömen)
      </span> : null}
    </>
  );

  if (!offer.trustpilotUrl) {
    return <span className={`cmp-mcommerce-trust-badge ${compact ? "compact" : ""}`}>{content}</span>;
  }

  return (
    <a className={`cmp-mcommerce-trust-badge ${compact ? "compact" : ""}`} href={offer.trustpilotUrl} target="_blank" rel="noreferrer">
      {content}
    </a>
  );
};

const PaymentBadges = ({ offer }: { offer: CompanyOffer }) => (
  <div className="cmp-mcommerce-payment-badges" aria-label={`Betalning: ${paymentMethods(offer).join(", ")}`}>
    {sortedPaymentMethods(offer).map((method) => {
      const id = methodId(method);
      return (
        <span key={method} className={id}>
          {id === "swish" ? <img src={swishLogo} alt="" aria-hidden /> : id === "paypal" ? <img src={paypalLogo} alt="" aria-hidden /> : <Landmark aria-hidden />}
          {id === "swish" ? method : id === "paypal" ? "PayPal" : "Bank"}
        </span>
      );
    })}
  </div>
);

const Head = ({ title, sub, onBack }: { title: string; sub?: string; onBack?: () => void }) => (
  <header className="cmp-mcommerce-head">
    {onBack ? (
      <button type="button" onClick={onBack} aria-label="Tillbaka">
        <ChevronLeft aria-hidden />
      </button>
    ) : (
      <span />
    )}
    <div>
      <strong>{title}</strong>
      {sub ? <p>{sub}</p> : null}
    </div>
    <span />
  </header>
);

const StepDots = ({ step }: { step: number }) => {
  const labels = ["Leverans", "Uppgifter", "Granska"];
  return (
    <div className="cmp-mcommerce-steps" aria-label={`Kassa steg ${step + 1} av 3`}>
      {labels.map((label, index) => (
        <div key={label} className={index === step ? "active" : index < step ? "done" : ""}>
          <strong>{index < step ? <Check aria-hidden /> : index + 1}{index === step ? <Squiggle /> : null}</strong>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
};

const PayoutMini = ({ offer, model, storage, payment }: { offer: CompanyOffer; model: string; storage: string; payment?: PaymentMethod | null }) => (
  <section className="cmp-mcommerce-payout">
    <div className="cmp-mcommerce-payout-info">
      <h2>{offer.företag}</h2>
      <span>{model} · {storage}</span>
      <TrustpilotBadge offer={offer} />
    </div>
    <div className="cmp-mcommerce-payout-price">
      <small>DU FÅR</small>
      <span><strong>{fmt(payoutAmount(offer, payment ?? null))}<Squiggle /></strong><em>SEK</em></span>
    </div>
  </section>
);

const FeeTrail = ({ amount }: { amount: number }) => (
  <span className="cmp-mcommerce-fee-trail">
    <strong>-{fmt(amount)} kr</strong>
    <em>(avgifter)</em>
  </span>
);

const Pick = ({ selected, title, sub, icon, trail, onClick }: { selected: boolean; title: string; sub: string; icon?: ReactNode; trail?: ReactNode; onClick: () => void }) => (
  <button type="button" className={`cmp-mcommerce-pick ${selected ? "selected" : ""}`} onClick={onClick}>
    <span>{selected ? <Check aria-hidden /> : null}</span>
    <div>
      <strong>{icon}{title}</strong>
      <p>{sub}</p>
    </div>
    {trail}
  </button>
);

const Field = ({
  label,
  placeholder,
  value,
  onChange,
  error,
  type = "text",
  inputMode,
  format,
  required,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  type?: string;
  inputMode?: React.HTMLAttributes<HTMLInputElement>["inputMode"];
  format?: "phone" | "personalNumber";
  required?: boolean;
}) => (
  <label className="cmp-mcommerce-field">
    <span>{label}{required ? " *" : ""}</span>
    <input
      type={type}
      inputMode={inputMode}
      placeholder={placeholder}
      value={value}
      aria-invalid={Boolean(error)}
      onChange={(event) => {
        const next = format === "phone"
          ? formatPhone(event.currentTarget.value)
          : format === "personalNumber"
            ? formatPersonalNumber(event.currentTarget.value)
            : event.currentTarget.value;
        onChange(next);
      }}
    />
    {error ? <small className="cmp-mcommerce-error">{error}</small> : null}
  </label>
);

const Foot = ({ back, next, onBack, onNext, disabled, loading }: { back?: string; next: string; onBack: () => void; onNext: () => void; disabled?: boolean; loading?: boolean }) => (
  <footer className="cmp-mcommerce-foot">
    <button type="button" className="secondary" onClick={onBack}>{back ?? "Tillbaka"}</button>
    <button type="button" onClick={onNext} disabled={disabled} data-loading={loading ? "true" : undefined}>
      <span>{next}</span>
    </button>
  </footer>
);

const MobileCommerceFlow = ({ offers, model, storage, color, conditionAnswers, onBack }: MobileCommerceFlowProps) => {
  const [step, setStep] = useState<MobileCommerceStep>("results");
  const [selectedOffer, setSelectedOffer] = useState<CompanyOffer | null>(null);
  const [shipping, setShipping] = useState<"email" | "kit" | null>(null);
  const [payment, setPayment] = useState<PaymentMethod | null>(null);
  const [form, setForm] = useState(emptyCheckoutForm);
  const [paymentErrors, setPaymentErrors] = useState<CheckoutErrors>({});
  const [customerErrors, setCustomerErrors] = useState<CheckoutErrors>({});
  const [findMy, setFindMy] = useState(false);
  const [terms, setTerms] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const sortedOffers = useMemo(
    () => [...offers].filter((offer) => !offer.notPurchased).sort((a, b) => b.pris - a.pris),
    [offers],
  );
  const best = sortedOffers[0];
  const low = sortedOffers[sortedOffers.length - 1]?.pris ?? 0;
  const activeOffer = selectedOffer ?? best;
  const deviceImage = getIphoneImage(model, color);
  const checkoutPaymentOptions = useMemo(
    () => (activeOffer ? sortedPaymentMethods(activeOffer).map((method) => ({ id: methodId(method), label: paymentLabelFor(methodId(method)) })) : []),
    [activeOffer],
  );

  if (!best) return null;

  const setField = (field: CheckoutField, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
    setPaymentErrors((current) => ({ ...current, [field]: undefined }));
    setCustomerErrors((current) => ({ ...current, [field]: undefined }));
  };

  const goToCustomerStep = () => {
    const errors = validatePaymentDetails(payment, form);
    setPaymentErrors(errors);
    if (!hasErrors(errors)) setStep("co2");
  };

  const goToReviewStep = () => {
    const errors = validateCustomerDetails(form);
    setCustomerErrors(errors);
    if (!hasErrors(errors)) setStep("co3");
  };

  const shippingLabel = shipping === "email" ? "Fraktsedel via e-post" : "Gratis försäljningspaket";
  const paymentLabel = paymentLabelFor(payment);

  const finishOrder = async () => {
    if (!shipping || !payment || isSubmitting) return;

    setSubmitError("");
    setIsSubmitting(true);

    try {
      const payload = {
        model,
        storage,
        dealer_id: activeOffer.företag.toLowerCase().replace(/\s+/g, "-"),
        dealer_name: activeOffer.företag,
        price_sek: activeOffer.pris,
        shipping_option: shipping,
        shipping_label: shippingLabel,
        customer: {
          first_name: form.firstName.trim(),
          last_name: form.lastName.trim(),
          personal_number: form.personalNumber.trim(),
          address: form.address.trim(),
          postal_code: form.postalCode.trim(),
          city: form.city.trim(),
          phone: form.phone.trim(),
          email: form.email.trim(),
        },
        payment: {
          method: payment,
          label: paymentLabel,
          clearing_number: payment === "bank" ? form.clearingNumber.trim() : undefined,
          account_number: payment === "bank" ? form.accountNumber.trim() : undefined,
          swish_number: payment === "swish" ? form.swishNumber.trim() : undefined,
          paypal_email: payment === "paypal" ? form.paypalEmail.trim() : undefined,
        },
        condition_answers: conditionAnswers,
        source: "cashmyphone_web" as const,
      };
      const optimisticOrder = makeOptimisticOrder(payload);
      const outboundPayload = { ...payload, client_order_id: optimisticOrder.order_id };
      let resolvedOrder: Order | null = null;

      void submitOrder(outboundPayload)
        .then((response) => {
          resolvedOrder = response.order;
          sessionStorage.setItem("cashmyphone:last-order", JSON.stringify(response.order));
          setOrder(response.order);
        })
        .catch((error) => {
          if (import.meta.env.DEV) console.error("Fel vid orderregistrering i bakgrunden:", error);
        });

      await wait(ORDER_SUBMIT_ANIMATION_MS);

      const orderToShow = resolvedOrder ?? optimisticOrder;
      sessionStorage.setItem("cashmyphone:last-order", JSON.stringify(orderToShow));
      setOrder(orderToShow);
      setStep("done");
    } catch (error) {
      if (import.meta.env.DEV) console.error("Fel vid orderregistrering:", error);
      setSubmitError("Ordern kunde inte registreras just nu. Försök igen om en stund.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (step === "results") {
    return (
      <main className="cmp-mcommerce">
        <Head title="Ditt resultat" sub={`${model} · ${storage}`} onBack={onBack} />
        <section className="cmp-mcommerce-result-intro">
          <h1>Vi har hittat det <span>bästa budet<Squiggle /></span></h1>
        </section>

        <section className="cmp-mcommerce-result-body">
          <article className="cmp-mcommerce-winner">
            <div className="cmp-mcommerce-winner-top">
              <div className="cmp-mcommerce-winner-info">
                <p>bästa valet ↓</p>
                <h2>{best.företag}</h2>
                <TrustpilotBadge offer={best} />
              </div>
              <div className="cmp-mcommerce-winner-price">
                <small>DU FÅR</small>
                <strong>{fmt(best.pris)}<Squiggle /></strong>
                <em>SEK</em>
              </div>
            </div>
            <button type="button" onClick={() => { setSelectedOffer(best); setStep("co1"); }}>
              Sälj till {best.företag} →
            </button>
          </article>

          <div className="cmp-mcommerce-offers">
            {sortedOffers.map((offer) => {
              const diff = offer.pris - low;
              return (
                <article key={`${offer.företag}-${offer.pris}`}>
                  <div>
                    <h3>{offer.företag}</h3>
                    <div className="cmp-mcommerce-offer-meta">
                      <TrustpilotBadge offer={offer} compact />
                      <PaymentBadges offer={offer} />
                    </div>
                  </div>
                  <div>
                    <strong>{fmt(offer.pris)} kr</strong>
                    <span className={diff === 0 ? "low" : undefined}>{diff > 0 ? `+${fmt(diff)} kr` : "lägsta bud"}</span>
                  </div>
                  <button type="button" onClick={() => { setSelectedOffer(offer); setStep("co1"); }}>
                    Sälj
                  </button>
                </article>
              );
            })}
          </div>
        </section>
      </main>
    );
  }

  if (step === "co1") {
    return (
      <main className="cmp-mcommerce checkout">
        <Head title="Kassa" sub="Steg 1 av 3 · Leverans & betalning" onBack={() => setStep("results")} />
        <PayoutMini offer={activeOffer} model={model} storage={storage} payment={payment} />
        <StepDots step={0} />
        <section className="cmp-mcommerce-panel">
         
          <section className="cmp-mcommerce-option-box">
            <h2>Fraktalternativ</h2>
            <Pick selected={shipping === "email"} onClick={() => setShipping("email")} title="Fraktsedel via e-post" sub="Skriv ut och tejpa på paketet" />
            <Pick selected={shipping === "kit"} onClick={() => setShipping("kit")} title="Försäljningspaket" sub="Levereras till dig på 3-5 dagar" />
          </section>
          <section className="cmp-mcommerce-option-box">
            <h2>Betalningsalternativ</h2>
            {checkoutPaymentOptions.map((option) => (
              <div key={option.id} className={`cmp-mcommerce-choice ${payment === option.id ? "selected open" : ""}`}>
                <Pick
                  selected={payment === option.id}
                  onClick={() => { setPayment(option.id); setPaymentErrors({}); }}
                  title={option.label}
                  sub={paymentCopy(option.id, activeOffer.pris)}
                  icon={option.id === "paypal" ? <img className="cmp-mcommerce-pick-logo" src={paypalLogo} alt="" aria-hidden /> : undefined}
                  trail={option.id === "paypal" ? <FeeTrail amount={paypalFee(activeOffer.pris)} /> : undefined}
                />
                {payment === "swish" && option.id === "swish" ? (
                  <div className="cmp-mcommerce-nested">
                    <Field
                      label="Ditt Swish-nummer"
                      placeholder="070-123 45 67"
                      value={form.swishNumber}
                      onChange={(value) => setField("swishNumber", value)}
                      error={paymentErrors.swishNumber}
                      type="tel"
                      inputMode="numeric"
                      format="phone"
                      required
                    />
                  </div>
                ) : null}
                {payment === "bank" && option.id === "bank" ? (
                  <div className="cmp-mcommerce-nested two">
                    <Field
                      label="Clearingnummer"
                      placeholder="XXXX"
                      value={form.clearingNumber}
                      onChange={(value) => setField("clearingNumber", value)}
                      error={paymentErrors.clearingNumber}
                      inputMode="numeric"
                      required
                    />
                    <Field
                      label="Kontonummer"
                      placeholder="XXXXXXXXXX"
                      value={form.accountNumber}
                      onChange={(value) => setField("accountNumber", value)}
                      error={paymentErrors.accountNumber}
                      inputMode="numeric"
                      required
                    />
                  </div>
                ) : null}
                {payment === "paypal" && option.id === "paypal" ? (
                  <div className="cmp-mcommerce-nested">
                    <Field
                      label="PayPal-e-post"
                      placeholder="namn@example.com"
                      value={form.paypalEmail}
                      onChange={(value) => setField("paypalEmail", value)}
                      error={paymentErrors.paypalEmail}
                      type="email"
                      inputMode="email"
                      required
                    />
                  </div>
                ) : null}
              </div>
            ))}
          </section>
        </section>
        <Foot onBack={() => setStep("results")} onNext={goToCustomerStep} next="Dina uppgifter →" disabled={!shipping || !payment} />
      </main>
    );
  }

  if (step === "co2") {
    return (
      <main className="cmp-mcommerce checkout">
        <Head title="Kassa" sub="Steg 2 av 3 · Dina uppgifter" onBack={() => setStep("co1")} />
        <PayoutMini offer={activeOffer} model={model} storage={storage} payment={payment} />
        <StepDots step={1} />
        <section className="cmp-mcommerce-panel">
          <p className="cmp-mcommerce-info">ⓘ Personnumret delas bara med {activeOffer.företag} och behövs för utbetalningen.</p>
          <h2>Personlig information</h2>
          <div className="cmp-mcommerce-form-grid">
            <Field label="Förnamn" placeholder="Anna" value={form.firstName} onChange={(value) => setField("firstName", value)} error={customerErrors.firstName} required />
            <Field label="Efternamn" placeholder="Svensson" value={form.lastName} onChange={(value) => setField("lastName", value)} error={customerErrors.lastName} required />
            <Field label="Personnummer" placeholder="ÅÅÅÅMMDD-XXXX" value={form.personalNumber} onChange={(value) => setField("personalNumber", value)} error={customerErrors.personalNumber} inputMode="numeric" format="personalNumber" required />
            <Field label="E-post" placeholder="anna@mail.se" value={form.email} onChange={(value) => setField("email", value)} error={customerErrors.email} type="email" required />
            <Field label="Telefon" placeholder="070-123 45 67" value={form.phone} onChange={(value) => setField("phone", value)} error={customerErrors.phone} type="tel" inputMode="numeric" format="phone" required />
            <Field label="Gatuadress" placeholder="Storgatan 14" value={form.address} onChange={(value) => setField("address", value)} error={customerErrors.address} required />
            <Field label="Postnummer" placeholder="123 45" value={form.postalCode} onChange={(value) => setField("postalCode", value)} error={customerErrors.postalCode} inputMode="numeric" required />
            <Field label="Ort" placeholder="Stockholm" value={form.city} onChange={(value) => setField("city", value)} error={customerErrors.city} required />
          </div>
        </section>
        <Foot onBack={() => setStep("co1")} onNext={goToReviewStep} next="Granska →" />
      </main>
    );
  }

  if (step === "co3") {
    const rows = [
      ["Återförsäljare", activeOffer.företag],
      ["Enhet", `${model} · ${storage}`],
      ["Frakt", shippingLabel],
      ["Betalning", paymentLabel],
      ...(payment === "paypal" ? [["PayPal-avgift", `-${fmt(paypalFee(activeOffer.pris))} kr`]] : []),
      ["Du får", `${fmt(payoutAmount(activeOffer, payment))} kr`],
      ["Namn", `${form.firstName} ${form.lastName}`],
      ["Adress", `${form.address}, ${form.postalCode} ${form.city}`],
    ];
    return (
      <main className="cmp-mcommerce checkout">
        <Head title="Kassa" sub="Steg 3 av 3 · Granska" onBack={() => setStep("co2")} />
        <PayoutMini offer={activeOffer} model={model} storage={storage} payment={payment} />
        <StepDots step={2} />
        <section className="cmp-mcommerce-panel">
          <p className="cmp-mcommerce-info">Kontrollera att allt stämmer innan du slutför.</p>
          <div className="cmp-mcommerce-summary">
            {rows.map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <button type="button" className={`cmp-mcommerce-check ${findMy ? "on" : ""}`} onClick={() => setFindMy((value) => !value)}>
            <span>{findMy ? <Check aria-hidden /> : null}</span>
            Jag har avaktiverat Hitta min iPhone / mitt Google-konto
          </button>
          <button type="button" className={`cmp-mcommerce-check ${terms ? "on" : ""}`} onClick={() => setTerms((value) => !value)}>
            <span>{terms ? <Check aria-hidden /> : null}</span>
            Jag godkänner {activeOffer.företag}s och CashMyPhones köpvillkor
          </button>
          {submitError ? <p className="cmp-mcommerce-submit-error">{submitError}</p> : null}
        </section>
        <Foot onBack={() => setStep("co2")} onNext={finishOrder} next="Slutför beställning" disabled={!findMy || !terms || isSubmitting} loading={isSubmitting} />
      </main>
    );
  }

  return (
    <>
      <main className="cmp-mcommerce done">
        <header className="cmp-mcommerce-done-hero">
          <p>Klart! ↓</p>
          <h1>Tack, {form.firstName}!</h1>
          <span>Din order är registrerad. Vi skickar en bekräftelse till <strong>{form.email}</strong>.</span>
        </header>
        <section className="cmp-mcommerce-order-card">
          <div>
            <small>Ordernummer</small>
            <strong>{order?.order_id}</strong>
            <span>{new Date(order?.created_at ?? Date.now()).toLocaleDateString("sv-SE", { day: "numeric", month: "long", year: "numeric" })}</span>
          </div>
          <article>
            <div className="thumb">
              {deviceImage ? <img src={deviceImage} alt="" aria-hidden /> : null}
            </div>
            <div>
              <h2>{model}</h2>
              <p>{storage} · Säljs till {activeOffer.företag}</p>
            </div>
          </article>
          <dl>
            <div><dt>Fraktmetod</dt><dd>{shippingLabel}</dd></div>
            <div><dt>Betalning</dt><dd>{paymentLabel}</dd></div>
            {payment === "paypal" ? <div><dt>PayPal-avgift</dt><dd>-{fmt(paypalFee(activeOffer.pris))} kr</dd></div> : null}
            <div><dt>Beräknad utbetalning</dt><dd>4–5 dagar</dd></div>
          </dl>
          <footer><span>Du får utbetalt</span><strong>{fmt(payoutAmount(activeOffer, payment))} kr<Squiggle /></strong></footer>
        </section>
        <section className="cmp-mcommerce-timeline">
          {[
            { state: "done", title: "Bekräftelse", text: `Skickas till ${form.email} med dina orderuppgifter.`, icon: Mail },
            { state: "now", title: "Skriv ut & skicka enheten", text: "Tejpa fraktsedeln på paketet och lämna på närmaste ombud. Fri frakt.", icon: Package },
            { state: "todo", title: `${activeOffer.företag} granskar`, text: "1–2 arbetsdagar efter att paketet kommit fram. Du får besked via e-post.", icon: Shield },
            { state: "todo", title: "Pengarna kommer", text: `${fmt(payoutAmount(activeOffer, payment))} kr betalas ut via ${paymentLabel}, 4–5 dagar efter godkänd granskning.`, icon: WalletCards },
          ].map(({ state, title, text, icon: Icon }, index) => (
            <div key={title} className={state}>
              <span><Icon aria-hidden /></span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
                {index === 1 ? <button type="button">Skriv ut fraktsedel ↓</button> : null}
              </div>
            </div>
          ))}
        </section>
        <div className="cmp-mcommerce-done-actions">
          <button type="button" onClick={() => window.location.assign("/")}>Till startsidan</button>
        </div>
      </main>
      <SiteFooter />
    </>
  );
};

export default MobileCommerceFlow;
