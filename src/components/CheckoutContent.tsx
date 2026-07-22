import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { Check, Info } from "lucide-react";
import TermsDialog from "@/components/TermsDialog";
import { useSavedOffers } from "@/hooks/useSavedOffers";
import { formatPersonalNumber } from "@/utils/checkoutValidation";
import { getIphoneColorLabel } from "@/utils/iphoneImage";
import { makeOptimisticOrder, pendingOrderIntegrations, submitOrder as submitOrderRequest } from "@/utils/orders";
import { dealerConfig, requiresPersonalNumber } from "@/utils/vendorCheckout";
import { trackEvent, trackStepView } from "@/utils/tracking";

export { dealerConfig } from "@/utils/vendorCheckout";

// =====================
// Schema & Types
// =====================

const checkoutSchema = z
  .object({
    shippingOption: z.string().optional(),
    firstName: z.string().min(1, "Förnamn krävs"),
    lastName: z.string().min(1, "Efternamn krävs"),
    personalNumber: z
      .string()
      .optional()
      .refine((value) => !value || /^\d{8}-?\d{4}$/.test(value), "Ogiltigt personnummer (ÅÅÅÅMMDD-XXXX)"),
    address: z.string().min(1, "Gatuadress krävs"),
    postalCode: z.string().min(1, "Postnummer krävs"),
    city: z.string().min(1, "Stad krävs"),
    phone: z.string().min(1, "Telefonnummer krävs"),
    email: z.string().email("Ogiltig e-postadress"),
    paymentMethod: z.string().optional(),
    clearingNumber: z.string().optional(),
    accountNumber: z.string().optional(),
    ibanNumber: z.string().optional(),
    swishNumber: z.string().optional(),
    paypalEmail: z.string().optional(),
    findMyIphoneDisabled: z.boolean().optional(),
    termsAccepted: z.boolean().optional(),
  })
  .superRefine((data, ctx) => {
    if (data.paymentMethod === "bank-iban" && !data.ibanNumber) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "IBAN-nummer krävs", path: ["ibanNumber"] });
    }
    if (data.paymentMethod === "bank" && !data.clearingNumber) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Clearingnummer krävs", path: ["clearingNumber"] });
    }
    if (data.paymentMethod === "bank" && !data.accountNumber) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Kontonummer krävs", path: ["accountNumber"] });
    }
    if (data.paymentMethod === "swish" && !data.swishNumber) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Swish-nummer krävs", path: ["swishNumber"] });
    }
    if (data.paymentMethod === "paypal" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.paypalEmail || "")) {
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: "PayPal-e-post krävs", path: ["paypalEmail"] });
    }
  });

type CheckoutFormData = z.infer<typeof checkoutSchema>;

const paypalFee = (priceSek: number) => (priceSek >= 5000 ? 100 : Math.round(priceSek * 0.02));
const ORDER_SUBMIT_ANIMATION_MS = 800;
const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));
const CHECKOUT_STEP_SLUGS: Record<number, string> = {
  1: "uppgifter",
  2: "frakt-betalning",
  3: "bekrafta",
};

// =====================
// Props
// =====================

export interface CheckoutContentProps {
  dealer: string;
  model: string;
  storage: string;
  color?: string;
  price: string;
  conditionAnswers?: Record<string, unknown>;
  savedOfferId?: string;
  compact?: boolean;
  showRestoredBanner?: boolean;
  initialStep?: number;
}

// =====================
// Component
// =====================

