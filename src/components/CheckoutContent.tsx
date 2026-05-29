import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { Loader2, Check, Info } from "lucide-react";
import TermsDialog from "@/components/TermsDialog";
import { useSavedOffers } from "@/hooks/useSavedOffers";

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
      .min(1, "Personnummer krävs")
      .regex(/^(\d{6}|\d{8})-?\d{4}$/, "Ogiltigt personnummer (ÅÅÅÅMMDD-XXXX)"),
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
  });

type CheckoutFormData = z.infer<typeof checkoutSchema>;

type ShippingOption = {
  id: string;
  label: string;
  description?: string;
  bullets?: string[];
};

type PaymentOption = {
  id: string;
  label: string;
  requiresBankDetails: boolean;
};

export type DealerConfig = {
  name: string;
  shippingOptions: ShippingOption[];
  paymentOptions: PaymentOption[];
};

// =====================
// Dealer Config
// =====================

export const dealerConfig: Record<string, DealerConfig> = {
  swappie: {
    name: "Swappie",
    shippingOptions: [
      {
        id: "sales-package",
        label: "Gratis försäljningspaket",
        description: "Levereras hem till dig inom 3–5 arbetsdagar",
        bullets: ["Gratis & säkert", "Fri fraktetikett ingår", "Skyddar din enhet"],
      },
      {
        id: "email-label",
        label: "Fraktsedel via e-post",
        description: "Få fraktsedeln direkt till din inkorg",
        bullets: ["Kostnadsfritt", "Skriv ut hemma", "Skicka när det passar dig"],
      },
    ],
    paymentOptions: [{ id: "bank", label: "Banköverföring", requiresBankDetails: true }],
  },
  fixmyphone: {
    name: "FixMyPhone",
    shippingOptions: [
      {
        id: "email-label",
        label: "Fraktsedel via e-post",
        description: "Få fraktsedeln direkt till din inkorg",
        bullets: ["Fri frakt tur & retur", "Fraktsedel via e-post", "Snabb hantering vid mottagande"],
      },
      {
        id: "sales-package",
        label: "Gratis försäljningspaket",
        description: "Levereras hem till dig inom 3–5 arbetsdagar",
        bullets: [
          "Gratis paket & fraktsedel hem",
          "Skyddar mobilen under transport",
          "Betalning direkt efter mottagandet",
        ],
      },
    ],
    paymentOptions: [
      { id: "swish", label: "Swish", requiresBankDetails: false },
      { id: "bank", label: "Banköverföring", requiresBankDetails: true },
    ],
  },
  happyphone: {
    name: "HappyPhone",
    shippingOptions: [
      {
        id: "email-label",
        label: "Fraktsedel via e-post",
        description: "Få fraktsedeln direkt till din inkorg",
        bullets: ["Fri frakt tur & retur", "Fraktsedel via e-post", "Snabb hantering vid mottagande"],
      },
      {
        id: "sales-package",
        label: "Gratis försäljningspaket",
        description: "Levereras hem till dig inom 3–5 arbetsdagar",
        bullets: [
          "Gratis paket & fraktsedel hem",
          "Skyddar mobilen under transport",
          "Betalning direkt efter mottagandet",
        ],
      },
    ],
    paymentOptions: [
      { id: "swish", label: "Swish", requiresBankDetails: false },
      { id: "bank", label: "Banköverföring", requiresBankDetails: true },
    ],
  },
  telestore: {
    name: "Telestore",
    shippingOptions: [
      {
        id: "sales-package",
        label: "Gratis försäljningspaket",
        description: "Levereras hem till dig inom 1-3 arbetsdagar",
        bullets: ["Gratis & säkert", "Fri fraktetikett ingår", "Skyddar din enhet"],
      },
      {
        id: "email-label",
        label: "Fraktsedel via e-post",
        description: "Få fraktsedeln direkt till din inkorg",
        bullets: ["Gratis fraktsedel via e-post", "Spårbart & försäkrat paket", "Utbetalning samma dag"],
      },
    ],
    paymentOptions: [
      { id: "swish", label: "Swish", requiresBankDetails: false },
      { id: "bank", label: "Banköverföring", requiresBankDetails: true },
    ],
  },
  renewed: {
    name: "Renewed",
    shippingOptions: [
      {
        id: "email-label",
        label: "Fraktsedel via e-post",
        description: "Få fraktsedeln direkt till din inkorg",
        bullets: ["Kostnadsfritt", "Skriv ut hemma", "Skicka när det passar dig"],
      },
    ],
    paymentOptions: [{ id: "bank", label: "Banköverföring", requiresBankDetails: true }],
  },
  cleverbuy: {
    name: "CleverBuy",
    shippingOptions: [
      {
        id: "email-label",
        label: "Digital fraktsedel via e-post",
        description: "Få fraktsedeln direkt till din inkorg",
        bullets: ["Kostnadsfritt", "Skriv ut hemma", "Utbetalning inom 2-4 dagar"],
      },
    ],
    paymentOptions: [{ id: "bank-iban", label: "Banköverföring (IBAN)", requiresBankDetails: true }],
  },
};

// =====================
// Props
// =====================

export interface CheckoutContentProps {
  dealer: string;
  model: string;
  storage: string;
  price: string;
  conditionAnswers?: Record<string, unknown>;
  savedOfferId?: string;
  compact?: boolean;
  showRestoredBanner?: boolean;
}

// =====================
// Component
// =====================

