import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Check, ChevronLeft, Info, Loader2, Search, Shield, Star, Truck, Wallet } from "lucide-react";
import { toast } from "sonner";

import DesktopCommerceFlow from "@/components/DesktopCommerceFlow";
import MobileCommerceFlow from "@/components/MobileCommerceFlow";
import ComparisonTable from "@/components/ComparisonTable";
import SellOfferDialog from "@/components/SellOfferDialog";
import {
  ConditionAnswers,
  ScreenGlass,
  WearLevel,
  WearLevelWithCrack,
  initialConditionAnswers,
} from "@/types/condition";
import type { CompanyOffer } from "@/types/offers";
import { fetchQuotes } from "@/utils/apiQuote";
import { getDefaultIphoneColor, getIphoneColorOptions, getIphoneImage, type IphoneColorOption } from "@/utils/iphoneImage";
import { modelToSlug } from "@/utils/modelSlug";
import { trackEvent, trackStepView } from "@/utils/tracking";
import { useIphoneCatalog } from "@/hooks/useIphoneCatalog";
import { useSavedOffers } from "@/hooks/useSavedOffers";
import type { SavedOffer } from "@/types/savedOffers";

import cmpLogo from "@/assets/televera-logo-full.png";
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
  initialStepSlug?: string;
}

interface RestoreLocationState {
  restoreFromSavedOffer?: SavedOffer;
}

type StepKey = "model" | "color" | "storage" | "battery" | "screen" | "display" | "sides" | "back" | "function" | "results";
type ScreenConditionMode = "perfect" | "micro" | "lightScratches" | "visibleScratches" | "deepScratches" | "chipped";

type Option<T extends string> = {
  value: T;
  label: string;
  summary: string;
};

const FLOW_STEPS: Exclude<StepKey, "model" | "results">[] = [
  "color",
  "storage",
  "battery",
  "display",
  "screen",
  "sides",
  "back",
  "function",
];

const STEP_LABELS: Record<Exclude<StepKey, "model" | "results">, string> = {
  color: "Färg",
  storage: "Lagring",
  battery: "Batteri",
  screen: "Skärm",
  display: "Bild/touch",
  sides: "Sidor",
  back: "Baksida",
  function: "Funktionskoll",
};

const STEP_SLUGS: Record<Exclude<StepKey, "model">, string> = {
  color: "farg",
  storage: "lagring",
  battery: "batteri",
  display: "skarm-funktion",
  screen: "skarm-skick",
  sides: "sidor",
  back: "baksida",
  function: "funktion",
  results: "resultat",
};

const SLUG_TO_STEP = Object.fromEntries(
  Object.entries(STEP_SLUGS).map(([step, slug]) => [slug, step]),
) as Record<string, Exclude<StepKey, "model">>;

const quoteStepEventName = (step: Exclude<StepKey, "model" | "results">, action: "viewed" | "completed") =>
  `quote_step_${step}_${action}`;

const LEGACY_FORM_QUERY = "legacyForm";

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
  { value: "none", label: "Som ny", summary: "Som ny" },
];

const screenConditionOptions: {
  value: ScreenConditionMode;
  label: string;
  glass: ScreenGlass;
  wear: WearLevel;
}[] = [
  { value: "perfect", label: "Som ny", glass: "none", wear: "none" },
  { value: "micro", label: "Mikrorepor", glass: "none", wear: "minimal" },
  { value: "lightScratches", label: "Lätta repor", glass: "none", wear: "some" },
  { value: "visibleScratches", label: "Tydliga repor", glass: "none", wear: "visible" },
  { value: "deepScratches", label: "Djupa repor", glass: "scratched", wear: "visible" },
  { value: "chipped", label: "Sprickor/flisor", glass: "chipped", wear: "visible" },
];

const sideOptions: Option<WearLevelWithCrack>[] = [
  { value: "none", label: "Som nya", summary: "Som nya" },
  { value: "minimal", label: "Mikrorepor", summary: "Mikrorepor" },
  { value: "some", label: "Lätta repor", summary: "Lätta repor" },
  { value: "visible", label: "Repor/bucklor", summary: "Repor/bucklor" },
  { value: "cracked", label: "Spruckna", summary: "Spruckna" },
];

const backOptions: Option<WearLevelWithCrack>[] = [
  { value: "none", label: "Som ny", summary: "Som ny" },
  { value: "minimal", label: "Mikrorepor", summary: "Mikrorepor" },
  { value: "some", label: "Lätta repor", summary: "Lätta repor" },
  { value: "visible", label: "Tydliga repor", summary: "Tydliga repor" },
  { value: "cracked", label: "Sprucken", summary: "Sprucken" },
];

