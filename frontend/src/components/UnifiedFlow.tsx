import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Check, ChevronLeft, Info, Loader2, Search, Star } from "lucide-react";
import { toast } from "sonner";

import ComparisonTable from "@/components/ComparisonTable";
import SellOfferDialog from "@/components/SellOfferDialog";
import {
  ConditionAnswers,
  ScreenGlass,
  WearLevel,
  WearLevelWithCrack,
  initialConditionAnswers,
} from "@/types/condition";
import { CompanyOffer, iphoneModels, storageByModel } from "@/data/mockData";
import { fetchQuotes } from "@/utils/apiQuote";
import { modelToSlug } from "@/utils/modelSlug";
import { useSavedOffers } from "@/hooks/useSavedOffers";
import type { SavedOffer } from "@/types/savedOffers";
import phoneMockup from "@/assets/mockup-iphone-new.png";

interface UnifiedFlowProps {
  onShowResults?: (showing: boolean) => void;
  onModelSelected?: (selected: boolean) => void;
  initialModel?: string;
}

interface RestoreLocationState {
  restoreFromSavedOffer?: SavedOffer;
}

type FlowStep = "model" | "storage" | "battery" | "function" | "glass" | "wear" | "sides" | "back" | "results";

type Option<T> = {
  value: T;
  label: string;
  description?: string;
  summary?: string;
};

const STEP_ORDER: FlowStep[] = ["storage", "battery", "function", "glass", "wear", "sides", "back"];
const STEP_LABELS: Record<Exclude<FlowStep, "model" | "results">, string> = {
  storage: "Lagring",
  battery: "Batteri",
  function: "Funktionskoll",
  glass: "Skärmglas",
  wear: "Skärmskick",
  sides: "Sidor",
  back: "Baksida",
};

const functionalQuestions: {
  key: keyof ConditionAnswers["functional"];
  title: string;
  shortLabel: string;
  info: string;
  invertGood?: boolean;
}[] = [
  {
    key: "powersOn",
    title: "Startar telefonen normalt?",
    shortLabel: "Startar normalt",
    info: "Håll in sidoknappen. Skärmen ska tändas och iOS ska starta utan problem.",
  },
  {
    key: "network",
    title: "Fungerar nätverket?",
    shortLabel: "Nätverk fungerar",
    info: "Sätt i ett SIM-kort eller eSIM och kontrollera att telefonen får mottagning.",
  },
  {
    key: "faceId",
    title: "Fungerar Face ID?",
    shortLabel: "Face ID fungerar",
    info: "Gå till Inställningar och testa upplåsning med Face ID.",
  },
  {
    key: "selfieCamera",
    title: "Fungerar selfie-kameran?",
    shortLabel: "Selfie-kamera OK",
    info: "Öppna Kamera-appen, växla till frontkameran och kontrollera bilden.",
  },
  {
    key: "speaker",
    title: "Fungerar högtalaren?",
    shortLabel: "Högtalare fungerar",
    info: "Spela upp ett ljud och lyssna efter sprakningar eller bortfall.",
  },
  {
    key: "bentOrWaterDamaged",
    title: "Är telefonen böjd eller vattenskadad?",
    shortLabel: "Inga skador",
    info: "Lägg den platt på ett bord. Den ska inte vagga och inte visa tecken på fukt.",
    invertGood: true,
  },
];

const screenGlassOptions: Option<ScreenGlass>[] = [
  { value: "chipped", label: "Flisig", description: "En eller flera flisor", summary: "Flisig" },
  { value: "scratched", label: "Kraftigt repad", description: "Tydliga djupa repor", summary: "Kraftiga repor" },
  {
    value: "none",
    label: "Inga sprickor, flisor eller kraftiga repor",
    description: "Glaset är helt",
    summary: "Inga skador",
  },
];

const screenWearOptions: Option<WearLevel>[] = [
  { value: "visible", label: "Synligt slitage", description: "Tydliga repor", summary: "Synliga repor" },
  { value: "some", label: "Repor som syns vid vissa vinklar", description: "Lättare bruksspår", summary: "Lätta repor" },
  { value: "minimal", label: "Minimalt slitage", description: "Enstaka mikrorepor", summary: "Mikrorepor" },
  { value: "none", label: "Inga tecken på användning", description: "Som ny", summary: "Som ny" },
];