const CheckoutContent = ({
  dealer,
  model,
  storage,
  color,
  price,
  conditionAnswers,
  savedOfferId,
  compact = false,
  showRestoredBanner = false,
  initialStep = 1,
}: CheckoutContentProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { removeSavedOffer } = useSavedOffers();
  const config = dealerConfig[dealer] || dealerConfig.swappie;
  const priceSek = parseInt(price || "0", 10);

  const [currentStep, setCurrentStep] = useState(initialStep);
  const [useSamePhoneForSwish, setUseSamePhoneForSwish] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showTeleveraTerms, setShowTeleveraTerms] = useState(false);
  const [showVendorTerms, setShowVendorTerms] = useState(false);
  const [showPersonalNumberInfo, setShowPersonalNumberInfo] = useState(false);
  const [selectedStore, setSelectedStore] = useState("");
  const viewedAtRef = useRef(Date.now());

  useEffect(() => {
    if (!compact) window.scrollTo({ top: 0, behavior: "instant" });
  }, [currentStep, compact]);

  useEffect(() => {
    if (compact) return;
    setCurrentStep(initialStep);
  }, [compact, initialStep]);

  useEffect(() => {
    if (compact) return;
    const slug = CHECKOUT_STEP_SLUGS[currentStep];
    const target = `/checkout/${slug}${location.search}`;
    if (`${location.pathname}${location.search}` !== target) {
      navigate(target, { replace: true });
    }
  }, [compact, currentStep, location.pathname, location.search, navigate]);

  useEffect(() => {
    viewedAtRef.current = Date.now();
    trackStepView("checkout_step_viewed", {
      funnel: "checkout",
      surface: compact ? "compact" : "page",
      step: currentStep,
      checkout_step: CHECKOUT_STEP_SLUGS[currentStep],
      model,
      storage,
      dealer: config.name,
      price: priceSek,
    });
  }, [compact, config.name, currentStep, model, priceSek, storage]);

  const {
    register,
    watch,
    setValue,
    setError,
    clearErrors,
    trigger,
    getValues,
    formState: { errors, submitCount },
  } = useForm<CheckoutFormData>({
    resolver: zodResolver(checkoutSchema),
    mode: "onSubmit",
    reValidateMode: "onSubmit",
    defaultValues: { findMyIphoneDisabled: false, termsAccepted: false },
  });

  const findMyIphoneDisabled = watch("findMyIphoneDisabled");
  const termsAccepted = watch("termsAccepted");
  const selectedPaymentMethod = watch("paymentMethod");
  const showPersonalNumberInCustomerStep = config.personalNumberRequirement === "always";
  const showPersonalNumberInSwishStep = config.personalNumberRequirement === "swish";
  const selectedShippingOption = config.shippingOptions.find((option) => option.id === watch("shippingOption"));
  const requiresStoreSelection = Boolean(selectedShippingOption?.stores?.length);
  const shippingFeeSek = selectedShippingOption?.feeSek ?? 0;
  const showErrors = submitCount > 0;

  const stepTitles = ["Nästa steg", "Frakt & betalning", "Bekräfta din beställning"];

  const nextStep = async () => {
    if (currentStep === 1) {
      if (!showPersonalNumberInCustomerStep) clearErrors("personalNumber");
      const isValid = await trigger(
        [
          "firstName",
          "lastName",
          ...(showPersonalNumberInCustomerStep ? (["personalNumber"] as const) : []),
          "address",
          "postalCode",
          "city",
          "phone",
          "email",
        ],
        { shouldFocus: false },
      );
      if (!isValid) {
        trackEvent("validation_error", {
          funnel: "checkout",
          surface: compact ? "compact" : "page",
          step: 1,
          checkout_step: CHECKOUT_STEP_SLUGS[1],
          fields: Object.keys(errors).join(","),
          model,
          storage,
          dealer: config.name,
        });
        toast.error("Vänligen fyll i alla obligatoriska fält");
        return;
      }
      trackEvent("checkout_step_completed", {
        funnel: "checkout",
        surface: compact ? "compact" : "page",
        step: 1,
        checkout_step: CHECKOUT_STEP_SLUGS[1],
        model,
        storage,
        dealer: config.name,
        duration_ms: Date.now() - viewedAtRef.current,
      });
      setCurrentStep(2);
      return;
    }

    if (currentStep === 2) {
      if (!watch("shippingOption")) {
        trackEvent("validation_error", {
          funnel: "checkout",
          surface: compact ? "compact" : "page",
          step: 2,
          checkout_step: CHECKOUT_STEP_SLUGS[2],
          fields: "shippingOption",
          model,
          storage,
          dealer: config.name,
        });
        toast.error("Välj ett fraktalternativ");
        return;
      }
      if (requiresStoreSelection && !selectedStore) {
        trackEvent("validation_error", {
          funnel: "checkout",
          surface: compact ? "compact" : "page",
          step: 2,
          checkout_step: CHECKOUT_STEP_SLUGS[2],
          fields: "selectedStore",
          model,
          storage,
          dealer: config.name,
        });
        toast.error("Välj butik för inlämning");
        return;
      }
      if (!watch("paymentMethod")) {
        trackEvent("validation_error", {
          funnel: "checkout",
          surface: compact ? "compact" : "page",
          step: 2,
          checkout_step: CHECKOUT_STEP_SLUGS[2],
          fields: "paymentMethod",
          model,
          storage,
          dealer: config.name,
        });
        toast.error("Välj en betalningsmetod");
        return;
      }

      const fields: (keyof CheckoutFormData)[] = [];
      const pm = watch("paymentMethod");
      if (pm === "bank") fields.push("clearingNumber", "accountNumber");
      if (pm === "bank-iban") fields.push("ibanNumber");
      if (pm === "swish") fields.push("swishNumber");
      if (pm === "paypal") fields.push("paypalEmail");
      if (requiresPersonalNumber(config, pm) && !fields.includes("personalNumber")) fields.push("personalNumber");

      if (fields.length) {
        const ok = await trigger(fields, { shouldFocus: false });
        if (!ok) {
          trackEvent("validation_error", {
            funnel: "checkout",
            surface: compact ? "compact" : "page",
            step: 2,
            checkout_step: CHECKOUT_STEP_SLUGS[2],
            fields: fields.join(","),
            model,
            storage,
            dealer: config.name,
          });
          toast.error("Vänligen fyll i alla obligatoriska fält");
          return;
        }
      }

      if (requiresPersonalNumber(config, pm) && !/^\d{8}-?\d{4}$/.test(watch("personalNumber") || "")) {
        setError("personalNumber", {
          type: "manual",
          message: "Personnummer krävs för vald betalningsmetod.",
        });
        trackEvent("validation_error", {
          funnel: "checkout",
          surface: compact ? "compact" : "page",
          step: 2,
          checkout_step: CHECKOUT_STEP_SLUGS[2],
          fields: "personalNumber",
          model,
          storage,
          dealer: config.name,
        });
        toast.error("Vänligen fyll i personnummer");
        return;
      }

      trackEvent("checkout_step_completed", {
        funnel: "checkout",
        surface: compact ? "compact" : "page",
        step: 2,
        checkout_step: CHECKOUT_STEP_SLUGS[2],
        model,
        storage,
        dealer: config.name,
        payment_method: pm,
        shipping_option: watch("shippingOption"),
        duration_ms: Date.now() - viewedAtRef.current,
      });
      setCurrentStep(3);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const paypalFeeSek = paypalFee(priceSek);
  const selectedPaypalFeeSek = selectedPaymentMethod === "paypal" ? paypalFeeSek : 0;
  const netPayoutSek = Math.max(0, priceSek - selectedPaypalFeeSek - shippingFeeSek);
  const paypalNetSek = Math.max(0, priceSek - paypalFeeSek - shippingFeeSek);
  const estimatedPrice = price ? `${price} kr` : "–";
  const shippingDisplayLabel = selectedStore
    ? `${selectedShippingOption?.label}: ${selectedStore}`
    : selectedShippingOption?.label;

  const submitOrder = async (data: CheckoutFormData) => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      const shipping = config.shippingOptions.find((option) => option.id === data.shippingOption);
      const submitShippingFeeSek = shipping?.feeSek ?? 0;
      const submitPaypalFeeSek = data.paymentMethod === "paypal" ? paypalFee(parseInt(price || "0", 10)) : 0;
      const shippingLabel = selectedStore ? `${shipping?.label || data.shippingOption}: ${selectedStore}` : shipping?.label || data.shippingOption || "";
      const payment = config.paymentOptions.find((option) => option.id === data.paymentMethod);
      const payload = {
        model,
        storage,
        color: getIphoneColorLabel(model, color),
        dealer_id: dealer,
        dealer_name: config.name,
        price_sek: Math.max(0, parseInt(price || "0", 10) - submitPaypalFeeSek - submitShippingFeeSek),
        shipping_option: data.shippingOption || "",
        shipping_label: shippingLabel,
        customer: {
          first_name: data.firstName,
          last_name: data.lastName,
          personal_number: data.personalNumber,
          address: data.address,
          postal_code: data.postalCode,
          city: data.city,
          phone: data.phone,
          email: data.email,
        },
        payment: {
          method: data.paymentMethod || "",
          label: payment?.label || data.paymentMethod || "",
          clearing_number: data.clearingNumber,
          account_number: data.accountNumber,
          iban_number: data.ibanNumber,
          swish_number: data.swishNumber,
          paypal_email: data.paypalEmail,
        },
        condition_answers: conditionAnswers,
        source: "televera_web" as const,
      };
      const optimisticOrder = makeOptimisticOrder(payload);
      const outboundPayload = { ...payload, client_order_id: optimisticOrder.order_id };
      let resolvedOrder = optimisticOrder;

      void submitOrderRequest(outboundPayload)
        .then((response) => {
          resolvedOrder = response.order;
          sessionStorage.setItem("televera:last-order", JSON.stringify(response.order));
        })
        .catch((error) => {
          if (import.meta.env.DEV) console.error("Fel vid orderregistrering i bakgrunden:", error);
        });

      await wait(ORDER_SUBMIT_ANIMATION_MS);

      sessionStorage.setItem("televera:last-order", JSON.stringify(resolvedOrder));
      if (savedOfferId) removeSavedOffer(savedOfferId);
      trackEvent("order_submitted", {
        funnel: "checkout",
        surface: compact ? "compact" : "page",
        model,
        storage,
        dealer: config.name,
        price: payload.price_sek,
        payment_method: data.paymentMethod,
        shipping_option: data.shippingOption,
      });

      navigate("/summary", {
        state: {
          order: resolvedOrder,
          integrations: pendingOrderIntegrations(),
        },
      });
    } catch (err) {
      if (import.meta.env.DEV) console.error("Fel vid inskick:", err);
      toast.error("Ordern kunde inte registreras", {
        description: "Försök igen om en stund eller kontakta oss så hjälper vi dig.",
      });
      setIsSubmitting(false);
    }
  };

  const outerClass = compact ? "" : "max-w-7xl mx-auto";

  return (
    <>
      <div className={outerClass}>
        {showRestoredBanner && (
          <div className="bg-primary/10 border border-primary/30 rounded-xl p-4 mb-8 flex items-center gap-3 animate-fade-in">
            <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
              <Check className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-foreground">Återställd från sparad värdering</p>
              <p className="text-sm text-muted-foreground">
                Vi har fyllt i information från din tidigare värdering av {model} {storage}
              </p>
            </div>
          </div>
        )}

        <div className="mb-5">
          <h2 className="text-2xl font-bold mb-3 text-foreground">{stepTitles[currentStep - 1]}</h2>
          <div className="flex gap-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-1.5 flex-1 rounded-full transition-colors duration-300 ${
                  currentStep >= s ? "bg-primary" : "bg-muted"
                }`}
              />
            ))}
          </div>
        </div>

        <form>
          <div className={compact ? "space-y-4" : "grid lg:grid-cols-3 gap-8"}>
            <div className={compact ? "space-y-4" : "lg:col-span-2 space-y-4"}>
              {currentStep === 1 && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      ["firstName", "Förnamn"],
                      ["lastName", "Efternamn"],
                    ].map(([id, label]) => (
                      <div key={id} className="space-y-1">
                        <Label htmlFor={id} className="text-sm">
                          {label}
                        </Label>
                        <Input id={id} className="h-10" {...register(id as keyof CheckoutFormData)} />
                        {showErrors && errors[id as keyof CheckoutFormData] && (
                          <p className="text-xs text-destructive">
                            {errors[id as keyof CheckoutFormData]?.message as string}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>

                  {showPersonalNumberInCustomerStep && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5">
                        <Label htmlFor="personalNumber" className="text-sm">
                          Personnummer
                        </Label>

                        <div className="relative inline-flex">
                          <button
                            type="button"
                            aria-label="Information om personnummer"
                            aria-expanded={showPersonalNumberInfo}
                            onClick={() => setShowPersonalNumberInfo((open) => !open)}
                            onBlur={() => setTimeout(() => setShowPersonalNumberInfo(false), 120)}
                            className="inline-flex items-center justify-center text-muted-foreground hover:text-foreground focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-full"
                          >
                            <Info className="w-3.5 h-3.5" />
                          </button>

                          {showPersonalNumberInfo && (
                            <div className="absolute left-1/2 top-full z-50 mt-2 w-72 -translate-x-1/2 rounded-lg border border-border bg-popover p-3 text-xs leading-relaxed text-popover-foreground shadow-lg">
                              Ditt personnummer delas endast med den återförsäljare du har valt och behandlas enligt GDPR.
                            </div>
                          )}
                        </div>
                      </div>

                      <Input
                        id="personalNumber"
                        inputMode="numeric"
                        placeholder="ÅÅÅÅMMDD-XXXX"
                        className="h-10"
                        {...register("personalNumber", {
                          onChange: (event) => {
                            setValue("personalNumber", formatPersonalNumber(event.currentTarget.value), { shouldValidate: showErrors });
                          },
                        })}
                      />
                      {showErrors && errors.personalNumber && (
                        <p className="text-xs text-destructive">{errors.personalNumber.message}</p>
                      )}
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label htmlFor="email" className="text-sm">
                        E-post
                      </Label>
                      <Input id="email" type="email" className="h-10" {...register("email")} />
                      {showErrors && errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="phone" className="text-sm">
                        Telefon
                      </Label>
                      <Input id="phone" type="tel" inputMode="tel" className="h-10" {...register("phone")} />
                      {showErrors && errors.phone && <p className="text-xs text-destructive">{errors.phone.message}</p>}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label htmlFor="address" className="text-sm">
                      Gatuadress
                    </Label>
                    <Input id="address" className="h-10" {...register("address")} />
                    {showErrors && errors.address && (
                      <p className="text-xs text-destructive">{errors.address.message}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label htmlFor="postalCode" className="text-sm">
                        Postnummer
                      </Label>
                      <Input id="postalCode" className="h-10" {...register("postalCode")} />
                      {showErrors && errors.postalCode && (
                        <p className="text-xs text-destructive">{errors.postalCode.message}</p>
                      )}
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="city" className="text-sm">
                        Ort
                      </Label>
                      <Input id="city" className="h-10" {...register("city")} />
                      {showErrors && errors.city && <p className="text-xs text-destructive">{errors.city.message}</p>}
                    </div>
                  </div>
                </div>
              )}

              {currentStep === 2 && (
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm mb-2 block">Fraktmetod</Label>
                    <div className="grid sm:grid-cols-2 gap-2">
                      {config.shippingOptions.map((option) => {
                        const selected = watch("shippingOption") === option.id;
                        return (
                          <div
                            key={option.id}
                            className={`rounded-lg border-2 transition-all ${
                              selected ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
                            }`}
                          >
                            <button
                              type="button"
                              onClick={() => {
                                setValue("shippingOption", selected ? "" : option.id);
                                setSelectedStore("");
                              }}
                              className="w-full text-left p-3"
                            >
                              <p className="font-semibold text-sm">{option.label}</p>
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  {option.features?.length ? (
                                    <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                                      {option.features.map((feature) => (
                                        <li key={feature} className="flex items-center gap-1.5">
                                          <Check className="h-3.5 w-3.5 text-primary" />
                                          <span className="font-normal">{feature}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  ) : null}
                                </div>
                                {option.feeSek ? (
                                  <span className="shrink-0 text-right text-xs font-semibold text-destructive">
                                    -{option.feeSek.toLocaleString("sv-SE")} kr
                                    <span className="block font-normal text-muted-foreground">({option.feeLabel})</span>
                                  </span>
                                ) : null}
                              </div>
                            </button>
                            {selected && option.stores?.length ? (
                              <div className="border-t border-primary/20 bg-primary/5 p-3">
                                <Label className="text-sm mb-2 block">Välj butik</Label>
                                <div className="grid gap-2 max-h-64 overflow-auto pr-1">
                                  {option.stores.map((store) => (
                                    <button
                                      type="button"
                                      key={store}
                                      onClick={() => setSelectedStore(store)}
                                      className={`text-left rounded-md border px-3 py-2 text-xs transition-all ${
                                        selectedStore === store
                                          ? "border-primary bg-primary/10 text-foreground"
                                          : "border-border bg-background hover:border-primary/50"
                                      }`}
                                    >
                                      {store}
                                    </button>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm mb-2 block">Betalningsmetod</Label>
                    <div className="space-y-2">
                      {config.paymentOptions.map((option) => {
                        const selected = watch("paymentMethod") === option.id;
                        return (
                          <div
                            key={option.id}
                            className={`rounded-lg border-2 transition-all ${
                              selected ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
                            }`}
                          >
                            <button
                              type="button"
                              onClick={() => setValue("paymentMethod", selected ? "" : option.id)}
                              className="w-full flex items-center justify-between p-3 text-left"
                            >
                              <div>
                                <p className="font-semibold text-sm">{option.label}</p>
                                <p className="text-xs text-muted-foreground">
                                  {option.id === "bank"
                                    ? "Pengar direkt till ditt bankkonto"
                                    : option.id === "bank-iban"
                                      ? "Pengar till bankkonto via IBAN"
                                      : option.id === "paypal"
                                        ? `Avgift ${priceSek >= 5000 ? "100 kr" : "2%"} dras från utbetalningen`
                                        : "Snabb utbetalning via Swish"}
                                </p>
                              </div>
                              <div
                                className={`w-5 h-5 border-2 rounded-full flex items-center justify-center ${
                                  selected ? "border-primary bg-primary" : "border-muted-foreground/30"
                                }`}
                              >
                                {selected && <div className="w-2 h-2 bg-white rounded-full" />}
                              </div>
                            </button>

                            {selected && (
                              <div className="px-3 pb-3 border-t pt-3 space-y-2">
                                {option.id === "bank" && (
                                  <div className="grid grid-cols-2 gap-2">
                                    <div className="space-y-1">
                                      <Label className="text-xs">Clearingnummer</Label>
                                      <Input className="h-9" {...register("clearingNumber")} placeholder="XXXX" />
                                      {showErrors && errors.clearingNumber && (
                                        <p className="text-xs text-destructive">{errors.clearingNumber.message}</p>
                                      )}
                                    </div>
                                    <div className="space-y-1">
                                      <Label className="text-xs">Kontonummer</Label>
                                      <Input className="h-9" {...register("accountNumber")} placeholder="XXXXXXXXXX" />
                                      {showErrors && errors.accountNumber && (
                                        <p className="text-xs text-destructive">{errors.accountNumber.message}</p>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {option.id === "bank-iban" && (
                                  <div className="space-y-1">
                                    <Label className="text-xs">IBAN-nummer</Label>
                                    <Input
                                      className="h-9"
                                      {...register("ibanNumber")}
                                      placeholder="SE00 0000 0000 0000 0000 0000"
                                    />
                                    {showErrors && errors.ibanNumber && (
                                      <p className="text-xs text-destructive">{errors.ibanNumber.message}</p>
                                    )}
                                  </div>
                                )}

                                {option.id === "swish" && (
                                  <div className="space-y-2">
                                    <div className="space-y-1">
                                      <Label className="text-xs">Swish-nummer</Label>
                                      <Input
                                        className="h-9"
                                        {...register("swishNumber")}
                                        placeholder="07XXXXXXXX"
                                        disabled={useSamePhoneForSwish}
                                      />
                                    </div>
                                    <div className="flex items-center space-x-2">
                                      <Checkbox
                                        id="useSamePhone"
                                        checked={useSamePhoneForSwish}
                                        onCheckedChange={(checked) => {
                                          const isChecked = checked as boolean;
                                          setUseSamePhoneForSwish(isChecked);
                                          setValue("swishNumber", isChecked ? watch("phone") || "" : "");
                                        }}
                                        className="rounded-[5px]"
                                      />
                                      <Label htmlFor="useSamePhone" className="text-xs font-normal cursor-pointer">
                                        Samma som telefonnummer
                                      </Label>
                                    </div>
                                    {showErrors && errors.swishNumber && (
                                      <p className="text-xs text-destructive">{errors.swishNumber.message}</p>
                                    )}
                                    {showPersonalNumberInSwishStep && (
                                      <div className="space-y-1">
                                        <Label className="text-xs">Personnummer</Label>
                                        <Input
                                          inputMode="numeric"
                                          placeholder="ÅÅÅÅMMDD-XXXX"
                                          className="h-9"
                                          {...register("personalNumber", {
                                            onChange: (event) => {
                                              setValue("personalNumber", formatPersonalNumber(event.currentTarget.value), { shouldValidate: showErrors });
                                            },
                                          })}
                                        />
                                        {showErrors && errors.personalNumber && (
                                          <p className="text-xs text-destructive">{errors.personalNumber.message}</p>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                )}

                                {option.id === "paypal" && (
                                  <div className="space-y-2">
                                    <div className="space-y-1">
                                      <Label className="text-xs">PayPal-e-post</Label>
                                      <Input
                                        className="h-9"
                                        {...register("paypalEmail")}
                                        placeholder="namn@example.com"
                                        type="email"
                                      />
                                      {showErrors && errors.paypalEmail && (
                                        <p className="text-xs text-destructive">{errors.paypalEmail.message}</p>
                                      )}
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                      PayPal-avgift: {paypalFeeSek.toLocaleString("sv-SE")} kr. Du får utbetalt{" "}
                                      {paypalNetSek.toLocaleString("sv-SE")} kr efter avgift.
                                    </p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {currentStep === 3 && (
                <div className="space-y-3">
                  <div className="rounded-lg border border-border p-3 space-y-1.5 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Aktör</span>
                      <span className="font-semibold">{config.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Leveranssätt</span>
                      <span className="font-semibold text-right">{shippingDisplayLabel}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Betalning</span>
                      <span className="font-semibold">
                        {config.paymentOptions.find((o) => o.id === watch("paymentMethod"))?.label}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Enhet</span>
                      <span className="font-semibold">
                        {model} {storage}
                      </span>
                    </div>
                    <div className="flex justify-between pt-1.5 border-t mt-1.5">
                      <span className="text-muted-foreground">Estimerat belopp</span>
                      <span className="font-bold text-primary">{estimatedPrice}</span>
                    </div>
                    {shippingFeeSek ? (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Fraktavgift</span>
                        <span className="font-semibold">-{shippingFeeSek.toLocaleString("sv-SE")} kr</span>
                      </div>
                    ) : null}
                    {watch("paymentMethod") === "paypal" && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">PayPal-avgift</span>
                          <span className="font-semibold">-{paypalFeeSek.toLocaleString("sv-SE")} kr</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Efter avgifter</span>
                          <span className="font-bold text-primary">{paypalNetSek.toLocaleString("sv-SE")} kr</span>
                        </div>
                      </>
                    )}
                    {watch("paymentMethod") !== "paypal" && shippingFeeSek ? (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Efter avgift</span>
                        <span className="font-bold text-primary">{netPayoutSek.toLocaleString("sv-SE")} kr</span>
                      </div>
                    ) : null}
                  </div>

                  <div className="rounded-lg border border-border p-3 space-y-0.5 text-sm">
                    <p className="font-semibold mb-1">Dina uppgifter</p>
                    <p>
                      {watch("firstName")} {watch("lastName")}
                    </p>
                    <p className="text-muted-foreground">{watch("email")}</p>
                    <p className="text-muted-foreground">{watch("phone")}</p>
                    <p className="text-muted-foreground">
                      {watch("address")}, {watch("postalCode")} {watch("city")}
                    </p>
                  </div>

                  <div className="space-y-2 pt-1">
                    <div className="flex items-start space-x-2">
                      <Checkbox
                        id="findMyIphone"
                        checked={findMyIphoneDisabled}
                        onCheckedChange={(c) => setValue("findMyIphoneDisabled", c as boolean)}
                        className="rounded-[5px] mt-0.5"
                      />
                      <Label htmlFor="findMyIphone" className="text-sm font-normal cursor-pointer leading-tight">
                        Jag har avaktiverat Hitta min iPhone
                      </Label>
                    </div>

                    <div className="flex items-start space-x-2">
                      <Checkbox
                        id="terms"
                        checked={termsAccepted}
                        onCheckedChange={(c) => setValue("termsAccepted", c as boolean)}
                        className="rounded-[5px] mt-0.5"
                      />
                      <Label htmlFor="terms" className="text-sm font-normal cursor-pointer leading-tight">
                        Jag har läst och godkänner{" "}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            setShowTeleveraTerms(true);
                          }}
                          className="text-primary hover:underline font-medium"
                        >
                          Televeras
                        </button>{" "}
                        och{" "}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            setShowVendorTerms(true);
                          }}
                          className="text-primary hover:underline font-medium"
                        >
                          {config.name}s villkor
                        </button>
                      </Label>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                {currentStep > 1 && (
                  <Button type="button" variant="outline" onClick={prevStep} className="flex-1 border-border">
                    ← Tillbaka
                  </Button>
                )}

                {currentStep < 3 ? (
                  <Button type="button" onClick={nextStep} className="flex-1">
                    Nästa →
                  </Button>
                ) : (
                  <Button
                    type="button"
                    className="cmp-checkout-submit flex-1"
                    disabled={isSubmitting}
                    data-loading={isSubmitting ? "true" : undefined}
                    onClick={async () => {
                      if (!watch("findMyIphoneDisabled")) {
                        trackEvent("validation_error", {
                          funnel: "checkout",
                          surface: compact ? "compact" : "page",
                          step: 3,
                          checkout_step: CHECKOUT_STEP_SLUGS[3],
                          fields: "findMyIphoneDisabled",
                          model,
                          storage,
                          dealer: config.name,
                        });
                        toast.error("Bekräfta att Hitta min iPhone är avaktiverad");
                        return;
                      }
                      if (!watch("termsAccepted")) {
                        trackEvent("validation_error", {
                          funnel: "checkout",
                          surface: compact ? "compact" : "page",
                          step: 3,
                          checkout_step: CHECKOUT_STEP_SLUGS[3],
                          fields: "termsAccepted",
                          model,
                          storage,
                          dealer: config.name,
                        });
                        toast.error("Du måste godkänna villkoren");
                        return;
                      }
                      trackEvent("checkout_step_completed", {
                        funnel: "checkout",
                        surface: compact ? "compact" : "page",
                        step: 3,
                        checkout_step: CHECKOUT_STEP_SLUGS[3],
                        model,
                        storage,
                        dealer: config.name,
                        duration_ms: Date.now() - viewedAtRef.current,
                      });
                      await submitOrder(getValues());
                    }}
                  >
                    <span>Slutför beställning</span>
                  </Button>
                )}
              </div>
            </div>

            {!compact && (
              <div className="lg:col-span-1">
                <Card className="p-6 sticky top-4 space-y-4">
                  <h2 className="text-xl font-semibold mb-4">Sammanfattning</h2>
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Modell</p>
                      <p className="font-medium">{model}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Lagring</p>
                      <p className="font-medium">{storage}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Köpare</p>
                      <p className="font-medium">{config.name}</p>
                    </div>
                    {watch("shippingOption") && (
                      <div>
                        <p className="text-sm text-muted-foreground">Fraktalternativ</p>
                        <p className="font-medium">
                          {shippingDisplayLabel}
                        </p>
                      </div>
                    )}
                    {watch("paymentMethod") && (
                      <div>
                        <p className="text-sm text-muted-foreground">Betalningsmetod</p>
                        <p className="font-medium">
                          {config.paymentOptions.find((opt) => opt.id === watch("paymentMethod"))?.label}
                        </p>
                      </div>
                    )}
                    <div className="pt-4 border-t">
                      <p className="text-sm text-muted-foreground mb-1">Uppskattat pris</p>
                      <p className="text-2xl font-bold text-primary">{netPayoutSek.toLocaleString("sv-SE")} kr</p>
                      {(shippingFeeSek || selectedPaypalFeeSek) ? (
                        <p className="text-xs text-muted-foreground mt-1">
                          Efter avgifter från {priceSek.toLocaleString("sv-SE")} kr
                        </p>
                      ) : null}
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </form>
      </div>

      <TermsDialog open={showTeleveraTerms} onOpenChange={setShowTeleveraTerms} type="televera" />
      <TermsDialog open={showVendorTerms} onOpenChange={setShowVendorTerms} type="vendor" vendorName={config.name} />
    </>
  );
};

export default CheckoutContent;
