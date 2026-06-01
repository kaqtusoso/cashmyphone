import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Check, ChevronLeft, Info, Loader2, Search, Shield, Star, Truck, Wallet } from "lucide-react";
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
import { getIphoneImage } from "@/utils/iphoneImage";
import { modelToSlug } from "@/utils/modelSlug";
import { useSavedOffers } from "@/hooks/useSavedOffers";
import type { SavedOffer } from "@/types/savedOffers";

import cmpLogo from "@/assets/logo-green.png";
import swappieLogo from "@/assets/swappie-logo.png";
import fixmyphoneLogo from "@/assets/fixmyphone-logo.png";
import fixiphoneLogo from "@/assets/fixiphone-logo.png";
import fixphoneproLogo from "@/assets/fixphonepro-logo.png";
import happyphoneLogo from "@/assets/happyphone-logo.png";
import renewedLogo from "@/assets/renewed-logo.png";
import phoneheroLogo from "@/assets/phonehero-logo.svg";
import telestoreLogo from "@/assets/telestore-logo.png";

interface UnifiedFlowProps {
  onShowResults?: (showing: boolean) => void;
  onModelSelected?: (selected: boolean) => void;
  initialModel?: string;
}

interface RestoreLocationState {
  restoreFromSavedOffer?: SavedOffer;
}

type StepKey = "model" | "storage" | "battery" | "function" | "glass" | "wear" | "sides" | "back" | "results";

type Option<T extends string> = {
  value: T;
  label: string;
  summary: string;
};

const FLOW_STEPS: Exclude<StepKey, "model" | "results">[] = [
  "storage",
  "battery",
  "function",
  "glass",
  "wear",
  "sides",
  "back",
];

const STEP_LABELS: Record<Exclude<StepKey, "model" | "results">, string> = {
  storage: "Lagring",
  battery: "Batteri",
  function: "Funktionskoll",
  glass: "Skärmglas",
  wear: "Skärmskick",
  sides: "Sidor",
  back: "Baksida",
};

const partnerLogos = [
  telestoreLogo,
  swappieLogo,
  fixmyphoneLogo,
  fixiphoneLogo,
  fixphoneproLogo,
  happyphoneLogo,
  renewedLogo,
  phoneheroLogo,
];

const functionalQuestions: {
  key: keyof ConditionAnswers["functional"];
  label: string;
  title: string;
  hint: string;
  inverted?: boolean;
}[] = [
  {
    key: "powersOn",
    label: "Startar normalt",
    title: "Startar telefonen normalt?",
    hint: "Håll in sidoknappen - skärmen ska tändas och iOS ska starta.",
  },
  {
    key: "network",
    label: "Nätverk fungerar",
    title: "Fungerar nätverket?",
    hint: "Sätt i ett SIM-kort och kontrollera att mottagning visas.",
  },
  {
    key: "faceId",
    label: "Face ID / fingeravtr.",
    title: "Fungerar Face ID?",
    hint: "Gå till Inställningar och testa upplåsning med Face ID.",
  },
  {
    key: "selfieCamera",
    label: "Selfie-kamera OK",
    title: "Fungerar selfie-kameran?",
    hint: "Öppna kameran, växla till frontkameran och kontrollera bilden.",
  },
  {
    key: "speaker",
    label: "Högtalare fungerar",
    title: "Fungerar högtalaren?",
    hint: "Spela upp ett ljud och lyssna efter sprakningar i högtalaren.",
  },
  {
    key: "bentOrWaterDamaged",
    label: "Inga skador",
    title: "Är telefonen böjd eller vattenskadad?",
    hint: "Lägg den platt - den ska inte vagga. Titta efter fuktmärken.",
    inverted: true,
  },
];

const glassOptions: Option<ScreenGlass>[] = [
  { value: "chipped", label: "Flisig - en eller flera flisor", summary: "Flisig" },
  { value: "scratched", label: "Kraftigt repad - tydliga djupa repor", summary: "Kraftiga repor" },
  { value: "none", label: "Inga sprickor, flisor eller kraftiga repor", summary: "Inga skador" },
];