const sidesBackOptions: Option<WearLevelWithCrack>[] = [
  { value: "cracked", label: "Sprucken eller trasig", description: "Sprickor eller bitar saknas", summary: "Sprucken" },
  { value: "visible", label: "Synligt slitage", description: "Repor eller bucklor", summary: "Synliga skador" },
  { value: "some", label: "Repor som syns vid vinklar", description: "Lättare bruksspår", summary: "Lätta repor" },
  { value: "minimal", label: "Minimalt slitage", description: "Enstaka märken", summary: "Minimalt" },
  { value: "none", label: "Inga tecken på användning", description: "Som ny", summary: "Som ny" },
];

const stepIndex = (step: FlowStep) => STEP_ORDER.indexOf(step);
const isValuationStep = (step: FlowStep): step is Exclude<FlowStep, "model" | "results"> => STEP_ORDER.includes(step);

const optionSummary = <T extends string>(options: Option<T>[], value: T | null) =>
  options.find((option) => option.value === value)?.summary ?? "–";

const formatBattery = (battery: number | null) => (battery === null ? "–" : `${battery} %`);

const PhoneGlyph = () => (
  <span className="cmp-phone-glyph" aria-hidden>
    <span />
  </span>
);

const InfoBox = ({ children }: { children: React.ReactNode }) => (
  <div className="cmp-flow-info">
    <Info className="cmp-flow-info-icon" aria-hidden />
    <p>{children}</p>
  </div>
);