const CheckoutContent = ({
  dealer,
  model,
  storage,
  price,
  conditionAnswers,
  savedOfferId,
  compact = false,
  showRestoredBanner = false,
}: CheckoutContentProps) => {
  const navigate = useNavigate();
  const { removeSavedOffer } = useSavedOffers();
  const config = dealerConfig[dealer] || dealerConfig.swappie;

  const [currentStep, setCurrentStep] = useState(1);
  const [useSamePhoneForSwish, setUseSamePhoneForSwish] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCashMyPhoneTerms, setShowCashMyPhoneTerms] = useState(false);
  const [showVendorTerms, setShowVendorTerms] = useState(false);
  const [showPersonalNumberInfo, setShowPersonalNumberInfo] = useState(false);

  useEffect(() => {
    if (!compact) window.scrollTo({ top: 0, behavior: "instant" });
  }, [currentStep, compact]);

  const {
    register,
    watch,
    setValue,
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
  const showErrors = submitCount > 0;

  const stepTitles = ["Dina uppgifter", "Frakt & betalning", "Bekräfta din beställning"];

  const nextStep = async () => {
    if (currentStep === 1) {
      const isValid = await trigger(
        ["firstName", "lastName", "personalNumber", "address", "postalCode", "city", "phone", "email"],
        { shouldFocus: false },
      );
      if (!isValid) {
        toast.error("Vänligen fyll i alla obligatoriska fält");
        return;
      }
      setCurrentStep(2);
      return;
    }

    if (currentStep === 2) {
      if (!watch("shippingOption")) {
        toast.error("Välj ett fraktalternativ");
        return;
      }
      if (!watch("paymentMethod")) {
        toast.error("Välj en betalningsmetod");
        return;
      }

      const fields: (keyof CheckoutFormData)[] = [];
      const pm = watch("paymentMethod");
      if (pm === "bank") fields.push("clearingNumber", "accountNumber");
      if (pm === "bank-iban") fields.push("ibanNumber");
      if (pm === "swish") fields.push("swishNumber");

      if (fields.length) {
        const ok = await trigger(fields, { shouldFocus: false });
        if (!ok) {
          toast.error("Vänligen fyll i alla obligatoriska fält");
          return;
        }
      }

      setCurrentStep(3);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const estimatedPrice = price ? `${price} kr` : "–";

  const handleNavigateToSummary = useCallback(() => {
    const data = getValues();
    navigate("/summary", {
      state: { ...data, model, storage, price: estimatedPrice, dealer: config.name },
    });
  }, [navigate, getValues, model, storage, estimatedPrice, config.name]);

  const submitOrder = async (data: CheckoutFormData) => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      await fetch("https://vina-unflutterable-madlyn.ngrok-free.dev/submit_order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model,
          storage,
          vendor: config.name,
          price: parseInt(price || "0"),
          shippingOption: data.shippingOption,
          contact: {
            firstName: data.firstName,
            lastName: data.lastName,
            personalNumber: data.personalNumber,
            address: data.address,
            postalCode: data.postalCode,
            city: data.city,
            phone: data.phone,
            email: data.email,
          },
          payment: {
            method: data.paymentMethod,
            details:
              data.paymentMethod === "bank"
                ? `Clearing: ${data.clearingNumber}, Konto: ${data.accountNumber}`
                : data.paymentMethod === "bank-iban"
                  ? `IBAN: ${data.ibanNumber}`
                  : `Swish: ${data.swishNumber}`,
          },
          answers: conditionAnswers,
        }),
      });

      if (savedOfferId) removeSavedOffer(savedOfferId);
    } catch (err) {
      if (import.meta.env.DEV) console.error("Fel vid inskick:", err);
    }

    setTimeout(() => handleNavigateToSummary(), 1500);
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
                      {...register("personalNumber")}
                    />
                    {showErrors && errors.personalNumber && (
                      <p className="text-xs text-destructive">{errors.personalNumber.message}</p>
                    )}
                  </div>

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
                          <button
                            type="button"
                            key={option.id}
                            onClick={() => setValue("shippingOption", selected ? "" : option.id)}
                            className={`text-left p-3 rounded-lg border-2 transition-all ${
                              selected ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
                            }`}
                          >
                            <p className="font-semibold text-sm">{option.label}</p>
                            {option.description && (
                              <p className="text-xs text-muted-foreground mt-0.5">{option.description}</p>
                            )}
                          </button>
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
                      <span className="font-semibold">
                        {config.shippingOptions.find((o) => o.id === watch("shippingOption"))?.label}
                      </span>
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
                            setShowCashMyPhoneTerms(true);
                          }}
                          className="text-primary hover:underline font-medium"
                        >
                          CashMyPhones
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
                    className="flex-1"
                    disabled={isSubmitting}
                    onClick={async () => {
                      if (!watch("findMyIphoneDisabled")) {
                        toast.error("Bekräfta att Hitta min iPhone är avaktiverad");
                        return;
                      }
                      if (!watch("termsAccepted")) {
                        toast.error("Du måste godkänna villkoren");
                        return;
                      }
                      await submitOrder(getValues());
                    }}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Skickar...
                      </>
                    ) : (
                      "Slutför beställning"
                    )}
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
                          {config.shippingOptions.find((opt) => opt.id === watch("shippingOption"))?.label}
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
                      <p className="text-2xl font-bold text-primary">{estimatedPrice}</p>
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </form>
      </div>

      <TermsDialog open={showCashMyPhoneTerms} onOpenChange={setShowCashMyPhoneTerms} type="cashmyphone" />
      <TermsDialog open={showVendorTerms} onOpenChange={setShowVendorTerms} type="vendor" vendorName={config.name} />
    </>
  );
};

export default CheckoutContent;
