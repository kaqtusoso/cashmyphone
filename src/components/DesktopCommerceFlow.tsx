import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Check, Landmark, Mail, Package, Shield, Star, WalletCards } from "lucide-react";

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
import "./DesktopCommerceFlow.css";

type CommerceStep = "results" | "co1" | "co2" | "co3" | "done";

interface DesktopCommerceFlowProps {
  offers: CompanyOffer[];
  model: string;
  storage: string;
  color?: string;
  conditionAnswers?: Record<string, unknown>;
  updated?: string;
  onBack: () => void;
}

const fmt = (value: number) => value.toLocaleString("sv-SE");
const ORDER_SUBMIT_ANIMATION_MS = 800;
const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

const Rating = ({ rating, dark = false }: { rating?: string; dark?: boolean }) => (
  <span className={`cmp-commerce-rating ${dark ? "dark" : ""}`}>
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
      <span className="cmp-commerce-trust-score">{prettyScore(offer.trustpilotScore)}{compact ? "/5" : ""}</span>
      {!compact ? (
        <span className="cmp-commerce-trust-stars" aria-hidden>
          {[0, 1, 2, 3, 4].map((index) => (
            <Star key={index} className={rating >= index + 0.75 ? "filled" : ""} />
          ))}
        </span>
      ) : null}
      {!compact ? <span className="cmp-commerce-trust-text">
        {prettyScore(offer.trustpilotScore)} av 5 ({offer.trustpilotReviews ?? "0"} omdömen)
      </span> : null}
    </>
  );

  if (!offer.trustpilotUrl) {
    return <span className={`cmp-commerce-trust-badge ${compact ? "compact" : ""}`}>{content}</span>;
  }

  return (
    <a className={`cmp-commerce-trust-badge ${compact ? "compact" : ""}`} href={offer.trustpilotUrl} target="_blank" rel="noreferrer">
      {content}
    </a>
  );
};