const wearOptions: Option<WearLevel>[] = [
  { value: "visible", label: "Synligt slitage - tydliga repor", summary: "Synliga repor" },
  { value: "some", label: "Repor som syns vid vissa vinklar", summary: "Lätta repor" },
  { value: "minimal", label: "Minimalt slitage - enstaka mikrorepor", summary: "Mikrorepor" },
  { value: "none", label: "Inga tecken - som ny", summary: "Som ny" },
];

const sideOptions: Option<WearLevelWithCrack>[] = [
  { value: "cracked", label: "Sprucken eller trasig", summary: "Sprucken" },
  { value: "visible", label: "Synligt slitage - repor eller bucklor", summary: "Synliga skador" },
  { value: "some", label: "Repor som syns vid vinklar", summary: "Lätta repor" },
  { value: "minimal", label: "Minimalt slitage", summary: "Minimalt" },
  { value: "none", label: "Inga tecken - som ny", summary: "Som ny" },
];

const defaultAnswers: ConditionAnswers = {
  ...initialConditionAnswers,
  screenFunction: {
    brightSpots: false,
    deadPixels: false,
    linesOrBurnIn: false,
    allWorks: true,
  },
  screenFunctionAnswered: true,
};

const formatStorage = (storage: string) => storage.replace(/^(\d+)(GB)$/i, "$1 GB").replace(/^(\d+)TB$/i, "$1 TB");
const stepIndex = (step: StepKey) => FLOW_STEPS.indexOf(step as Exclude<StepKey, "model" | "results">);
const isFlowStep = (step: StepKey): step is Exclude<StepKey, "model" | "results"> => FLOW_STEPS.includes(step as Exclude<StepKey, "model" | "results">);
const optionSummary = <T extends string>(options: Option<T>[], value: T | null) => options.find((option) => option.value === value)?.summary ?? "-";
const newSavedOfferId = () => (crypto.randomUUID ? crypto.randomUUID() : `offer-${Date.now()}`);

const Nav = ({ onSell }: { onSell: () => void }) => (
  <nav className="claude-nav">
    <a className="claude-brand" href="/">
      <img src={cmpLogo} alt="CashMyPhone" />
      <span>CashMyPhone</span>
    </a>
    <div className="claude-nav-links">
      <a href="/#sa-funkar-det">Så funkar det</a>
      <a href="/#varfor-oss">Varför oss</a>
      <a href="/#vanliga-fragor">Vanliga frågor</a>
      <button type="button" onClick={onSell}>Sälj nu</button>
    </div>
  </nav>
);

const Squiggle = () => (
  <svg className="claude-squiggle" viewBox="0 0 200 12" preserveAspectRatio="none" aria-hidden>
    <path d="M3 8 C 45 3, 90 3, 130 6 S 185 9, 197 5" />
  </svg>
);

const SearchBox = ({
  search,
  setSearch,
  open,
  setOpen,
  models,
  onSelect,
}: {
  search: string;
  setSearch: (value: string) => void;
  open: boolean;
  setOpen: (value: boolean) => void;
  models: string[];
  onSelect: (model: string) => void;
}) => {
  const blurRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  return (
    <div className="claude-search">
      <Search aria-hidden />
      <input
        value={search}
        placeholder="Sök modell, t.ex. iPhone 14 Pro..."
        onChange={(event) => {
          setSearch(event.target.value);
          setOpen(true);
        }}
        onFocus={() => {
          if (blurRef.current) clearTimeout(blurRef.current);
          setOpen(true);
        }}
        onBlur={() => {
          blurRef.current = setTimeout(() => setOpen(false), 150);
        }}
      />
      <button type="button" disabled={!search.trim()} onMouseDown={(event) => event.preventDefault()} onClick={() => models[0] && onSelect(models[0])}>
        Jämför bud
      </button>
      {open && (
        <div className="claude-search-menu">
          {models.length ? (
            models.map((model) => (
              <button key={model} type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => onSelect(model)}>
                {model}
              </button>
            ))
          ) : (
            <p>Ingen modell hittades.</p>
          )}
        </div>
      )}
    </div>
  );
};