const functionalIssueOptions: {
  key: keyof ConditionAnswers["functional"];
  label: string;
  summary: string;
}[] = [
  { key: "powersOn", label: "Startar inte", summary: "Startar inte" },
  { key: "faceId", label: "Face ID / Touch ID fungerar inte", summary: "Face ID" },
  { key: "network", label: "Nätverk eller SIM fungerar inte", summary: "Nätverk" },
  { key: "selfieCamera", label: "Selfie-kameran fungerar inte", summary: "Selfie-kamera" },
  { key: "rearCamera", label: "Bakre kameran fungerar inte", summary: "Kamera" },
  { key: "speaker", label: "Högtalare eller mikrofon fungerar inte", summary: "Ljud" },
  { key: "chargingOrButtons", label: "Laddning eller knappar fungerar inte", summary: "Laddning/knappar" },
  { key: "other", label: "Annat fel", summary: "Annat fel" },
];

const screenFunctionOptions: {
  key: keyof ConditionAnswers["screenFunction"];
  label: string;
  summary: string;
}[] = [
  { key: "brightSpots", label: "Ljusa fläckar", summary: "Fläckar" },
  { key: "deadPixels", label: "Döda pixlar", summary: "Pixlar" },
  { key: "linesOrBurnIn", label: "Linjer eller inbränning", summary: "Linjer/inbränning" },
  { key: "touchIssue", label: "Touchproblem", summary: "Touch" },
];

const physicalFunctionIssueOptions: {
  key: keyof NonNullable<ConditionAnswers["critical"]>;
  label: string;
  summary: string;
}[] = [
  { key: "bent", label: "Telefonen är böjd", summary: "Böjd" },
  { key: "waterDamaged", label: "Fuktskada eller vattenskada", summary: "Fuktskada" },
];

const defaultAnswers: ConditionAnswers = {
  ...initialConditionAnswers,
  screenFunction: {
    brightSpots: false,
    deadPixels: false,
    linesOrBurnIn: false,
    touchIssue: false,
    allWorks: true,
  },
  screenFunctionAnswered: true,
};

const formatStorage = (storage: string) => storage.replace(/^(\d+)(GB)$/i, "$1 GB").replace(/^(\d+)TB$/i, "$1 TB");
const stepIndex = (step: StepKey) => FLOW_STEPS.indexOf(step as Exclude<StepKey, "model" | "results">);
const isFlowStep = (step: StepKey): step is Exclude<StepKey, "model" | "results"> => FLOW_STEPS.includes(step as Exclude<StepKey, "model" | "results">);
const optionSummary = <T extends string>(options: Option<T>[], value: T | null) => options.find((option) => option.value === value)?.summary ?? "-";
const newSavedOfferId = () => (crypto.randomUUID ? crypto.randomUUID() : `offer-${Date.now()}`);
const isLegacyFormEnabled = () => new URLSearchParams(window.location.search).has(LEGACY_FORM_QUERY);
const deriveScreenConditionMode = (answers: ConditionAnswers): ScreenConditionMode | null => {
  if (!answers.screenGlass || !answers.screenWear) return null;
  if (answers.screenGlass === "chipped") return "chipped";
  if (answers.screenGlass === "scratched") return "deepScratches";
  if (answers.screenWear === "visible") return "visibleScratches";
  if (answers.screenWear === "some") return "lightScratches";
  if (answers.screenWear === "minimal") return "micro";
  return "perfect";
};
const deriveScreenFaultMode = (answers: ConditionAnswers): "works" | "faults" | null => {
  if (!answers.screenFunctionAnswered) return null;
  return answers.screenFunction.allWorks ? "works" : "faults";
};

const allFunctionalOk = (answers: ConditionAnswers) =>
  functionalIssueOptions.every((option) => answers.functional[option.key] !== false) &&
  physicalFunctionIssueOptions.every((option) => !answers.critical?.[option.key]);

const hasAnsweredFunction = (answers: ConditionAnswers) =>
  answers.functional.powersOn !== null;

const functionSummary = (answers: ConditionAnswers) => {
  if (!hasAnsweredFunction(answers)) return "-";
  if (allFunctionalOk(answers)) return "Allt OK";
  const issues = functionalIssueOptions
    .filter((option) => answers.functional[option.key] === false)
    .map((option) => option.summary);
  const physicalIssues = physicalFunctionIssueOptions
    .filter((option) => answers.critical?.[option.key])
    .map((option) => option.summary);
  const allIssues = [...issues, ...physicalIssues];
  return allIssues.length ? allIssues.join(", ") : "Fel finns";
};

const persistedFlowKey = (model: string) => `televera:flow:${modelToSlug(model)}`;

