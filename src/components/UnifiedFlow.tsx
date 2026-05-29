import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Check, CheckCircle2, Zap, Lock, Loader2, Search } from "lucide-react";
import {
  ConditionAnswers,
  initialConditionAnswers,
  WearLevel,
  WearLevelWithCrack,
  ScreenGlass,
} from "@/types/condition";
import { iphoneModels, storageByModel, CompanyOffer } from "@/data/mockData";
import { fetchQuotes } from "@/utils/apiQuote";
import { modelToSlug } from "@/utils/modelSlug";
import ComparisonTable from "./ComparisonTable";
import SellOfferDialog from "./SellOfferDialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { useSavedOffers } from "@/hooks/useSavedOffers";
import type { SavedOffer } from "@/types/savedOffers";

interface UnifiedFlowProps {
  onShowResults?: (showing: boolean) => void;
  onModelSelected?: (selected: boolean) => void;
  initialModel?: string;
}

interface RestoreLocationState {
  restoreFromSavedOffer?: SavedOffer;
}

// =====================================================
// Step descriptors
// =====================================================

// 6 separate yes/no functional questions (step 4)
const functionalQuestions: {
  key: keyof ConditionAnswers["functional"];
  title: string;
  shortLabel: string;
  info: string;
  // For most questions, "Ja" means OK (good).
  // For bentOrWaterDamaged, "Ja" means BAD (and "Nej" is normal).
  invertGood?: boolean;
}[] = [
  {
    key: "powersOn",
    title: "Startar din iPhone som den ska?",
    shortLabel: "iPhone startar",
    info: "Tryck på sidoknappen och kontrollera att skärmen tänds och att iOS startar normalt.",
  },
  {
    key: "network",
    title: "Fungerar nätverksanslutningen?",
    shortLabel: "Nätverk fungerar",
    info: "Sätt i ett SIM-kort eller eSIM och kontrollera att telefonen får mottagning och kan ringa.",
  },
  {
    key: "faceId",
    title: "Fungerar Face ID?",
    shortLabel: "Face ID fungerar",
    info: "Gå till Inställningar → Face ID och lösenkod och prova att låsa upp telefonen med ditt ansikte.",
  },
  {
    key: "selfieCamera",
    title: "Fungerar selfiekameran?",
    shortLabel: "Selfiekamera fungerar",
    info: "Öppna Kamera-appen, växla till främre kameran och kontrollera att bilden är skarp utan fläckar.",
  },
  {
    key: "speaker",
    title: "Fungerar högtalaren?",
    shortLabel: "Högtalare fungerar",
    info: "Spela upp ett ljud och lyssna efter sprakningar eller bortfall i båda högtalarna.",
  },
  {
    key: "bentOrWaterDamaged",
    title: "Är telefonen böjd eller vattenskadad?",
    shortLabel: "Inga skador",
    info: "Lägg telefonen platt på ett bord och titta från sidan — den ska ligga helt rakt utan att vagga.",
    invertGood: true,
  },
];

const screenGlassOptions: { value: ScreenGlass; label: string; description: string }[] = [
  { value: "chipped", label: "Flisig", description: "En eller flera flisor" },
  { value: "scratched", label: "Kraftigt repad", description: "Tydliga, djupa repor" },
  { value: "none", label: "Inga sprickor, flisor eller kraftiga repor", description: "Glaset är helt" },
];

const screenWearOptions: { value: WearLevel; label: string; description: string }[] = [
  { value: "visible", label: "Synligt slitage", description: "Lätt synliga repor" },
  { value: "some", label: "Vissa tecken på slitage", description: "Repor som syns vid vissa vinklar" },
  { value: "minimal", label: "Minimalt slitage", description: "Enstaka mikrorepor" },
  { value: "none", label: "Inga tecken på användning", description: "Som ny" },
];

const sidesBackOptions: { value: WearLevelWithCrack; label: string; description: string }[] = [
  { value: "cracked", label: "Sprucken eller trasig", description: "Sprickor eller bitar saknas" },
  { value: "visible", label: "Synligt slitage", description: "Lätt synliga repor eller bucklor" },
  { value: "some", label: "Vissa tecken på slitage", description: "Repor som syns vid vissa vinklar" },
  { value: "minimal", label: "Minimalt slitage", description: "Enstaka mikrorepor" },
  { value: "none", label: "Inga tecken på användning", description: "Som ny" },
];