const StepProgress = ({ step }: { step: Exclude<FlowStep, "model" | "results"> }) => {
  const index = stepIndex(step);
  const percent = ((index + 0.5) / STEP_ORDER.length) * 100;

  return (
    <div className="cmp-step-progress">
      <div className="cmp-step-progress-labels">
        <span>Steg {index + 1} av 7</span>
        <span>{STEP_LABELS[step]}</span>
      </div>
      <div className="cmp-step-track">
        <span style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
};

const MobileHeader = ({
  model,
  step,
  onBack,
}: {
  model: string;
  step: Exclude<FlowStep, "model" | "results">;
  onBack: () => void;
}) => (
  <div className="cmp-mobile-step-head">
    <button type="button" onClick={onBack} aria-label="Gå tillbaka">
      <ChevronLeft />
    </button>
    <PhoneGlyph />
    <div>
      <span>Du värderar</span>
      <strong>{model || "din telefon"}</strong>
    </div>
    <em>{stepIndex(step) + 1}/7</em>
  </div>
);

const FootBar = ({
  onBack,
  onNext,
  nextLabel = "Fortsätt",
  nextDisabled,
  loading,
  backDisabled,
}: {
  onBack?: () => void;
  onNext: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  loading?: boolean;
  backDisabled?: boolean;
}) => (
  <div className="cmp-flow-foot">
    {onBack && (
      <button type="button" className="cmp-btn cmp-btn-secondary" onClick={onBack} disabled={backDisabled || loading}>
        <ChevronLeft aria-hidden />
        Tillbaka
      </button>
    )}
    <button type="button" className="cmp-btn cmp-btn-primary" onClick={onNext} disabled={nextDisabled || loading}>
      {loading ? (
        <>
          <Loader2 className="cmp-spin" aria-hidden />
          Beräknar...
        </>
      ) : (
        `${nextLabel} →`
      )}
    </button>
  </div>
);

const OptionList = <T extends string>({
  options,
  value,
  onChange,
}: {
  options: Option<T>[];
  value: T | null;
  onChange: (value: T) => void;
}) => (
  <div className="cmp-option-list">
    {options.map((option) => (
      <button
        key={option.value}
        type="button"
        className={value === option.value ? "cmp-option-row selected" : "cmp-option-row"}
        onClick={() => onChange(option.value)}
      >
        <span className="cmp-radio-dot" aria-hidden />
        <span>
          <strong>{option.label}</strong>
          {option.description && <em>{option.description}</em>}
        </span>
      </button>
    ))}
  </div>
);

const ValuePanel = ({
  model,
  storage,
  answers,
  activeStep,
}: {
  model: string;
  storage: string;
  answers: ConditionAnswers;
  activeStep: Exclude<FlowStep, "model" | "results">;
}) => {
  const currentIndex = stepIndex(activeStep);
  const rows = [
    { key: "storage", label: "Lagring", value: storage || "–" },
    { key: "battery", label: "Batteri", value: formatBattery(answers.batteryHealth) },
    {
      key: "function",
      label: "Funktionskoll",
      value: functionalQuestions.every((q) => answers.functional[q.key] !== null) ? "Allt OK" : "–",
    },
    { key: "glass", label: "Skärmglas", value: optionSummary(screenGlassOptions, answers.screenGlass) },
    { key: "wear", label: "Skärmskick", value: optionSummary(screenWearOptions, answers.screenWear) },
    { key: "sides", label: "Sidor", value: optionSummary(sidesBackOptions, answers.sidesWear) },
    { key: "back", label: "Baksida", value: optionSummary(sidesBackOptions, answers.backWear) },
  ];

  return (
    <aside className="cmp-value-panel">
      <div className="cmp-device-card">
        <div>
          <p>Du värderar</p>
          <h2>{model || "Din telefon"}</h2>
        </div>
        <div className="cmp-device-image">
          <img src={phoneMockup} alt="" />
        </div>
      </div>
      <div className="cmp-value-rows">
        {rows.map((row, index) =>
          index <= currentIndex ? (
            <div key={row.key} className="cmp-value-row">
              <span>{row.label}</span>
              <strong className={row.value === "–" ? "empty" : ""}>{row.value}</strong>
            </div>
          ) : null,
        )}
      </div>
    </aside>
  );
};

const UnifiedFlow = ({ onShowResults, onModelSelected, initialModel }: UnifiedFlowProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { addSavedOffer } = useSavedOffers();
  const [step, setStep] = useState<FlowStep>(initialModel ? "storage" : "model");
  const [model, setModel] = useState(initialModel ?? "");
  const [storage, setStorage] = useState("");
  const [answers, setAnswers] = useState<ConditionAnswers>(initialConditionAnswers);
  const [batteryMode, setBatteryMode] = useState<"enter" | "cant" | null>(null);
  const [funcSubStep, setFuncSubStep] = useState(0);
  const [results, setResults] = useState<CompanyOffer[] | null>(null);
  const [resultsTimestamp, setResultsTimestamp] = useState("");
  const [loadingResults, setLoadingResults] = useState(false);
  const [search, setSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [sellDialogOpen, setSellDialogOpen] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState<CompanyOffer | null>(null);
  const [activeSavedOfferId, setActiveSavedOfferId] = useState<string | undefined>(undefined);
  const blurTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const flowRef = useRef<HTMLDivElement | null>(null);

  const availableStorage = model ? storageByModel[model] || [] : [];
  const filteredModels = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    if (!normalized) return iphoneModels;
    return iphoneModels.filter((item) => item.toLowerCase().includes(normalized));
  }, [search]);

  useEffect(() => {
    if (initialModel) onModelSelected?.(true);
  }, [initialModel, onModelSelected]);

  useEffect(() => {
    const state = location.state as RestoreLocationState | null;
    if (!state?.restoreFromSavedOffer) return;

    const saved = state.restoreFromSavedOffer;
    setModel(saved.model);
    setStorage(saved.storage);
    if (saved.condition) setAnswers(saved.condition);
    if (saved.offers?.length) {
      setResults(saved.offers);
      setStep("results");
      onShowResults?.(true);
      onModelSelected?.(true);
      toast.success("Värdering återställd");
    }
  }, [location.state, onModelSelected, onShowResults]);

  useEffect(() => {
    if (step === "model" || step === "results") return;
    const timer = window.setTimeout(() => {
      flowRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 40);

    return () => window.clearTimeout(timer);
  }, [step, funcSubStep]);

  const selectModel = (nextModel: string) => {
    setModel(nextModel);
    setSearch(nextModel);
    setStorage("");
    setStep("storage");
    setSearchOpen(false);
    onModelSelected?.(true);
    navigate(`/salja/${modelToSlug(nextModel)}`);
  };

  const goStep = (next: FlowStep) => {
    setStep(next);
    onShowResults?.(next === "results");
  };

  const goBack = () => {
    if (step === "function" && funcSubStep > 0 && funcSubStep < functionalQuestions.length) {
      setFuncSubStep((current) => current - 1);
      return;
    }

    if (step === "storage") {
      if (initialModel) {
        navigate("/");
        return;
      }
      reset();
      return;
    }

    if (step === "results") {
      goStep("back");
      return;
    }

    const index = stepIndex(step);
    if (index > 0) goStep(STEP_ORDER[index - 1]);
  };

  const reset = () => {
    setStep("model");
    setModel("");
    setStorage("");
    setSearch("");
    setAnswers(initialConditionAnswers);
    setBatteryMode(null);
    setFuncSubStep(0);
    setResults(null);
    setResultsTimestamp("");
    setActiveSavedOfferId(undefined);
    onShowResults?.(false);
    onModelSelected?.(false);
  };

  const computeAndShow = async () => {
    setLoadingResults(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 700));
      const offers = await fetchQuotes(model, storage, answers);
      setResults(offers);
      setResultsTimestamp(
        new Date().toLocaleString("sv-SE", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        }),
      );
      goStep("results");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      console.error("fetchQuotes failed:", error);
      toast.error("Kunde inte hämta priser just nu. Försök igen.");
    } finally {
      setLoadingResults(false);
    }
  };

  const handleFuncAnswer = (value: boolean) => {
    const question = functionalQuestions[funcSubStep];
    if (!question) return;

    const nextFunctional = { ...answers.functional, [question.key]: value };
    setAnswers((current) => ({ ...current, functional: nextFunctional }));

    const nextAfterCurrent = functionalQuestions.findIndex(
      (candidate, index) => index > funcSubStep && nextFunctional[candidate.key] === null,
    );
    const nextUnanswered = functionalQuestions.findIndex((candidate) => nextFunctional[candidate.key] === null);

    setFuncSubStep(
      nextAfterCurrent >= 0
        ? nextAfterCurrent
        : nextUnanswered >= 0
          ? nextUnanswered
          : functionalQuestions.length,
    );
  };

  const handleSellClick = (offer: CompanyOffer) => {
    const savedOfferId = addSavedOffer({
      model,
      storage,
      condition: answers,
      offers: results || [],
      selectedCompany: offer.company,
      selectedPrice: offer.price,
    });

    setActiveSavedOfferId(savedOfferId);
    setSelectedOffer(offer);
    setSellDialogOpen(true);
  };

  const renderModelStep = () => (
    <section id="valuation" className="cmp-model-step">
      <div className="cmp-model-card">
        <div className="cmp-search-wrap">
          <Search aria-hidden />
          <input
            value={search}
            placeholder="Sök eller välj din modell..."
            onChange={(event) => {
              setSearch(event.target.value);
              setSearchOpen(true);
            }}
            onFocus={() => {
              if (blurTimeoutRef.current) {
                clearTimeout(blurTimeoutRef.current);
                blurTimeoutRef.current = null;
              }
              setSearchOpen(true);
            }}
            onBlur={() => {
              blurTimeoutRef.current = setTimeout(() => setSearchOpen(false), 150);
            }}
          />
          {searchOpen && (
            <div className="cmp-search-results">
              {filteredModels.length ? (
                filteredModels.map((item) => (
                  <button key={item} type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => selectModel(item)}>
                    {item}
                  </button>
                ))
              ) : (
                <p>Ingen modell hittades.</p>
              )}
            </div>
          )}
        </div>
        <div className="cmp-trust-row">
          <span>
            <Check aria-hidden /> Gratis
          </span>
          <span>
            <Check aria-hidden /> Tar 30 sek
          </span>
          <span>
            <Star aria-hidden /> Flera bud
          </span>
        </div>
      </div>
    </section>
  );

  const renderStorage = () => (
    <>
      <h2>Hur mycket lagring?</h2>
      <InfoBox>Hittas under Inställningar → Allmänt → Om → Kapacitet.</InfoBox>
      <div className="cmp-storage-grid">
        {availableStorage.map((item) => (
          <button
            key={item}
            type="button"
            className={storage === item ? "selected" : ""}
            onClick={() => {
              setStorage(item);
              goStep("battery");
            }}
          >
            {item}
          </button>
        ))}
      </div>
      <FootBar onBack={goBack} onNext={() => goStep("battery")} nextDisabled={!storage} />
    </>
  );

  const renderBattery = () => {
    const valid = batteryMode === "cant" || (answers.batteryHealth !== null && answers.batteryHealth >= 1 && answers.batteryHealth <= 100);

    return (
      <>
        <h2>Vad är batterihälsan?</h2>
        <InfoBox>Hittas under Inställningar → Batteri → Batterihälsa och laddning → Maximal kapacitet.</InfoBox>
        <button
          type="button"
          className={batteryMode === "enter" ? "cmp-battery-card selected" : "cmp-battery-card"}
          onClick={() => setBatteryMode("enter")}
        >
          <span className="cmp-radio-dot" aria-hidden />
          <strong>Ange batterikapacitet</strong>
          <div className="cmp-battery-input" onClick={(event) => event.stopPropagation()}>
            <input
              type="number"
              min={1}
              max={100}
              inputMode="numeric"
              value={answers.batteryHealth ?? ""}
              placeholder="87"
              onFocus={() => setBatteryMode("enter")}
              onChange={(event) => {
                setBatteryMode("enter");
                const nextValue = event.target.value;
                if (nextValue === "") {
                  setAnswers((current) => ({ ...current, batteryHealth: null }));
                  return;
                }
                const parsed = parseInt(nextValue, 10);
                if (Number.isNaN(parsed)) return;
                setAnswers((current) => ({ ...current, batteryHealth: Math.max(1, Math.min(100, parsed)) }));
              }}
            />
            <span>%</span>
          </div>
        </button>
        <button
          type="button"
          className={batteryMode === "cant" ? "cmp-battery-card compact selected" : "cmp-battery-card compact"}
          onClick={() => {
            setBatteryMode("cant");
            setAnswers((current) => ({ ...current, batteryHealth: 100 }));
          }}
        >
          <span className="cmp-radio-dot" aria-hidden />
          <strong>Kan inte kontrollera</strong>
          <em>Vi bekräftar kapaciteten efter inspektion.</em>
        </button>
        <FootBar onBack={goBack} onNext={() => goStep("function")} nextDisabled={!valid} />
      </>
    );
  };

  const renderFunction = () => {
    const allAnswered = functionalQuestions.every((question) => answers.functional[question.key] !== null);
    const activeQuestion = funcSubStep < functionalQuestions.length ? functionalQuestions[funcSubStep] : null;

    return (
      <>
        <h2>Funktionskoll</h2>
        <div className="cmp-done-rows">
          {functionalQuestions.map((question, index) => {
            const answer = answers.functional[question.key];
            if (answer === null) return null;
            return (
              <div key={question.key} className="cmp-done-row">
                <span>
                  <Check aria-hidden />
                </span>
                <strong>{question.shortLabel}</strong>
                <button type="button" onClick={() => setFuncSubStep(index)}>
                  Redigera
                </button>
              </div>
            );
          })}
        </div>

        {activeQuestion ? (
          <div className="cmp-function-card">
            <p>
              {funcSubStep + 1}/{functionalQuestions.length} · Funktionskoll
            </p>
            <h3>{activeQuestion.title}</h3>
            <InfoBox>
              {activeQuestion.info}
              {activeQuestion.invertGood ? " Svara Nej om allt är som det ska." : ""}
            </InfoBox>
            <div className="cmp-yes-no">
              {(activeQuestion.invertGood ? [false, true] : [true, false]).map((value) => (
                <button key={String(value)} type="button" onClick={() => handleFuncAnswer(value)}>
                  {value ? "Ja" : "Nej"}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="cmp-all-done">
            <span>
              <Check aria-hidden />
            </span>
            Allt kontrollerat
          </div>
        )}

        <FootBar onBack={goBack} onNext={() => goStep("glass")} nextDisabled={!allAnswered} />
      </>
    );
  };

  const renderCondition = <T extends string>({
    title,
    hint,
    options,
    value,
    onChange,
    next,
    nextLabel,
    loading,
  }: {
    title: string;
    hint: string;
    options: Option<T>[];
    value: T | null;
    onChange: (value: T) => void;
    next: () => void;
    nextLabel?: string;
    loading?: boolean;
  }) => (
    <>
      <h2>{title}</h2>
      <InfoBox>{hint}</InfoBox>
      <OptionList options={options} value={value} onChange={onChange} />
      <FootBar onBack={goBack} onNext={next} nextDisabled={!value} nextLabel={nextLabel} loading={loading} />
    </>
  );

  const renderStepContent = (currentStep: Exclude<FlowStep, "model" | "results">) => {
    switch (currentStep) {
      case "storage":
        return renderStorage();
      case "battery":
        return renderBattery();
      case "function":
        return renderFunction();
      case "glass":
        return renderCondition({
          title: "Hur ser glaset ut?",
          hint: "Håll upp telefonen mot ljuset och titta noga efter sprickor, flisor och repor.",
          options: screenGlassOptions,
          value: answers.screenGlass,
          onChange: (value) => setAnswers((current) => ({ ...current, screenGlass: value })),
          next: () => goStep("wear"),
        });
      case "wear":
        return renderCondition({
          title: "Hur är skärmens skick?",
          hint: "Titta med skärmen på, gärna mot en ljus bakgrund.",
          options: screenWearOptions,
          value: answers.screenWear,
          onChange: (value) => setAnswers((current) => ({ ...current, screenWear: value })),
          next: () => goStep("sides"),
        });
      case "sides":
        return renderCondition({
          title: "Hur ser sidorna ut?",
          hint: "Titta längs kanterna och ramens sidor, och kika efter repor, bucklor och sprickor.",
          options: sidesBackOptions,
          value: answers.sidesWear,
          onChange: (value) => setAnswers((current) => ({ ...current, sidesWear: value })),
          next: () => goStep("back"),
        });
      case "back":
        return renderCondition({
          title: "Hur ser baksidan ut?",
          hint: "Lägg telefonen med baksidan upp mot ett plant underlag och titta noga.",
          options: sidesBackOptions,
          value: answers.backWear,
          onChange: (value) => setAnswers((current) => ({ ...current, backWear: value })),
          next: computeAndShow,
          nextLabel: "Beräkna bästa bud",
          loading: loadingResults,
        });
    }
  };

  const renderValuationStep = () => {
    if (!isValuationStep(step)) return null;

    return (
      <section id="valuation" ref={flowRef} className="cmp-valuation-shell">
        <div className="cmp-mobile-flow">
          <MobileHeader model={model} step={step} onBack={goBack} />
          <StepProgress step={step} />
          <div className="cmp-mobile-content">{renderStepContent(step)}</div>
        </div>

        <div className="cmp-desktop-flow">
          <ValuePanel model={model} storage={storage} answers={answers} activeStep={step} />
          <main className="cmp-desktop-main">
            <div className="cmp-desktop-progress">
              <div>
                <span style={{ width: `${((stepIndex(step) + 0.5) / STEP_ORDER.length) * 100}%` }} />
              </div>
              <strong>{stepIndex(step) + 1}/7</strong>
            </div>
            <div className="cmp-desktop-card">{renderStepContent(step)}</div>
          </main>
        </div>
      </section>
    );
  };

  const renderResults = () => {
    if (!results) return null;

    return (
      <section id="valuation" className="cmp-results">
        <div className="cmp-results-head">
          <button type="button" onClick={() => goStep("back")}>
            <ChevronLeft aria-hidden />
            Tillbaka
          </button>
          <div>
            <span>Bästa bud för</span>
            <h2>
              {model} · {storage}
            </h2>
          </div>
        </div>
        <ComparisonTable
          offers={results}
          model={model}
          storage={storage}
          onSellClick={handleSellClick}
          updatedAt={resultsTimestamp}
        />
        <SellOfferDialog
          open={sellDialogOpen}
          onOpenChange={setSellDialogOpen}
          offer={selectedOffer}
          model={model}
          storage={storage}
          savedOfferId={activeSavedOfferId}
        />
      </section>
    );
  };

  if (step === "model") return renderModelStep();
  if (step === "results") return renderResults();
  return renderValuationStep();
};

export default UnifiedFlow;