const getFirstIncompleteStep = ({
  color,
  storage,
  answers,
  batteryMode,
  screenConditionMode,
  screenFaultMode,
  functionMode,
}: {
  color: string;
  storage: string;
  answers: ConditionAnswers;
  batteryMode: "input" | "cant" | null;
  screenConditionMode: ScreenConditionMode | null;
  screenFaultMode: "works" | "faults" | null;
  functionMode: "yes" | "no" | null;
}): Exclude<StepKey, "model" | "results"> => {
  if (!color) return "color";
  if (!storage) return "storage";
  if (!(batteryMode === "cant" || (answers.batteryHealth !== null && answers.batteryHealth >= 1 && answers.batteryHealth <= 100))) return "battery";
  if (!screenFaultMode) return "display";
  if (!screenConditionMode || !answers.screenGlass || !answers.screenWear) return "screen";
  if (!answers.sidesWear) return "sides";
  if (!answers.backWear) return "back";
  if (!functionMode) return "function";
  return "function";
};

const screenSummary = (answers: ConditionAnswers) => {
  const glass = optionSummary(glassOptions, answers.screenGlass);
  const wear = optionSummary(wearOptions, answers.screenWear);
  const parts = [];
  if (wear !== "-") parts.push(wear);
  if (glass !== "-" && glass !== "Inga skador") parts.unshift(glass);
  if (answers.screenFunctionAnswered && !answers.screenFunction.allWorks) {
    const faults = screenFunctionOptions
      .filter((option) => Boolean(answers.screenFunction[option.key]))
      .map((option) => option.summary);
    parts.push(faults.length ? faults.join(", ") : "Skärmfel");
  }
  return parts.length ? parts.join(" · ") : "-";
};

const Nav = ({ onSell }: { onSell: () => void }) => (
  <nav className="claude-nav">
    <a className="claude-brand" href="/">
      <img src={cmpLogo} alt="Televera" />
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
                <span className="claude-search-thumb" aria-hidden>
                  <img src={getIphoneImage(model)} alt="" loading="lazy" decoding="async" />
                </span>
                <span>{model}</span>
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
      <span style={{ width: `${((stepIndex(step) + 1) / FLOW_STEPS.length) * 100}%` }} />
    </div>
    <strong>{stepIndex(step) + 1}/{FLOW_STEPS.length}</strong>
  </div>
);