const InfoBox = ({ children }: { children: React.ReactNode }) => (
  <div className="claude-info-box">
    <Info aria-hidden />
    <p>{children}</p>
  </div>
);

const Progress = ({ step }: { step: Exclude<StepKey, "model" | "results"> }) => (
  <div className="claude-progress">
    <div>
      <span style={{ width: `${((stepIndex(step) + 0.5) / FLOW_STEPS.length) * 100}%` }} />
    </div>
    <strong>{stepIndex(step) + 1}/7</strong>
  </div>
);

const DevicePanel = ({
  model,
  storage,
  answers,
  step,
}: {
  model: string;
  storage: string;
  answers: ConditionAnswers;
  step: Exclude<StepKey, "model" | "results">;
}) => {
  const phoneImage = getIphoneImage(model);
  const rows = [
    { key: "storage", label: "Lagring", value: storage ? formatStorage(storage) : "-" },
    { key: "battery", label: "Batteri", value: answers.batteryHealth === null ? "-" : `${answers.batteryHealth} %` },
    {
      key: "function",
      label: "Funktionskoll",
      value: functionalQuestions.every((question) => answers.functional[question.key] !== null) ? "Allt OK" : "-",
    },
    { key: "glass", label: "Skärmglas", value: optionSummary(glassOptions, answers.screenGlass) },
    { key: "wear", label: "Skärmskick", value: optionSummary(wearOptions, answers.screenWear) },
    { key: "sides", label: "Sidor", value: optionSummary(sideOptions, answers.sidesWear) },
    { key: "back", label: "Baksida", value: optionSummary(sideOptions, answers.backWear) },
  ];

  return (
    <aside className="claude-device-panel">
      <div className="claude-device-top">
        <div>
          <p>Du värderar</p>
          <h2>
            {model}
            <Squiggle />
          </h2>
        </div>
        <span>
          <img src={phoneImage} alt={model} />
        </span>
      </div>
      <div className="claude-device-rows">
        {rows.map((row, index) =>
          index <= stepIndex(step) ? (
            <div key={row.key}>
              <span>{row.label}</span>
              <strong className={row.value === "-" ? "empty" : ""}>{row.value}</strong>
            </div>
          ) : null,
        )}
      </div>
    </aside>
  );
};

const MobileStepHeader = ({ model, step, onBack }: { model: string; step: Exclude<StepKey, "model" | "results">; onBack: () => void }) => (
  <div className="claude-mobile-step-head">
    <button type="button" onClick={onBack} aria-label="Tillbaka">
      <ChevronLeft aria-hidden />
    </button>
    <div className="claude-mobile-phone" aria-hidden />
    <div>
      <span>Du värderar</span>
      <strong>{model}</strong>
    </div>
    <em>{stepIndex(step) + 1}/7</em>
  </div>
);

const RadioList = <T extends string>({
  options,
  value,
  onChange,
}: {
  options: Option<T>[];
  value: T | null;
  onChange: (value: T) => void;
}) => (
  <div className="claude-radio-list">
    {options.map((option) => (
      <button key={option.value} type="button" className={value === option.value ? "selected" : ""} onClick={() => onChange(option.value)}>
        <span aria-hidden />
        <strong>{option.label}</strong>
      </button>
    ))}
  </div>
);