const PaymentBadges = ({ offer }: { offer: CompanyOffer }) => (
  <div className="cmp-commerce-payment-badges" aria-label={`Betalning: ${paymentMethods(offer).join(", ")}`}>
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

const Squiggle = () => (
  <svg className="cmp-commerce-squiggle" viewBox="0 0 200 12" preserveAspectRatio="none" aria-hidden>
    <path d="M3 8 C 45 3, 90 3, 130 6 S 185 9, 197 5" />
  </svg>
);

const StepDots = ({ step }: { step: number }) => {
  const labels = ["Leverans", "Uppgifter", "Granska"];
  return (
    <div className="cmp-commerce-stepdots">
      {labels.map((label, index) => (
        <div key={label} className={index === step ? "active" : index < step ? "done" : ""}>
          <strong>{index < step ? <Check aria-hidden /> : index + 1}{index === step ? <Squiggle /> : null}</strong>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
};

const PayoutHero = ({ offer, model, storage, payment, note }: { offer: CompanyOffer; model: string; storage: string; payment?: PaymentMethod | null; note?: string }) => (
  <>
    {note ? <p className="cmp-commerce-note">{note}</p> : null}
    <section className="cmp-commerce-payout">
      <div className="cmp-commerce-payout-info">
        <h2>{offer.företag}</h2>
        <TrustpilotBadge offer={offer} />
        <span>{model} · {storage}</span>
      </div>
      <div className="cmp-commerce-payout-price">
        <small>DU FÅR</small>
        <span><strong>{fmt(payoutAmount(offer, payment ?? null))}<Squiggle /></strong><em>SEK</em></span>
      </div>
    </section>
  </>
);

const FeeTrail = ({ amount }: { amount: number }) => (
  <span className="cmp-commerce-fee-trail">
    <strong>-{fmt(amount)} kr</strong>
    <em>(avgifter)</em>
  </span>
);

const Pick = ({ selected, title, text, icon, trail, onClick }: { selected: boolean; title: string; text: string; icon?: ReactNode; trail?: ReactNode; onClick: () => void }) => (
  <button type="button" className={`cmp-commerce-pick ${selected ? "selected" : ""}`} onClick={onClick}>
    <span>{selected ? <Check aria-hidden /> : null}</span>
    <div>
      <strong>{icon}{title}</strong>
      <p>{text}</p>
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
  <label className="cmp-commerce-field">
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
    {error ? <small className="cmp-commerce-error">{error}</small> : null}
  </label>
);

const Footer = ({ back, next, onBack, onNext, disabled, loading, hideArrow }: { back?: string; next: string; onBack: () => void; onNext: () => void; disabled?: boolean; loading?: boolean; hideArrow?: boolean }) => (
  <div className="cmp-commerce-foot">
    <button type="button" className="secondary" onClick={onBack}>← {back ?? "Tillbaka"}</button>
    <button type="button" onClick={onNext} disabled={disabled} data-loading={loading ? "true" : undefined}>
      <span>{next}{hideArrow ? "" : " →"}</span>
    </button>
  </div>
);

const CheckoutShell = ({
  step,
  note,
  offer,
  model,
  storage,
  payment,
  children,
}: {
  step: number;
  note?: string;
  offer: CompanyOffer;
  model: string;
  storage: string;
  payment?: PaymentMethod | null;
  children: ReactNode;
}) => (
  <main className="cmp-commerce-checkout">
    <PayoutHero offer={offer} model={model} storage={storage} payment={payment} note={note} />
    <StepDots step={step} />
    {children}
  </main>
);

const Timeline = ({ offer, email, paymentLabel, payment }: { offer: CompanyOffer; email: string; paymentLabel: string; payment: PaymentMethod | null }) => {
  const rows = [
    { state: "done", title: "Bekräftelse", text: `Skickas till ${email || "din e-post"} med dina orderuppgifter.`, icon: Mail },
    { state: "now", title: "Skriv ut & skicka enheten", text: "Tejpa fraktsedeln på paketet och lämna på närmaste ombud. Fri frakt.", icon: Package },
    { state: "todo", title: "Din mobil granskas", text: `${offer.företag} kontrollerar skicket på din mobil efter att de har tagit emot paketet.`, icon: Shield },
    { state: "todo", title: "Pengarna kommer", text: `${fmt(payoutAmount(offer, payment))} SEK betalas ut via ${paymentLabel} efter godkänd granskning.`, icon: WalletCards },
  ];

  return (
    <div className="cmp-commerce-timeline">
      {rows.map((row, index) => {
        const Icon = row.icon;
        return (
          <div key={row.title} className={row.state}>
            <span><Icon aria-hidden /></span>
            <div>
              <h3>{row.title}</h3>
              <p>{row.text}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const DesktopCommerceFlow = ({ offers, model, storage, color, conditionAnswers, updated, onBack }: DesktopCommerceFlowProps) => {
  const [step, setStep] = useState<CommerceStep>("results");
  const [selectedOffer, setSelectedOffer] = useState<CompanyOffer | null>(null);
  const [shipping, setShipping] = useState<"email" | "pkg" | null>(null);
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
      <main className="cmp-commerce cmp-commerce-results">
        <div className="cmp-commerce-results-head">
          <button type="button" className="cmp-commerce-back" onClick={onBack}>← Tillbaka</button>
          <p className="cmp-commerce-kicker">Du värderade <strong>{model} · {storage}</strong></p>
          <h1>Vi hittade det <span>bästa budet<Squiggle /></span> för din mobil</h1>
        </div>

        <div className="cmp-commerce-results-grid">
          <section className="cmp-commerce-results-stack">
            <div className="cmp-commerce-winner">
              <div className="cmp-commerce-winner-info">
                <p>bästa valet ↓</p>
                <h2>{best.företag}</h2>
                <TrustpilotBadge offer={best} />
              </div>
              <div className="cmp-commerce-winner-action">
                <div className="cmp-commerce-winner-price">
                  <small>DU FÅR</small>
                  <strong>{fmt(best.pris)}<Squiggle /></strong>
                  <em>SEK</em>
                </div>
                <button type="button" onClick={() => { setSelectedOffer(best); setStep("co1"); }}>
                  Sälj till {best.företag} →
                </button>
              </div>
            </div>

            <div className="cmp-commerce-offers">
              {sortedOffers.map((offer) => {
                const diff = offer.pris - low;
                return (
                  <article key={`${offer.företag}-${offer.pris}`}>
                    <div>
                      <h3>{offer.företag}</h3>
                      <div className="cmp-commerce-offer-meta">
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
            {updated ? <p className="cmp-commerce-updated">Priser hämtade: {updated}</p> : null}
          </section>
        </div>
      </main>
    );
  }

  if (step === "co1") {
    return (
      <div className="cmp-commerce">
        <CheckoutShell step={0} note="" offer={activeOffer} model={model} storage={storage} payment={payment}>
          <section className="cmp-commerce-option-box">
            <h2 className="cmp-commerce-hand">Fraktalternativ</h2>
            <Pick selected={shipping === "email"} onClick={() => setShipping("email")} title="Fraktsedel via e-post" text="Skriv ut och tejpa på paketet" />
            <Pick selected={shipping === "pkg"} onClick={() => setShipping("pkg")} title="Försäljningspaket" text="Levereras till dig på 3–5 dagar" />
          </section>
          <section className="cmp-commerce-option-box">
            <h2 className="cmp-commerce-hand">Betalningsalternativ</h2>
            {checkoutPaymentOptions.map((option) => (
              <div key={option.id} className={`cmp-commerce-choice ${payment === option.id ? "selected open" : ""}`}>
                <Pick
                  selected={payment === option.id}
                  onClick={() => { setPayment(option.id); setPaymentErrors({}); }}
                  title={option.label}
                  text={paymentCopy(option.id, activeOffer.pris)}
                  icon={option.id === "paypal" ? <img className="cmp-commerce-pick-logo" src={paypalLogo} alt="" aria-hidden /> : undefined}
                  trail={option.id === "paypal" ? <FeeTrail amount={paypalFee(activeOffer.pris)} /> : undefined}
                />
                {payment === "swish" && option.id === "swish" ? (
                  <div className="cmp-commerce-nested">
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
                  <div className="cmp-commerce-nested two">
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
                  <div className="cmp-commerce-nested">
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
          <Footer onBack={() => setStep("results")} onNext={goToCustomerStep} next="Dina uppgifter" disabled={!shipping || !payment} />
        </CheckoutShell>
      </div>
    );
  }

  if (step === "co2") {
    return (
      <div className="cmp-commerce">
        <CheckoutShell step={1} offer={activeOffer} model={model} storage={storage} payment={payment}>
          <p className="cmp-commerce-info">ⓘ Personnumret delas bara med {activeOffer.företag} och behövs för utbetalningen.</p>
          <h2 className="cmp-commerce-hand">Personlig information</h2>
          <div className="cmp-commerce-formgrid">
            <Field label="Förnamn" placeholder="Anna" value={form.firstName} onChange={(value) => setField("firstName", value)} error={customerErrors.firstName} required />
            <Field label="Efternamn" placeholder="Svensson" value={form.lastName} onChange={(value) => setField("lastName", value)} error={customerErrors.lastName} required />
            <Field label="Personnummer" placeholder="ÅÅÅÅMMDD-XXXX" value={form.personalNumber} onChange={(value) => setField("personalNumber", value)} error={customerErrors.personalNumber} inputMode="numeric" format="personalNumber" required />
            <Field label="E-post" placeholder="anna@mail.se" value={form.email} onChange={(value) => setField("email", value)} error={customerErrors.email} type="email" required />
            <Field label="Telefon" placeholder="070-123 45 67" value={form.phone} onChange={(value) => setField("phone", value)} error={customerErrors.phone} type="tel" inputMode="numeric" format="phone" required />
            <Field label="Gatuadress" placeholder="Storgatan 14" value={form.address} onChange={(value) => setField("address", value)} error={customerErrors.address} required />
            <Field label="Postnummer" placeholder="123 45" value={form.postalCode} onChange={(value) => setField("postalCode", value)} error={customerErrors.postalCode} inputMode="numeric" required />
            <Field label="Ort" placeholder="Stockholm" value={form.city} onChange={(value) => setField("city", value)} error={customerErrors.city} required />
          </div>
          <Footer onBack={() => setStep("co1")} onNext={goToReviewStep} next="Granska" />
        </CheckoutShell>
      </div>
    );
  }

  if (step === "co3") {
    const rows = [
      ["Enhet", `${model} · ${storage}`],
      ["Köpare", activeOffer.företag],
      ["Frakt", shippingLabel],
      ["Betalning", paymentLabel],
      ...(payment === "paypal"
        ? [
            ["PayPal-avgift", `-${fmt(paypalFee(activeOffer.pris))} kr`],
            ["Efter avgift", `${fmt(payoutAmount(activeOffer, payment))} kr`],
          ]
        : []),
      ["Namn", `${form.firstName} ${form.lastName}`],
      ["Adress", `${form.address}, ${form.postalCode} ${form.city}`],
    ];
    return (
      <div className="cmp-commerce">
        <CheckoutShell step={2} offer={activeOffer} model={model} storage={storage} payment={payment}>
          <h2 className="cmp-commerce-hand">Stämmer allt?</h2>
          <div className="cmp-commerce-summary">
            {rows.map(([label, value]) => (
              <div key={label}><span>{label}</span><strong>{value}</strong></div>
            ))}
          </div>
          <button type="button" className={`cmp-commerce-check ${findMy ? "on" : ""}`} onClick={() => setFindMy((value) => !value)}>
            <span>{findMy ? <Check aria-hidden /> : null}</span>Jag har avaktiverat Hitta min iPhone / mitt Google-konto
          </button>
          <button type="button" className={`cmp-commerce-check ${terms ? "on" : ""}`} onClick={() => setTerms((value) => !value)}>
            <span>{terms ? <Check aria-hidden /> : null}</span>Jag godkänner {activeOffer.företag}s och CashMyPhones köpvillkor
          </button>
          {submitError ? <p className="cmp-commerce-submit-error">{submitError}</p> : null}
          <Footer
            onBack={() => setStep("co2")}
            onNext={finishOrder}
            next="Slutför"
            disabled={!findMy || !terms || isSubmitting}
            loading={isSubmitting}
            hideArrow={isSubmitting}
          />
        </CheckoutShell>
      </div>
    );
  }

  return (
    <>
      <main className="cmp-commerce cmp-commerce-done">
        <header>
          <p>Klart! ↓</p>
          <h1>Tack, {form.firstName}!</h1>
          <span>Din order är registrerad. Vi skickar en bekräftelse till <strong>{form.email}</strong>.</span>
        </header>
        <div className="cmp-commerce-done-grid">
          <section className="cmp-commerce-order-card">
            <div>
              <div>
                <small>Ordernummer</small>
                <strong>{order?.order_id}</strong>
                <span>{new Date(order?.created_at ?? Date.now()).toLocaleDateString("sv-SE", { day: "numeric", month: "long", year: "numeric" })}</span>
              </div>
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
          <section>
            <Timeline offer={activeOffer} email={form.email} paymentLabel={paymentLabel} payment={payment} />
            <div className="cmp-commerce-done-actions">
              <button type="button" onClick={() => window.location.assign("/")}>Till startsidan</button>
            </div>
          </section>
        </div>
      </main>
      <SiteFooter />
    </>
  );
};

export default DesktopCommerceFlow;