const DevicePanel = ({
  model,
  color,
  storage,
  answers,
  step,
}: {
  model: string;
  color: string;
  storage: string;
  answers: ConditionAnswers;
  step: Exclude<StepKey, "model" | "results">;
}) => {
  const phoneImage = getIphoneImage(model, color);
  const selectedColor = getIphoneColorOptions(model).find((option) => option.value === color);
  const rows = [
    { key: "color", label: "Färg", value: selectedColor?.label ?? "-" },
    { key: "storage", label: "Lagring", value: storage ? formatStorage(storage) : "-" },
    { key: "battery", label: "Batteri", value: answers.batteryHealth === null ? "-" : `${answers.batteryHealth}%` },
    { key: "screen", label: "Skärm", value: screenSummary(answers) },
    { key: "sides", label: "Sidor", value: optionSummary(sideOptions, answers.sidesWear) },
    { key: "back", label: "Baksida", value: optionSummary(backOptions, answers.backWear) },
    { key: "function", label: "Funktionskoll", value: functionSummary(answers) },
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

const MobileStepHeader = ({
  model,
  color,
  step,
  onBack,
}: {
  model: string;
  color: string;
  step: Exclude<StepKey, "model" | "results">;
  onBack: () => void;
}) => (
  <div className="claude-mobile-step-head">
    <button type="button" onClick={onBack} aria-label="Tillbaka">
      <ChevronLeft aria-hidden />
    </button>
    <div className="claude-mobile-phone">
      <img src={getIphoneImage(model, color)} alt="" />
    </div>
    <div>
      <span>Du värderar</span>
      <strong>{model}</strong>
    </div>
    <em>{stepIndex(step) + 1}/{FLOW_STEPS.length}</em>
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

const UnifiedFlow = ({ onShowResults, onModelSelected, initialModel, initialStepSlug }: UnifiedFlowProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { addSavedOffer } = useSavedOffers();
  const requestedInitialStep = initialStepSlug ? SLUG_TO_STEP[initialStepSlug] : undefined;

  const [step, setStep] = useState<StepKey>(initialModel ? requestedInitialStep ?? "color" : "model");
  const [model, setModel] = useState(initialModel ?? "");
  const [color, setColor] = useState("");
  const [storage, setStorage] = useState("");
  const [answers, setAnswers] = useState<ConditionAnswers>(defaultAnswers);
  const [batteryMode, setBatteryMode] = useState<"input" | "cant" | null>(null);
  const [functionMode, setFunctionMode] = useState<"yes" | "no" | null>(null);
  const [screenConditionMode, setScreenConditionMode] = useState<ScreenConditionMode | null>(null);
  const [screenFaultMode, setScreenFaultMode] = useState<"works" | "faults" | null>(null);
  const [funcIndex, setFuncIndex] = useState(0);
  const [results, setResults] = useState<CompanyOffer[] | null>(null);
  const [submittedAnswers, setSubmittedAnswers] = useState<ConditionAnswers | null>(null);
  const [resultsTimestamp, setResultsTimestamp] = useState("");
  const [loadingResults, setLoadingResults] = useState(false);
  const [search, setSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState<CompanyOffer | null>(null);
  const [sellDialogOpen, setSellDialogOpen] = useState(false);
  const [savedOfferId, setSavedOfferId] = useState<string | undefined>();
  const flowRootRef = useRef<HTMLDivElement>(null);
  const functionCardRef = useRef<HTMLDivElement>(null);
  const viewedAtRef = useRef(Date.now());
  const { models: iphoneModels, storageByModel } = useIphoneCatalog();
  const legacyForm = isLegacyFormEnabled();

  const filteredModels = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    if (!normalized) return iphoneModels;
    return iphoneModels.filter((item) => item.toLowerCase().includes(normalized));
  }, [iphoneModels, search]);

  const availableStorage = model ? storageByModel[model] ?? [] : [];
  const availableColors = useMemo(() => (model ? getIphoneColorOptions(model) : []), [model]);

  useEffect(() => {
    if (!initialModel) return;
    const persisted = (() => {
      try {
        return JSON.parse(sessionStorage.getItem(persistedFlowKey(initialModel)) || "null") as {
          color?: string;
          storage?: string;
          answers?: ConditionAnswers;
          batteryMode?: "input" | "cant" | null;
          functionMode?: "yes" | "no" | null;
          screenConditionMode?: ScreenConditionMode | null;
          screenFaultMode?: "works" | "faults" | null;
          funcIndex?: number;
        } | null;
      } catch {
        return null;
      }
    })();

    if (!persisted) return;
    const restoredAnswers = persisted.answers ?? defaultAnswers;
    setColor(persisted.color ?? "");
    setStorage(persisted.storage ?? "");
    setAnswers(restoredAnswers);
    setBatteryMode(persisted.batteryMode ?? null);
    setFunctionMode(persisted.functionMode ?? null);
    setScreenConditionMode(persisted.screenConditionMode ?? deriveScreenConditionMode(restoredAnswers));
    setScreenFaultMode(persisted.screenFaultMode ?? deriveScreenFaultMode(restoredAnswers));
    setFuncIndex(persisted.funcIndex ?? 0);
  }, [initialModel]);

  useEffect(() => {
    if (!model || step === "model") return;
    try {
      sessionStorage.setItem(
        persistedFlowKey(model),
        JSON.stringify({
          color,
          storage,
          answers,
          batteryMode,
          functionMode,
          screenConditionMode,
          screenFaultMode,
          funcIndex,
        }),
      );
    } catch {
      // Storage is a convenience for refresh recovery; the flow still works without it.
    }
  }, [answers, batteryMode, color, funcIndex, functionMode, model, screenConditionMode, screenFaultMode, step, storage]);

  useEffect(() => {
    if (!initialModel || !requestedInitialStep || requestedInitialStep === "results") return;
    const firstIncomplete = getFirstIncompleteStep({
      color,
      storage,
      answers,
      batteryMode,
      screenConditionMode,
      screenFaultMode,
      functionMode,
    });
    if (stepIndex(requestedInitialStep) > stepIndex(firstIncomplete)) {
      setStep(firstIncomplete);
    }
  }, [answers, batteryMode, color, functionMode, initialModel, requestedInitialStep, screenConditionMode, screenFaultMode, storage]);

  useEffect(() => {
    if (!model || step === "model") return;
    const slug = STEP_SLUGS[step as Exclude<StepKey, "model">];
    if (!slug) return;
    const modelPath = `/salja/${modelToSlug(model)}`;
    const hasStepInPath = location.pathname.startsWith(`${modelPath}/`);
    const stepPath = step === "color" && !hasStepInPath ? modelPath : `${modelPath}/${slug}`;
    const target = `${stepPath}${location.search}`;
    if (`${location.pathname}${location.search}` !== target) {
      navigate(target, { replace: true });
    }
  }, [location.pathname, location.search, model, navigate, step]);

  useEffect(() => {
    const now = Date.now();
    viewedAtRef.current = now;
    if (step === "model") {
      trackStepView("landing_viewed", { funnel: "quote" });
      return;
    }
    if (step === "results") {
      trackStepView("quote_results_viewed", {
        funnel: "quote",
        model,
        storage,
        offer_count: results?.length ?? 0,
        best_price: results?.[0]?.pris,
      });
      return;
    }
    const stepPayload = {
      funnel: "quote",
      step,
      step_label: STEP_LABELS[step],
      step_index: stepIndex(step) + 1,
      model,
      storage,
    };
    trackStepView("quote_step_viewed", stepPayload);
    trackStepView(quoteStepEventName(step, "viewed"), stepPayload);
  }, [model, results, step, storage]);

  const trackStepCompleted = (completedStep: StepKey, extra: Record<string, string | number | boolean | null | undefined> = {}) => {
    if (completedStep === "model") return;
    const stepPayload = {
      funnel: "quote",
      step: completedStep,
      step_index: isFlowStep(completedStep) ? stepIndex(completedStep) + 1 : undefined,
      step_label: isFlowStep(completedStep) ? STEP_LABELS[completedStep] : undefined,
      model,
      storage,
      duration_ms: Date.now() - viewedAtRef.current,
      ...extra,
    };
    trackEvent("quote_step_completed", stepPayload);
    if (isFlowStep(completedStep)) {
      trackEvent(quoteStepEventName(completedStep, "completed"), stepPayload);
    }
  };

  useEffect(() => {
    const state = location.state as RestoreLocationState | null;
    if (!state?.restoreFromSavedOffer) return;

    const saved = state.restoreFromSavedOffer;
    setModel(saved.model);
    setColor(saved.color ?? "");
    setStorage(saved.storage);
    const restoredCondition = saved.condition ?? defaultAnswers;
    setAnswers(restoredCondition);
    setSubmittedAnswers(saved.condition ?? null);
    setFunctionMode(hasAnsweredFunction(restoredCondition) ? (allFunctionalOk(restoredCondition) ? "yes" : "no") : null);
    setScreenConditionMode(deriveScreenConditionMode(restoredCondition));
    setScreenFaultMode(deriveScreenFaultMode(restoredCondition));
    if (saved.offers?.length) {
      setResults(saved.offers);
      setStep("results");
      onShowResults?.(true);
      onModelSelected?.(true);
    }
  }, [location.state, onModelSelected, onShowResults]);

  const scrollToFlowTop = () => {
    const scroll = () => {
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      document.scrollingElement?.scrollTo({ top: 0, left: 0, behavior: "auto" });
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
      flowRootRef.current?.scrollIntoView({ behavior: "auto", block: "start" });
    };

    scroll();
    requestAnimationFrame(scroll);
    setTimeout(scroll, 60);
    setTimeout(scroll, 180);
  };

  const scrollToFunctionQuestion = () => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        functionCardRef.current?.scrollIntoView({ behavior: "auto", block: "start" });
      });
    });
  };

  const go = (next: StepKey, options: { completeCurrent?: boolean } = {}) => {
    if (options.completeCurrent ?? true) trackStepCompleted(step);
    setStep(next);
    onShowResults?.(next === "results");
    scrollToFlowTop();
  };

  useEffect(() => {
    if (step === "function") return;
    if (step === "model") return;
    scrollToFlowTop();
  }, [step]);

  const selectModel = (selectedModel: string) => {
    setModel(selectedModel);
    setSearch(selectedModel);
    setColor("");
    setStorage("");
    setAnswers(defaultAnswers);
    setSubmittedAnswers(null);
    setBatteryMode(null);
    setFunctionMode(null);
    setScreenConditionMode(null);
    setScreenFaultMode(null);
    setFuncIndex(0);
    setSearchOpen(false);
    onModelSelected?.(true);
    trackEvent("model_selected", {
      funnel: "quote",
      model: selectedModel,
    });
    navigate(`/salja/${modelToSlug(selectedModel)}${location.search}`);
  };

  const reset = () => {
    setStep("model");
    setModel("");
    setColor("");
    setStorage("");
    setSearch("");
    setAnswers(defaultAnswers);
    setSubmittedAnswers(null);
    setBatteryMode(null);
    setFunctionMode(null);
    setScreenConditionMode(null);
    setScreenFaultMode(null);
    setResults(null);
    setFuncIndex(0);
    onShowResults?.(false);
    onModelSelected?.(false);
    navigate("/");
  };

  const goBack = () => {
    if (step === "color") {
      reset();
      return;
    }
    if (legacyForm && step === "function" && funcIndex > 0 && funcIndex < functionalQuestions.length) {
      setFuncIndex((current) => current - 1);
      scrollToFunctionQuestion();
      return;
    }
    if (step === "results") {
      go(FLOW_STEPS[FLOW_STEPS.length - 1], { completeCurrent: false });
      return;
    }

    const index = stepIndex(step);
    if (index > 0) go(FLOW_STEPS[index - 1], { completeCurrent: false });
  };

  const handleFunctionAnswer = (value: boolean) => {
    const question = functionalQuestions[funcIndex];
    if (!question) return;
    const nextFunctional = { ...answers.functional, [question.key]: value };
    setAnswers((current) => ({ ...current, functional: nextFunctional }));

    const next = functionalQuestions.findIndex((candidate, index) => index > funcIndex && nextFunctional[candidate.key] === null);
    const fallback = functionalQuestions.findIndex((candidate) => nextFunctional[candidate.key] === null);
    const nextIndex = next >= 0 ? next : fallback >= 0 ? fallback : functionalQuestions.length;
    setFuncIndex(nextIndex);
    if (nextIndex < functionalQuestions.length) {
      scrollToFunctionQuestion();
    } else {
      scrollToFlowTop();
    }
  };

  const computeAndShow = async () => {
    const critical = answers.critical ?? initialConditionAnswers.critical;
    const quoteAnswers: ConditionAnswers = {
      ...answers,
      functional: {
        ...answers.functional,
        bentOrWaterDamaged: Boolean(critical?.bent || critical?.waterDamaged),
      },
      critical,
      screenFunctionAnswered: true,
    };

    setLoadingResults(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 800));
      const offers = await fetchQuotes(model, storage, quoteAnswers);
      setResults(offers);
      setSubmittedAnswers(quoteAnswers);
      setResultsTimestamp(offers[0]?.uppdaterad ?? "");
      trackEvent("quote_submitted", {
        funnel: "quote",
        model,
        storage,
        offer_count: offers.length,
        best_price: offers[0]?.pris,
      });
      go("results");
    } catch (error) {
      console.error(error);
      toast.error("Kunde inte hämta priser just nu. Försök igen.");
    } finally {
      setLoadingResults(false);
    }
  };

  const handleSelectOffer = (offer: CompanyOffer) => {
    trackEvent("offer_selected", {
      funnel: "quote",
      model,
      storage,
      dealer: offer.företag,
      price: offer.pris,
    });
    const id = newSavedOfferId();
    addSavedOffer({
      id,
      model,
      storage,
      color,
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
          ["Välj köpare", "Välj det bästa budet och följ köparens instruktioner.", Truck],
          ["Slutför affären", "Köparen kontrollerar mobilen och betalar ut enligt sina villkor.", Wallet],
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
    if (currentStep === "color") {
      return (
        <>
          <h1>Vilken färg är den?</h1>
          <InfoBox>Välj färgen på din {model}.</InfoBox>
          <div className="claude-color-grid">
            {availableColors.map((option: IphoneColorOption) => {
              const selected = color === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  className={selected ? "selected" : ""}
                  onClick={() => setColor(option.value)}
                >
                  <span className="claude-color-phone">
                    <img src={option.image} alt="" />
                  </span>
                  <span className="claude-color-meta">
                    <strong>{option.label}</strong>
                  </span>
                </button>
              );
            })}
          </div>
          <Foot onBack={goBack} onNext={() => go("storage")} disabled={!color} />
        </>
      );
    }

    if (currentStep === "storage") {
      return (
        <>
          <h1>Hur mycket lagring?</h1>
          <InfoBox>Inställningar → Allmänt → Om → Kapacitet</InfoBox>
          <div className="claude-radio-list">
            {availableStorage.map((item) => (
              <button
                key={item}
                type="button"
                className={storage === item ? "selected" : ""}
                onClick={() => setStorage(item)}
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
          <InfoBox>Inställningar → Batteri → Batterihälsa → Maximal kapacitet</InfoBox>
          <button type="button" className={batteryMode === "input" ? "claude-battery selected" : "claude-battery"} onClick={() => setBatteryMode("input")}>
            <span aria-hidden />
            <strong>Ange batterikapacitet</strong>
            <div>
              <input
                value={answers.batteryHealth ?? ""}
                type="number"
                inputMode="numeric"
                pattern="[0-9]*"
                min={1}
                max={100}
                placeholder="Använd siffror (t.ex. 89)"
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
              setAnswers((current) => ({ ...current, batteryHealth: null }));
            }}
          >
            <span aria-hidden />
            <strong>Kan inte kontrollera</strong>
            <small>Vi bekräftar kapaciteten åt dig efter inspektion.</small>
          </button>
          <Foot onBack={goBack} onNext={() => go("display")} disabled={!valid} />
        </>
      );
    }

    if (currentStep === "function") {
      if (!legacyForm) {
        const issues = functionalIssueOptions.filter((option) => answers.functional[option.key] === false);
        const physicalIssues = physicalFunctionIssueOptions.filter((option) => answers.critical?.[option.key]);
        const done = functionMode === "yes" || (functionMode === "no" && (issues.length > 0 || physicalIssues.length > 0));

        const setAllWorks = () => {
          setFunctionMode("yes");
          setAnswers((current) => ({
            ...current,
            functional: {
              ...current.functional,
              powersOn: true,
              network: true,
              faceId: true,
              selfieCamera: true,
              rearCamera: true,
              speaker: true,
              chargingOrButtons: true,
              other: true,
              bentOrWaterDamaged: false,
            },
            critical: { ...initialConditionAnswers.critical! },
          }));
        };

        const setHasIssues = () => {
          setFunctionMode("no");
        };

        const toggleIssue = (key: keyof ConditionAnswers["functional"]) => {
          setFunctionMode("no");
          setAnswers((current) => {
            const selected = current.functional[key] === false;
            const nextFunctional = {
              ...current.functional,
              powersOn: current.functional.powersOn ?? true,
              network: current.functional.network ?? true,
              faceId: current.functional.faceId ?? true,
              selfieCamera: current.functional.selfieCamera ?? true,
              rearCamera: current.functional.rearCamera ?? true,
              speaker: current.functional.speaker ?? true,
              chargingOrButtons: current.functional.chargingOrButtons ?? true,
              other: current.functional.other ?? true,
              bentOrWaterDamaged: current.functional.bentOrWaterDamaged ?? false,
              [key]: selected ? true : false,
            };
            return { ...current, functional: nextFunctional };
          });
        };

        const togglePhysicalIssue = (key: keyof NonNullable<ConditionAnswers["critical"]>) => {
          setFunctionMode("no");
          setAnswers((current) => {
            const nextCritical = {
              ...(current.critical ?? initialConditionAnswers.critical!),
              [key]: !(current.critical ?? initialConditionAnswers.critical!)[key],
            };
            return {
              ...current,
              critical: nextCritical,
              functional: {
                ...current.functional,
                bentOrWaterDamaged: Boolean(nextCritical.bent || nextCritical.waterDamaged),
              },
            };
          });
        };

        return (
          <>
            <h1>Fungerar telefonen som den ska?</h1>
            <InfoBox>Välj Ja om allt fungerar normalt. Om något är fel kan du välja Nej och markera det som inte fungerar.</InfoBox>
            <div className="claude-radio-list">
              <button type="button" className={functionMode === "yes" ? "selected" : ""} onClick={setAllWorks}>
                <span aria-hidden />
                <strong>Ja</strong>
              </button>
              <button type="button" className={functionMode === "no" ? "selected" : ""} onClick={setHasIssues}>
                <span aria-hidden />
                <strong>Nej</strong>
              </button>
            </div>
            {functionMode === "no" ? (
              <div className="claude-dropdown-panel">
                <h2>Vad fungerar inte?</h2>
                <div className="claude-checkbox-list">
                  {functionalIssueOptions.map((option) => {
                    const selected = answers.functional[option.key] === false;
                    return (
                      <button key={option.key} type="button" className={selected ? "selected" : ""} onClick={() => toggleIssue(option.key)}>
                        <span aria-hidden />
                        <strong>{option.label}</strong>
                      </button>
                    );
                  })}
                  {physicalFunctionIssueOptions.map((option) => {
                    const selected = Boolean(answers.critical?.[option.key]);
                    return (
                      <button key={option.key} type="button" className={selected ? "selected" : ""} onClick={() => togglePhysicalIssue(option.key)}>
                        <span aria-hidden />
                        <strong>{option.label}</strong>
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : null}
            <Foot onBack={goBack} onNext={computeAndShow} disabled={!done} loading={loadingResults} nextLabel="Beräkna bästa bud" />
          </>
        );
      }

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
                  <button type="button" onClick={() => {
                    setFuncIndex(index);
                    scrollToFunctionQuestion();
                  }}>Redigera</button>
                </div>
              );
            })}
          </div>
          {active ? (
            <div className="claude-function-card" ref={functionCardRef}>
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
          <Foot onBack={goBack} onNext={computeAndShow} disabled={!done} loading={loadingResults} nextLabel="Beräkna bästa bud" />
        </>
      );
    }

    const conditionScreens = {
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
        options: backOptions,
        value: answers.backWear,
        set: (value: WearLevelWithCrack) => setAnswers((current) => ({ ...current, backWear: value })),
        next: () => go("function"),
      },
    }[currentStep as "sides" | "back"];

    if (currentStep === "screen") {
      const screenValid = Boolean(screenConditionMode && answers.screenGlass && answers.screenWear);
      const selectScreenCondition = (option: (typeof screenConditionOptions)[number]) => {
        setScreenConditionMode(option.value);
        setAnswers((current) => ({
          ...current,
          screenGlass: option.glass,
          screenWear: option.wear,
        }));
      };

      return (
        <>
          <h1>Hur är skärmens skick?</h1>
          <InfoBox>Välj det alternativ som passar bäst.</InfoBox>
          <div className="claude-radio-list">
            {screenConditionOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                className={screenConditionMode === option.value ? "selected" : ""}
                onClick={() => selectScreenCondition(option)}
              >
                <span aria-hidden />
                <strong>{option.label}</strong>
              </button>
            ))}
          </div>
          <Foot onBack={goBack} onNext={() => go("sides")} disabled={!screenValid} />
        </>
      );
    }

    if (currentStep === "display") {
      const selectedScreenFaults = screenFunctionOptions.filter((option) => Boolean(answers.screenFunction[option.key]));
      const displayValid = screenFaultMode === "works" || (screenFaultMode === "faults" && selectedScreenFaults.length > 0);
      const setScreenWorks = () => {
        setScreenFaultMode("works");
        setAnswers((current) => ({
          ...current,
          screenFunction: {
            brightSpots: false,
            deadPixels: false,
            linesOrBurnIn: false,
            touchIssue: false,
            allWorks: true,
          },
          screenFunctionAnswered: true,
        }));
      };
      const setScreenHasFaults = () => {
        setScreenFaultMode("faults");
        setAnswers((current) => ({
          ...current,
          screenFunction: {
            ...current.screenFunction,
            allWorks: false,
          },
          screenFunctionAnswered: true,
        }));
      };
      const toggleScreenFault = (key: keyof ConditionAnswers["screenFunction"]) => {
        setScreenFaultMode("faults");
        setAnswers((current) => {
          const next = {
            ...current.screenFunction,
            [key]: !current.screenFunction[key],
          };
          const hasFault = screenFunctionOptions.some((option) => Boolean(next[option.key]));
          return {
            ...current,
            screenFunction: {
              ...next,
              allWorks: !hasFault,
            },
            screenFunctionAnswered: true,
          };
        });
      };

      return (
        <>
          <h1>Fungerar bild och touch?</h1>
          <InfoBox>Välj Ja om skärmen visar bilden normalt och touch fungerar över hela skärmen.</InfoBox>
          <div className="claude-radio-list">
            <button type="button" className={screenFaultMode === "works" ? "selected" : ""} onClick={setScreenWorks}>
              <span aria-hidden />
              <strong>Ja</strong>
            </button>
            <button type="button" className={screenFaultMode === "faults" ? "selected" : ""} onClick={setScreenHasFaults}>
              <span aria-hidden />
              <strong>Nej</strong>
            </button>
          </div>
          {screenFaultMode === "faults" ? (
            <div className="claude-dropdown-panel compact">
              <div className="claude-checkbox-list compact">
                {screenFunctionOptions.map((option) => {
                  const selected = Boolean(answers.screenFunction[option.key]);
                  return (
                    <button key={option.key} type="button" className={selected ? "selected" : ""} onClick={() => toggleScreenFault(option.key)}>
                      <span aria-hidden />
                      <strong>{option.label}</strong>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : null}
          <Foot onBack={goBack} onNext={() => go("screen")} disabled={!displayValid} />
        </>
      );
    }

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
        />
      </>
    );
  };

  const renderAssessment = () => {
    if (!isFlowStep(step)) return null;

    return (
      <div className="claude-page claude-assessment" ref={flowRootRef}>
        <div className="claude-mobile-only">
          <MobileStepHeader model={model} color={color} step={step} onBack={goBack} />
          <div className="claude-mobile-progress">
            <span>Steg {stepIndex(step) + 1} av {FLOW_STEPS.length}</span>
            <em>{STEP_LABELS[step]}</em>
            <div><i style={{ width: `${((stepIndex(step) + 0.5) / FLOW_STEPS.length) * 100}%` }} /></div>
          </div>
          <div className="claude-mobile-step">{renderStepContent(step)}</div>
        </div>

        <div className="claude-desktop-flow">
          <Progress step={step} />
          <DevicePanel model={model} color={color} storage={storage} answers={answers} step={step} />
          <main>
            <div className="claude-step-card">{renderStepContent(step)}</div>
          </main>
        </div>
      </div>
    );
  };

  const renderResults = () => {
    if (!results) return null;

    return (
      <div className="claude-page claude-results-page" ref={flowRootRef}>
        <div className="cmp-commerce-desktop-only">
          <DesktopCommerceFlow
            offers={results}
            model={model}
            storage={formatStorage(storage)}
            color={color}
            conditionAnswers={(submittedAnswers ?? answers) as unknown as Record<string, unknown>}
            updated={resultsTimestamp}
            onBack={() => go("back", { completeCurrent: false })}
          />
        </div>
        <div className="cmp-commerce-mobile-only">
          <MobileCommerceFlow
            offers={results}
            model={model}
            storage={formatStorage(storage)}
            color={color}
            conditionAnswers={(submittedAnswers ?? answers) as unknown as Record<string, unknown>}
            onBack={() => go("back", { completeCurrent: false })}
          />
        </div>
      </div>
    );
  };

  if (step === "model") return renderHome();
  if (step === "results") return renderResults();
  return renderAssessment();
};

export default UnifiedFlow;