const Foot = ({
  onBack,
  onNext,
  disabled,
  loading,
  nextLabel = "Fortsätt",
}: {
  onBack?: () => void;
  onNext: () => void;
  disabled?: boolean;
  loading?: boolean;
  nextLabel?: string;
}) => (
  <div className="claude-foot">
    {onBack ? (
      <button type="button" className="secondary" onClick={onBack} disabled={loading}>
        ← Tillbaka
      </button>
    ) : (
      <span />
    )}
    <button type="button" className="primary" onClick={onNext} disabled={disabled || loading}>
      {loading ? (
        <>
          <Loader2 aria-hidden />
          Beräknar...
        </>
      ) : (
        `${nextLabel} →`
      )}
    </button>
  </div>
);

const UnifiedFlow = ({ onShowResults, onModelSelected, initialModel }: UnifiedFlowProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { addSavedOffer } = useSavedOffers();

  const [step, setStep] = useState<StepKey>(initialModel ? "storage" : "model");
  const [model, setModel] = useState(initialModel ?? "");
  const [storage, setStorage] = useState("");
  const [answers, setAnswers] = useState<ConditionAnswers>(defaultAnswers);
  const [batteryMode, setBatteryMode] = useState<"input" | "cant">("input");
  const [funcIndex, setFuncIndex] = useState(0);
  const [results, setResults] = useState<CompanyOffer[] | null>(null);
  const [resultsTimestamp, setResultsTimestamp] = useState("");
  const [loadingResults, setLoadingResults] = useState(false);
  const [search, setSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState<CompanyOffer | null>(null);
  const [sellDialogOpen, setSellDialogOpen] = useState(false);
  const [savedOfferId, setSavedOfferId] = useState<string | undefined>();

  const filteredModels = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    if (!normalized) return iphoneModels;
    return iphoneModels.filter((item) => item.toLowerCase().includes(normalized));
  }, [search]);

  const availableStorage = model ? storageByModel[model] ?? [] : [];

  useEffect(() => {
    const state = location.state as RestoreLocationState | null;
    if (!state?.restoreFromSavedOffer) return;

    const saved = state.restoreFromSavedOffer;
    setModel(saved.model);
    setStorage(saved.storage);
    setAnswers(saved.condition ?? defaultAnswers);
    if (saved.offers?.length) {
      setResults(saved.offers);
      setStep("results");
      onShowResults?.(true);
      onModelSelected?.(true);
    }
  }, [location.state, onModelSelected, onShowResults]);

  const go = (next: StepKey) => {
    setStep(next);
    onShowResults?.(next === "results");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const selectModel = (selectedModel: string) => {
    setModel(selectedModel);
    setSearch(selectedModel);
    setStorage("");
    setAnswers(defaultAnswers);
    setFuncIndex(0);
    setSearchOpen(false);
    onModelSelected?.(true);
    navigate(`/salja/${modelToSlug(selectedModel)}`);
  };

  const reset = () => {
    setStep("model");
    setModel("");
    setStorage("");
    setSearch("");
    setAnswers(defaultAnswers);
    setResults(null);
    setFuncIndex(0);
    onShowResults?.(false);
    onModelSelected?.(false);
    navigate("/");
  };

  const goBack = () => {
    if (step === "storage") {
      reset();
      return;
    }
    if (step === "function" && funcIndex > 0 && funcIndex < functionalQuestions.length) {
      setFuncIndex((current) => current - 1);
      return;
    }
    if (step === "results") {
      go("back");
      return;
    }

    const index = stepIndex(step);
    if (index > 0) go(FLOW_STEPS[index - 1]);
  };

  const handleFunctionAnswer = (value: boolean) => {
    const question = functionalQuestions[funcIndex];
    if (!question) return;
    const nextFunctional = { ...answers.functional, [question.key]: value };
    setAnswers((current) => ({ ...current, functional: nextFunctional }));

    const next = functionalQuestions.findIndex((candidate, index) => index > funcIndex && nextFunctional[candidate.key] === null);
    const fallback = functionalQuestions.findIndex((candidate) => nextFunctional[candidate.key] === null);
    setFuncIndex(next >= 0 ? next : fallback >= 0 ? fallback : functionalQuestions.length);
  };

  const computeAndShow = async () => {
    const quoteAnswers: ConditionAnswers = {
      ...answers,
      screenFunction: {
        brightSpots: false,
        deadPixels: false,
        linesOrBurnIn: false,
        allWorks: true,
      },
      screenFunctionAnswered: true,
    };

    setLoadingResults(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 800));
      const offers = await fetchQuotes(model, storage, quoteAnswers);
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
      go("results");
    } catch (error) {
      console.error(error);
      toast.error("Kunde inte hämta priser just nu. Försök igen.");
    } finally {
      setLoadingResults(false);
    }
  };

  const handleSelectOffer = (offer: CompanyOffer) => {
    const id = newSavedOfferId();
    addSavedOffer({
      id,
      model,
      storage,
      condition: answers,
      offers: results,
      selectedOffer: offer,
      timestamp: Date.now(),
    });
    setSavedOfferId(id);
    setSelectedOffer(offer);
    setSellDialogOpen(true);
  };

  const renderHome = () => (
    <div className="claude-page">
      <Nav onSell={() => setSearchOpen(true)} />
      <section className="claude-hero">
        <div>
          <h1>
            Hitta <span>bästa priset<Squiggle /></span> för din mobil
          </h1>
          <p className="claude-hand">helt gratis!</p>
          <SearchBox
            search={search}
            setSearch={setSearch}
            open={searchOpen}
            setOpen={setSearchOpen}
            models={filteredModels}
            onSelect={selectModel}
          />
          <div className="claude-pills">
            <span>Tar 30 sek</span>
            <span>Swish / banköverföring</span>
            <span>Fri frakt</span>
          </div>
        </div>
      </section>
      <section className="claude-partners">
        <p>Vi jämför bud från Sveriges återförsäljare</p>
        <div>
          {[...partnerLogos, ...partnerLogos].map((logo, index) => (
            <img key={`${logo}-${index}`} src={logo} alt="" />
          ))}
        </div>
      </section>
      <section id="sa-funkar-det" className="claude-info-section">
        {[
          ["Sök & jämför bud", "Skriv in din modell och se bud från flera återförsäljare direkt.", Search],
          ["Välj & skicka", "Välj det bästa budet och skicka telefonen gratis med fraktsedel.", Truck],
          ["Få betalt", "Återförsäljaren kontrollerar mobilen och betalar ut via Swish eller bank.", Wallet],
        ].map(([title, text, Icon], index) => (
          <article key={String(title)}>
            <span>{index + 1}</span>
            <Icon aria-hidden />
            <h2>{title as string}</h2>
            <p>{text as string}</p>
          </article>
        ))}
      </section>
      <section id="varfor-oss" className="claude-why">
        <h2>Mindre krångel, mer betalt</h2>
        <div>
          <Shield aria-hidden />
          <p>Vi samlar bud, frakt och villkor på ett ställe så att du snabbt hittar bästa köparen.</p>
        </div>
      </section>
    </div>
  );

  const renderStepContent = (currentStep: Exclude<StepKey, "model" | "results">) => {
    if (currentStep === "storage") {
      return (
        <>
          <h1>Hur mycket lagring?</h1>
          <p className="claude-sub">Inställningar → Allmänt → Om → Kapacitet</p>
          <div className="claude-radio-list">
            {availableStorage.map((item) => (
              <button
                key={item}
                type="button"
                className={storage === item ? "selected" : ""}
                onClick={() => {
                  setStorage(item);
                  go("battery");
                }}
              >
                <span aria-hidden />
                <strong>{formatStorage(item)}</strong>
              </button>
            ))}
          </div>
          <Foot onBack={goBack} onNext={() => go("battery")} disabled={!storage} />
        </>
      );
    }

    if (currentStep === "battery") {
      const valid = batteryMode === "cant" || (answers.batteryHealth !== null && answers.batteryHealth >= 1 && answers.batteryHealth <= 100);
      return (
        <>
          <h1>Vad är batterihälsan?</h1>
          <p className="claude-sub">Inställningar → Batteri → Batterihälsa → Maximal kapacitet</p>
          <button type="button" className={batteryMode === "input" ? "claude-battery selected" : "claude-battery"} onClick={() => setBatteryMode("input")}>
            <span aria-hidden />
            <strong>Ange batterikapacitet</strong>
            <div>
              <input
                value={answers.batteryHealth ?? ""}
                type="number"
                min={1}
                max={100}
                placeholder="87"
                onChange={(event) => {
                  setBatteryMode("input");
                  const value = event.target.value;
                  if (!value) {
                    setAnswers((current) => ({ ...current, batteryHealth: null }));
                    return;
                  }
                  const parsed = parseInt(value, 10);
                  if (!Number.isNaN(parsed)) setAnswers((current) => ({ ...current, batteryHealth: Math.max(1, Math.min(100, parsed)) }));
                }}
              />
              <em>%</em>
            </div>
          </button>
          <button
            type="button"
            className={batteryMode === "cant" ? "claude-battery compact selected" : "claude-battery compact"}
            onClick={() => {
              setBatteryMode("cant");
              setAnswers((current) => ({ ...current, batteryHealth: 100 }));
            }}
          >
            <span aria-hidden />
            <strong>Kan inte kontrollera</strong>
            <small>Vi bekräftar kapaciteten åt dig efter inspektion.</small>
          </button>
          <Foot onBack={goBack} onNext={() => go("function")} disabled={!valid} />
        </>
      );
    }

    if (currentStep === "function") {
      const done = functionalQuestions.every((question) => answers.functional[question.key] !== null);
      const active = funcIndex < functionalQuestions.length ? functionalQuestions[funcIndex] : null;

      return (
        <>
          <h1>{done ? "Allt kontrollerat" : "Funktionskoll"}</h1>
          <div className="claude-done-list">
            {functionalQuestions.map((question, index) => {
              const answer = answers.functional[question.key];
              if (answer === null) return null;
              return (
                <div key={question.key}>
                  <span><Check aria-hidden /></span>
                  <strong>{question.label}</strong>
                  <button type="button" onClick={() => setFuncIndex(index)}>Redigera</button>
                </div>
              );
            })}
          </div>
          {active ? (
            <div className="claude-function-card">
              <p>{funcIndex + 1}/{functionalQuestions.length} · Funktionskoll</p>
              <h2>{active.title}</h2>
              <InfoBox>{active.hint}</InfoBox>
              <div>
                {(active.inverted ? [false, true] : [true, false]).map((value) => (
                  <button key={String(value)} type="button" onClick={() => handleFunctionAnswer(value)}>
                    {value ? "Ja" : "Nej"}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          <Foot onBack={goBack} onNext={() => go("glass")} disabled={!done} />
        </>
      );
    }

    const conditionScreens = {
      glass: {
        title: "Hur ser glaset ut?",
        hint: "Håll upp telefonen mot ljuset och titta noga efter sprickor, flisor och repor.",
        options: glassOptions,
        value: answers.screenGlass,
        set: (value: ScreenGlass) => setAnswers((current) => ({ ...current, screenGlass: value })),
        next: () => go("wear"),
      },
      wear: {
        title: "Hur är skärmens skick?",
        hint: "Titta med skärmen på, gärna mot en ljus bakgrund.",
        options: wearOptions,
        value: answers.screenWear,
        set: (value: WearLevel) => setAnswers((current) => ({ ...current, screenWear: value })),
        next: () => go("sides"),
      },
      sides: {
        title: "Hur ser sidorna ut?",
        hint: "Titta längs kanterna och ramens sidor - kika efter repor, bucklor och sprickor.",
        options: sideOptions,
        value: answers.sidesWear,
        set: (value: WearLevelWithCrack) => setAnswers((current) => ({ ...current, sidesWear: value })),
        next: () => go("back"),
      },
      back: {
        title: "Hur ser baksidan ut?",
        hint: "Lägg telefonen med baksidan upp mot ett plant underlag och titta noga.",
        options: sideOptions,
        value: answers.backWear,
        set: (value: WearLevelWithCrack) => setAnswers((current) => ({ ...current, backWear: value })),
        next: computeAndShow,
      },
    }[currentStep];

    return (
      <>
        <h1>{conditionScreens.title}</h1>
        <InfoBox>{conditionScreens.hint}</InfoBox>
        <RadioList
          options={conditionScreens.options}
          value={conditionScreens.value}
          onChange={(value) => conditionScreens.set(value as never)}
        />
        <Foot
          onBack={goBack}
          onNext={conditionScreens.next}
          disabled={!conditionScreens.value}
          loading={currentStep === "back" && loadingResults}
          nextLabel={currentStep === "back" ? "Beräkna bästa bud" : "Fortsätt"}
        />
      </>
    );
  };

  const renderAssessment = () => {
    if (!isFlowStep(step)) return null;

    return (
      <div className="claude-page claude-assessment">
        <Nav onSell={() => go("storage")} />
        <div className="claude-mobile-only">
          <MobileStepHeader model={model} step={step} onBack={goBack} />
          <div className="claude-mobile-progress">
            <span>Steg {stepIndex(step) + 1} av 7</span>
            <em>{STEP_LABELS[step]}</em>
            <div><i style={{ width: `${((stepIndex(step) + 0.5) / FLOW_STEPS.length) * 100}%` }} /></div>
          </div>
          <div className="claude-mobile-step">{renderStepContent(step)}</div>
        </div>

        <div className="claude-desktop-flow">
          <DevicePanel model={model} storage={storage} answers={answers} step={step} />
          <main>
            <Progress step={step} />
            <div className="claude-step-card">{renderStepContent(step)}</div>
          </main>
        </div>
      </div>
    );
  };

  const renderResults = () => {
    if (!results) return null;
    const sorted = [...results].filter((offer) => !offer.notPurchased).sort((a, b) => b.pris - a.pris);
    const best = sorted[0];

    return (
      <div className="claude-page claude-results-page">
        <Nav onSell={() => go("storage")} />
        <main className="claude-results-shell">
          <button type="button" className="claude-back-link" onClick={() => go("back")}>← Tillbaka</button>
          <p>Du värderade <strong>{model} · {formatStorage(storage)}</strong></p>
          <h1>
            Vi hittade ditt <span>bästa bud<Squiggle /></span>
          </h1>
          {best && (
            <section className="claude-best-offer">
              <div>
                <p className="claude-hand">bästa valet ↓</p>
                <h2>{best.företag}</h2>
                <span><Star aria-hidden /> Trustpilot {best.trustpilotScore ?? "-"}</span>
              </div>
              <div>
                <small>Du får</small>
                <strong>{best.pris.toLocaleString("sv-SE")}<em> kr</em><Squiggle /></strong>
                <button type="button" onClick={() => handleSelectOffer(best)}>Sälj till {best.företag} →</button>
              </div>
            </section>
          )}
          <ComparisonTable offers={results} onSelectOffer={handleSelectOffer} />
          {resultsTimestamp && <p className="claude-updated">Priser hämtade: {resultsTimestamp}</p>}
        </main>
        <SellOfferDialog
          open={sellDialogOpen}
          onOpenChange={setSellDialogOpen}
          offer={selectedOffer}
          model={model}
          storage={storage}
          conditionAnswers={answers}
          savedOfferId={savedOfferId}
        />
      </div>
    );
  };

  if (step === "model") return renderHome();
  if (step === "results") return renderResults();
  return renderAssessment();
};

export default UnifiedFlow;