// =====================================================
// Component
// =====================================================

const Step9ContinueButton = ({ disabled, onDelayComplete }: { disabled: boolean; onDelayComplete: () => void }) => {
  const [pending, setPending] = useState(false);

  const handleClick = () => {
    if (pending) return;
    setPending(true);
    setTimeout(() => {
      onDelayComplete();
    }, 1500);
  };

  return (
    <Button
      size="lg"
      onClick={handleClick}
      disabled={disabled || pending}
      className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white"
    >
      {pending ? (
        <>
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          Beräknar...
        </>
      ) : (
        <>
          Fortsätt <ChevronRight className="w-4 h-4 ml-2" />
        </>
      )}
    </Button>
  );
};

const TOTAL_STEPS = 9; // 1-Modell, 2-Lagring, 3-Batteri, 4-Funktion, 5-Skärmfunktion, 6-Skärmglas, 7-Skärmskick, 8-Sidor, 9-Baksida

const UnifiedFlow = ({ onShowResults, onModelSelected, initialModel }: UnifiedFlowProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [step, setStep] = useState(initialModel ? 2 : 1);
  const [model, setModel] = useState(initialModel ?? "");
  const [storage, setStorage] = useState("");
  const [answers, setAnswers] = useState<ConditionAnswers>(initialConditionAnswers);
  const [funcSubStep, setFuncSubStep] = useState(0); // 0..5 for the 6 yes/no questions
  const [results, setResults] = useState<CompanyOffer[] | null>(null);
  const [loadingResults, setLoadingResults] = useState(false);
  const [batteryMode, setBatteryMode] = useState<"enter" | "cant" | null>(null);
  const { addSavedOffer } = useSavedOffers();
  const [sellDialogOpen, setSellDialogOpen] = useState(false);
  const [selectedOffer, setSelectedOffer] = useState<CompanyOffer | null>(null);
  const [activeSavedOfferId, setActiveSavedOfferId] = useState<string | undefined>(undefined);
  const [resultsTimestamp, setResultsTimestamp] = useState<string>("");
  const [searchOpen, setSearchOpen] = useState(false);
  const blurTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Notify parent when initialModel preselects a model
  useEffect(() => {
    if (initialModel) onModelSelected?.(true);
  }, [initialModel, onModelSelected]);

  // Restore saved offer (existing UX)
  useEffect(() => {
    const state = location.state as RestoreLocationState | null;
    if (state?.restoreFromSavedOffer) {
      const saved = state.restoreFromSavedOffer;
      setModel(saved.model);
      setStorage(saved.storage);
      if (saved.condition) setAnswers(saved.condition);
      if (saved.offers && saved.offers.length > 0) {
        setResults(saved.offers);
        setStep(TOTAL_STEPS + 1);
        onShowResults?.(true);
        onModelSelected?.(true);
        toast.success("Värdering återställd");
      }
    }
  }, [location.state, onShowResults, onModelSelected]);

  useEffect(() => {
    if (results) window.scrollTo({ top: 0, behavior: "smooth" });
  }, [results]);

  const availableStorage = model ? storageByModel[model] || [] : [];

  const goNext = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS + 1));
  const goBack = () => {
    if (step === 4 && funcSubStep > 0) {
      setFuncSubStep((s) => s - 1);
      return;
    }
    if (step === 2 && initialModel) {
      navigate("/");
      return;
    }
    if (step === 1) {
      reset();
      return;
    }
    setStep((s) => Math.max(s - 1, 1));
  };

  const reset = () => {
    if (initialModel) {
      navigate("/");
      return;
    }
    setStep(1);
    setModel("");
    setStorage("");
    setAnswers(initialConditionAnswers);
    setFuncSubStep(0);
    setResults(null);
    onShowResults?.(false);
    onModelSelected?.(false);
  };

  const computeAndShow = async () => {
    setLoadingResults(true);
    try {
      // Tiny artificial delay so it feels like "real" comparison
      await new Promise((r) => setTimeout(r, 600));
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
      setStep(TOTAL_STEPS + 1);
      onShowResults?.(true);
    } catch (err) {
      console.error("fetchQuotes failed:", err);
      toast.error("Kunde inte hämta priser just nu. Försök igen.");
    } finally {
      setLoadingResults(false);
    }
  };

  const setFunctional = (key: keyof ConditionAnswers["functional"], value: boolean) => {
    setAnswers((a) => ({ ...a, functional: { ...a.functional, [key]: value } }));
  };

  const handleFuncAnswer = (value: boolean) => {
    const q = functionalQuestions[funcSubStep];
    setFunctional(q.key, value);
  };

  const cardClass =
    "bg-card rounded-2xl p-6 md:p-10 shadow-xl shadow-foreground/5 border border-border max-w-2xl mx-auto w-full";

  const renderProgress = () => {
    if (step < 2 || step > TOTAL_STEPS) return null;
    const percent = ((step - 1) / (TOTAL_STEPS - 1)) * 100;
    return (
      <div className="mb-8">
        <div className="mb-2 text-xs font-medium text-muted-foreground">
          <span>
            Steg {step} av {TOTAL_STEPS}
          </span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-primary transition-all duration-500 ease-out" style={{ width: `${percent}%` }} />
        </div>
      </div>
    );
  };

  const renderContext = () => {
    if (!model) return null;
    return (
      <div className="mb-8 flex items-center gap-3 px-4 py-3 bg-primary/5 border border-primary/15 rounded-xl">
        <span className="text-[10px] font-bold uppercase tracking-wider text-primary/80">Du värderar</span>
        <span className="h-4 w-px bg-primary/20" />
        <span className="text-sm font-semibold text-foreground">
          {model}
          {storage ? ` • ${storage}` : ""}
        </span>
      </div>
    );
  };

  // ---------------------------------------------------
  // Step 1: model
  // ---------------------------------------------------
  if (step === 1) {
    return (
      <div id="valuation" className="flex flex-col animate-fade-in scroll-mt-20 relative">
        <div
          aria-hidden
          className="pointer-events-none absolute -top-12 -right-12 w-64 h-64 bg-primary/5 rounded-full blur-3xl"
        />
        <div className="relative bg-card rounded-3xl p-8 md:p-10 shadow-xl shadow-foreground/5 border border-border max-w-2xl mx-auto w-full">
          <div className="space-y-2">
            <Command shouldFilter className="relative rounded-xl border border-border bg-muted/40 overflow-visible">
              <CommandInput
                placeholder="Sök eller välj din modell..."
                className="h-14 text-base"
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
                <CommandList className="absolute left-0 right-0 top-full z-50 mt-2 max-h-80 overflow-y-auto rounded-xl border border-border bg-card p-1 shadow-2xl shadow-foreground/10">
                  <CommandEmpty>Ingen modell hittades.</CommandEmpty>
                  <CommandGroup>
                    {iphoneModels.map((m) => (
                      <CommandItem
                        key={m}
                        value={m}
                        onSelect={() => {
                          if (blurTimeoutRef.current) {
                            clearTimeout(blurTimeoutRef.current);
                            blurTimeoutRef.current = null;
                          }
                          setSearchOpen(false);
                          setModel(m);
                          setStorage("");
                          onModelSelected?.(true);
                          navigate(`/salja/${modelToSlug(m)}`);
                        }}
                        className="text-base py-3 cursor-pointer"
                      >
                        {m}
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              )}
            </Command>
          </div>

          <div className="mt-6 pt-6 border-t border-border flex flex-wrap justify-center items-center gap-x-6 gap-y-2">
            {[
              { icon: Check, label: "Gratis" },
              { icon: Zap, label: "Tar 30 sek" },
              { icon: Lock, label: "Säkert & tryggt" },
            ].map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center justify-center gap-1.5 text-[11px] sm:text-xs font-medium text-muted-foreground whitespace-nowrap"
              >
                <Icon className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------
  // Step 2: storage
  // ---------------------------------------------------
  if (step === 2) {
    return (
      <div id="valuation" className="flex flex-col animate-fade-in scroll-mt-20">
        <div className={cardClass}>
          {renderProgress()}
          {renderContext()}

          <div className="mb-6 p-4 bg-muted/50 rounded-xl">
            <h2 className="text-lg md:text-xl font-bold text-foreground mb-1">Hur mycket lagring?</h2>
            <p className="text-sm text-muted-foreground">
              Du hittar det under Inställningar → Allmänt → Om → Kapacitet
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            {availableStorage.map((s) => (
              <button
                key={s}
                onClick={() => {
                  setStorage(s);
                  setStep(3);
                }}
                className={`p-5 rounded-xl border-2 transition-all duration-200 hover:border-primary hover:bg-primary/5 ${
                  storage === s ? "border-primary bg-primary/5" : "border-border bg-card"
                }`}
              >
                <p className="text-lg font-semibold text-foreground">{s}</p>
              </button>
            ))}
          </div>

          <Button variant="outline" size="lg" onClick={goBack} className="w-full">
            <ChevronLeft className="w-4 h-4 mr-2" /> Bakåt
          </Button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------
  // Step 3: battery health
  // ---------------------------------------------------
  if (step === 3) {
    const battery = answers.batteryHealth;
    const mode = batteryMode;
    const inputValid = mode === "enter" && battery !== null && battery >= 0 && battery <= 100;
    const canContinue = mode === "cant" || inputValid;
    return (
      <div id="valuation" className="flex flex-col animate-fade-in scroll-mt-20">
        <div className={cardClass}>
          {renderProgress()}
          {renderContext()}

          <div className="mb-6 p-4 bg-muted/50 rounded-xl">
            <h2 className="text-lg md:text-xl font-bold text-foreground mb-1">Batterihälsa</h2>
            <p className="text-sm text-muted-foreground">
              Hitta under Inställningar → Batteri → Batterihälsa och laddning
            </p>
          </div>

          <div className="space-y-3 mb-8">
            <div
              className={`rounded-xl border-2 transition-all duration-200 ${
                mode === "enter" ? "border-primary bg-primary/5" : "border-border bg-card"
              }`}
            >
              <button
                type="button"
                onClick={() => setBatteryMode("enter")}
                className="w-full text-left p-5 flex items-center gap-3"
              >
                <span
                  className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                    mode === "enter" ? "border-primary" : "border-muted-foreground/40"
                  }`}
                >
                  {mode === "enter" && <span className="w-2.5 h-2.5 rounded-full bg-primary" />}
                </span>
                <p className="text-base font-semibold text-foreground">Ange batterikapacitet</p>
              </button>
              <div className="px-5 pb-5 -mt-2">
                <div className="relative">
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={battery ?? ""}
                    placeholder="Använd siffror (t.ex. 87)"
                    onFocus={() => setBatteryMode("enter")}
                    onWheel={(e) => (e.target as HTMLInputElement).blur()}
                    onChange={(e) => {
                      setBatteryMode("enter");
                      if (e.target.value === "") {
                        setAnswers((a) => ({ ...a, batteryHealth: null }));
                        return;
                      }
                      const v = parseInt(e.target.value, 10);
                      if (Number.isNaN(v)) return;
                      setAnswers((a) => ({ ...a, batteryHealth: Math.max(0, Math.min(100, v)) }));
                    }}
                    className="w-full h-12 pl-3 pr-10 text-base rounded-xl border-2 border-border bg-background text-foreground focus:border-primary focus:outline-none transition-colors"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground font-medium">%</span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                setBatteryMode("cant");
                setAnswers((a) => ({ ...a, batteryHealth: 100 }));
              }}
              className={`w-full text-left p-5 rounded-xl border-2 transition-all duration-200 hover:border-primary/60 ${
                mode === "cant" ? "border-primary bg-primary/5" : "border-border bg-card"
              }`}
            >
              <div className="flex items-center gap-3">
                <span
                  className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${
                    mode === "cant" ? "border-primary" : "border-muted-foreground/40"
                  }`}
                >
                  {mode === "cant" && <span className="w-2.5 h-2.5 rounded-full bg-primary" />}
                </span>
                <div>
                  <p className="text-base font-semibold text-foreground">Kan inte kontrollera</p>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    Vi kommer att bekräfta kapaciteten efter inspektion
                  </p>
                </div>
              </div>
            </button>
          </div>

          <div className="flex gap-3">
            <Button variant="outline" size="lg" onClick={goBack} className="flex-1">
              <ChevronLeft className="w-4 h-4 mr-2" /> Bakåt
            </Button>
            <Button size="lg" onClick={() => setStep(4)} disabled={!canContinue} className="flex-1">
              Fortsätt <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------
  // Step 4: functional checks (6 yes/no, one at a time)
  // ---------------------------------------------------
  if (step === 4) {
    const isAnswered = (key: keyof ConditionAnswers["functional"]) => {
      const v = answers.functional[key];
      return v !== null && v !== undefined;
    };
    const allAnswered = functionalQuestions.every((fq) => isAnswered(fq.key));
    const showingQuestion = funcSubStep < functionalQuestions.length;
    const activeIndex = showingQuestion ? funcSubStep : -1;
    const activeQ = showingQuestion ? functionalQuestions[activeIndex] : null;
    const current = activeQ ? answers.functional[activeQ.key] : null;

    const goToNext = () => {
      const total = functionalQuestions.length;
      for (let offset = 1; offset <= total; offset++) {
        const idx = ((activeIndex >= 0 ? activeIndex : -1) + offset) % total;
        if (!isAnswered(functionalQuestions[idx].key)) {
          setFuncSubStep(idx);
          return;
        }
      }
      setFuncSubStep(functionalQuestions.length);
    };

    const renderCompletedRow = (cq: (typeof functionalQuestions)[number], i: number) => {
      const ans = answers.functional[cq.key];
      const isGood = cq.invertGood ? ans === false : ans === true;
      return (
        <div
          key={cq.key}
          className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-emerald-50 border border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-900"
        >
          <div className="flex items-center gap-3 min-w-0">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
            <span className="text-sm font-medium text-foreground truncate">
              {cq.shortLabel}
              {!isGood && <span className="ml-2 text-xs text-muted-foreground">(svar: {ans ? "Ja" : "Nej"})</span>}
            </span>
          </div>
          <button
            onClick={() => setFuncSubStep(i)}
            className="text-sm font-semibold text-primary hover:underline flex-shrink-0"
          >
            Redigera
          </button>
        </div>
      );
    };

    const renderActiveCard = () => (
      <div className="rounded-2xl border-2 border-border bg-card p-5">
        <p className="text-xs font-bold tracking-wider text-muted-foreground mb-3">
          {activeIndex + 1}/{functionalQuestions.length} · Funktionskoll
        </p>
        <h3 className="text-xl md:text-2xl font-bold text-foreground mb-4">{activeQ!.title}</h3>
        <div className="mb-5 px-4 py-3 rounded-xl bg-muted/60 border border-border text-sm text-muted-foreground">
          {activeQ!.info}
          {activeQ!.invertGood && <p className="mt-2 text-xs italic">Svara &quot;Nej&quot; om allt är som det ska.</p>}
        </div>
        <div className="grid grid-cols-2 gap-3">
          {(activeQ!.invertGood ? [false, true] : [true, false]).map((val) => (
            <button
              key={String(val)}
              onClick={() => handleFuncAnswer(val)}
              className={`py-4 rounded-xl border-2 font-semibold text-base transition-all duration-200 ${
                current === val
                  ? "border-primary bg-primary/10 text-foreground shadow-sm"
                  : "border-border bg-card text-foreground hover:border-primary/60 hover:bg-card"
              }`}
            >
              {val ? "Ja" : "Nej"}
            </button>
          ))}
        </div>
      </div>
    );

    return (
      <div id="valuation" className="flex flex-col animate-fade-in scroll-mt-20">
        <div className={cardClass}>
          {renderProgress()}
          {renderContext()}

          <div className="mb-6 space-y-2">
            {functionalQuestions.map((cq, i) => {
              if (i === activeIndex) return <div key="active">{renderActiveCard()}</div>;
              if (isAnswered(cq.key)) return renderCompletedRow(cq, i);
              return null;
            })}
          </div>

          {!showingQuestion && allAnswered && (
            <div className="mb-6 flex items-center gap-3 px-5 py-4 rounded-xl bg-emerald-100 border border-emerald-300 dark:bg-emerald-950/50 dark:border-emerald-800">
              <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
              <p className="text-sm font-semibold text-emerald-900 dark:text-emerald-100">
                Alla funktionskollar klara!
              </p>
            </div>
          )}

          <div className="flex gap-3">
            <Button variant="outline" size="lg" onClick={goBack} className="flex-1">
              <ChevronLeft className="w-4 h-4 mr-2" /> Bakåt
            </Button>
            <Button
              size="lg"
              onClick={() => {
                if (!showingQuestion && allAnswered) {
                  setStep(5);
                } else if (current !== null && current !== undefined) {
                  goToNext();
                }
              }}
              disabled={showingQuestion && (current === null || current === undefined)}
              className="flex-1"
            >
              Fortsätt <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------
  // Step 5: screen function (multi-select)
  // ---------------------------------------------------
  if (step === 5) {
    const sf = answers.screenFunction;
    const answered = answers.screenFunctionAnswered;

    const toggle = (key: keyof typeof sf) => {
      setAnswers((a) => {
        const next = { ...a.screenFunction };
        if (key === "allWorks") {
          const newVal = !next.allWorks;
          return {
            ...a,
            screenFunctionAnswered: true,
            screenFunction: {
              brightSpots: newVal ? false : next.brightSpots,
              deadPixels: newVal ? false : next.deadPixels,
              linesOrBurnIn: newVal ? false : next.linesOrBurnIn,
              allWorks: newVal,
            },
          };
        }
        next[key] = !next[key];
        if (next[key]) next.allWorks = false;
        return { ...a, screenFunctionAnswered: true, screenFunction: next };
      });
    };

    const items: { key: keyof typeof sf; label: string }[] = [
      { key: "brightSpots", label: "Ljusa fläckar" },
      { key: "deadPixels", label: "Trasiga pixlar" },
      { key: "linesOrBurnIn", label: "Linjer eller inbränd bild" },
      { key: "allWorks", label: "Allt fungerar" },
    ];

    const anySelected = sf.brightSpots || sf.deadPixels || sf.linesOrBurnIn || sf.allWorks;

    return (
      <div id="valuation" className="flex flex-col animate-fade-in scroll-mt-20">
        <div className={cardClass}>
          {renderProgress()}
          {renderContext()}

          <div className="mb-6 p-4 bg-muted/50 rounded-xl">
            <h2 className="text-lg md:text-xl font-bold text-foreground mb-1">Hur fungerar skärmen?</h2>
            <p className="text-sm text-muted-foreground">Välj alla som stämmer.</p>
          </div>

          <div className="space-y-2.5 mb-6">
            {items.map((it) => {
              const selected = sf[it.key];
              return (
                <button
                  key={it.key}
                  onClick={() => toggle(it.key)}
                  className={`w-full p-4 rounded-xl border-2 transition-all duration-200 text-left flex items-center gap-3 hover:border-primary hover:bg-primary/5 ${
                    selected ? "border-primary bg-primary/5" : "border-border bg-card"
                  }`}
                >
                  <Checkbox checked={selected} className="pointer-events-none" />
                  <span className="font-semibold text-foreground text-base">{it.label}</span>
                </button>
              );
            })}
          </div>

          <div className="flex gap-3">
            <Button variant="outline" size="lg" onClick={goBack} className="flex-1">
              <ChevronLeft className="w-4 h-4 mr-2" /> Bakåt
            </Button>
            <Button size="lg" onClick={() => setStep(6)} disabled={!answered || !anySelected} className="flex-1">
              Fortsätt <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------
  // Generic single-select renderer for steps 6-9
  // ---------------------------------------------------
  const renderSingleChoiceStep = <T extends string>(opts: {
    title: string;
    subtitle?: string;
    options: { value: T; label: string; description: string }[];
    value: T | null;
    onChange: (v: T) => void;
    onContinue: () => void;
  }) => {
    const hasValue = opts.value !== null;
    return (
      <div id="valuation" className="flex flex-col animate-fade-in scroll-mt-20">
        <div className={cardClass}>
          {renderProgress()}
          {renderContext()}

          <div className="mb-6 p-4 bg-muted/50 rounded-xl">
            <h2 className="text-lg md:text-xl font-bold text-foreground mb-1">{opts.title}</h2>
            {opts.subtitle && <p className="text-sm text-muted-foreground">{opts.subtitle}</p>}
          </div>

          <div className="space-y-2.5 mb-6">
            {opts.options.map((o) => {
              const selected = opts.value === o.value;
              return (
                <button
                  key={o.value}
                  onClick={() => {
                    opts.onChange(o.value);
                  }}
                  className={`w-full p-4 rounded-xl border-2 transition-all duration-200 text-left hover:border-primary hover:bg-primary/5 ${
                    selected ? "border-primary bg-primary/5" : "border-border bg-card"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <p className="font-semibold text-foreground text-base mb-0.5">{o.label}</p>
                      <p className="text-sm text-muted-foreground">{o.description}</p>
                    </div>
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-1 ${
                        selected ? "border-primary bg-primary" : "border-muted-foreground/30"
                      }`}
                    >
                      {selected && <div className="w-2 h-2 rounded-full bg-white" />}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="flex gap-3">
            <Button variant="outline" size="lg" onClick={goBack} className="flex-1">
              <ChevronLeft className="w-4 h-4 mr-2" /> Bakåt
            </Button>
            <Button size="lg" onClick={opts.onContinue} disabled={!hasValue} className="flex-1">
              Fortsätt <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </div>
      </div>
    );
  };

  // ---------------------------------------------------
  // Step 6: screen glass
  // ---------------------------------------------------
  if (step === 6) {
    return renderSingleChoiceStep({
      title: "Hur ser skärmglaset ut?",
      options: screenGlassOptions,
      value: answers.screenGlass,
      onChange: (v) => setAnswers((a) => ({ ...a, screenGlass: v })),
      onContinue: () => setStep(7),
    });
  }

  // ---------------------------------------------------
  // Step 7: screen wear
  // ---------------------------------------------------
  if (step === 7) {
    return renderSingleChoiceStep({
      title: "Hur ser skärmens skick ut?",
      subtitle: "Bortsett från sprickor och flisor — hur sliten är skärmen?",
      options: screenWearOptions,
      value: answers.screenWear,
      onChange: (v) => setAnswers((a) => ({ ...a, screenWear: v })),
      onContinue: () => setStep(8),
    });
  }

  // ---------------------------------------------------
  // Step 8: sides
  // ---------------------------------------------------
  if (step === 8) {
    return renderSingleChoiceStep({
      title: "Hur ser sidorna ut?",
      options: sidesBackOptions,
      value: answers.sidesWear,
      onChange: (v) => setAnswers((a) => ({ ...a, sidesWear: v })),
      onContinue: () => setStep(9),
    });
  }

  // ---------------------------------------------------
  // Step 9: back
  // ---------------------------------------------------
  if (step === 9) {
    const hasValue = answers.backWear !== null;
    return (
      <div id="valuation" className="flex flex-col animate-fade-in scroll-mt-20">
        <div className={cardClass}>
          {renderProgress()}
          {renderContext()}

          <div className="mb-6 p-4 bg-muted/50 rounded-xl">
            <h2 className="text-lg md:text-xl font-bold text-foreground mb-1">Hur ser baksidan ut?</h2>
          </div>

          <div className="space-y-2.5 mb-6">
            {sidesBackOptions.map((o) => {
              const selected = answers.backWear === o.value;
              return (
                <button
                  key={o.value}
                  onClick={() => setAnswers((a) => ({ ...a, backWear: o.value }))}
                  className={`w-full p-4 rounded-xl border-2 transition-all duration-200 text-left hover:border-primary hover:bg-primary/5 ${
                    selected ? "border-primary bg-primary/5" : "border-border bg-card"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <p className="font-semibold text-foreground text-base mb-0.5">{o.label}</p>
                      <p className="text-sm text-muted-foreground">{o.description}</p>
                    </div>
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-1 ${
                        selected ? "border-primary bg-primary" : "border-muted-foreground/30"
                      }`}
                    >
                      {selected && <div className="w-2 h-2 rounded-full bg-white" />}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="flex gap-3">
            <Button variant="outline" size="lg" onClick={goBack} className="flex-1">
              <ChevronLeft className="w-4 h-4 mr-2" /> Bakåt
            </Button>
            <Step9ContinueButton disabled={!hasValue} onDelayComplete={() => computeAndShow()} />
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------
  // Final step: results
  // ---------------------------------------------------
  if (loadingResults || !results) {
    return (
      <div id="valuation" className="flex flex-col animate-fade-in scroll-mt-20">
        <div className={cardClass}>
          <div className="text-center py-12">
            <Loader2 className="w-10 h-10 text-primary mx-auto mb-4 animate-spin" />
            <p className="text-muted-foreground">Jämför priser från återförsäljare...</p>
          </div>
        </div>
      </div>
    );
  }

  // Sort: purchasable first (high→low), refusals last
  const purchasable = results.filter((o) => !o.notPurchased && o.pris > 0);
  const refused = results.filter((o) => o.notPurchased || o.pris <= 0);

  const bestOffer = purchasable.length > 0 ? [...purchasable].sort((a, b) => b.pris - a.pris)[0] : null;
  const lowestPrice = purchasable.length > 0 ? [...purchasable].sort((a, b) => a.pris - b.pris)[0].pris : 0;
  const bestDiff = bestOffer ? bestOffer.pris - lowestPrice : 0;

  const handleSelectOffer = (offer: CompanyOffer) => {
    const savedOffer = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      model,
      storage,
      condition: answers,
      offers: results,
      selectedOffer: offer,
      timestamp: Date.now(),
    };
    addSavedOffer(savedOffer);
    setActiveSavedOfferId(savedOffer.id);
    setSelectedOffer(offer);
    setSellDialogOpen(true);
  };

  return (
    <div
      id="valuation"
      className="animate-fade-in scroll-mt-20 bg-muted/40 -mx-4 md:-mx-6 px-4 md:px-6 pt-0 pb-0 rounded-2xl"
    >
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6 text-center">
          <h2 className="text-2xl md:text-4xl font-bold text-foreground mb-2 tracking-tight">
            Värdering för{" "}
            <span className="text-primary">
              {model} {storage}
            </span>
          </h2>
          <p className="text-sm md:text-base text-muted-foreground">
            {purchasable.length} återförsäljare har värderat din telefon
          </p>
          {resultsTimestamp && (
            <p className="text-xs text-muted-foreground/70 mt-1">Priser hämtade: {resultsTimestamp}</p>
          )}
        </div>

        {/* Best offer hero */}
        {bestOffer && (
          <div className="bg-primary/5 border-2 border-primary/40 rounded-2xl p-6 md:p-8 mb-8 text-center">
            <p className="text-sm md:text-base font-semibold text-primary mb-2">💰 Bästa erbjudandet</p>
            <div className="text-4xl md:text-5xl font-bold text-primary mb-2">
              {bestOffer.pris.toLocaleString("sv-SE")} SEK
            </div>
            {bestDiff > 0 && (
              <p className="text-sm text-muted-foreground">
                Skillnad mot lägsta pris:{" "}
                <span className="font-semibold text-primary underline underline-offset-2">
                  {bestDiff.toLocaleString("sv-SE")} kr
                </span>
              </p>
            )}
          </div>
        )}

        {/* Offers list */}
        <ComparisonTable offers={purchasable} onSelectOffer={handleSelectOffer} />

        {refused.length > 0 && (
          <div className="mt-8">
            <div className="bg-card border border-border rounded-xl p-4 text-sm text-muted-foreground">
              <p className="font-semibold text-foreground mb-1">Köper ej din telefon</p>
              <ul className="list-disc list-inside space-y-1">
                {refused.map((o, i) => (
                  <li key={i}>{o.företag}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="text-center mt-8">
          <Button variant="outline" onClick={reset}>
            Gör en ny värdering
          </Button>
        </div>
      </div>

      <SellOfferDialog
        open={sellDialogOpen}
        onOpenChange={setSellDialogOpen}
        offer={selectedOffer}
        model={model}
        storage={storage}
        conditionAnswers={answers}
        savedOfferId={activeSavedOfferId}
      />
    </div>
  );
};

export default UnifiedFlow;
