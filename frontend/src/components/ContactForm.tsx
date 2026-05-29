import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Check, Clock, Loader2 } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "sonner";

/* -----------------------------
   Typewriter placeholder hook
------------------------------ */

const questions = [
  "Funkar det att sälja en iPhone som har sprucken skärm?",
  "När får jag pengarna efter att jag skickat in mobilen?",
  "Behöver jag originalkartongen för att sälja?",
  "Köper ni även gamla iPhones, typ iPhone 8?",
  "Vad räknas som dålig batterihälsa egentligen?",
  "Får jag något kvitto eller intyg när jag säljer?",
  "Hur lång tid tar det innan jag får svar på min värdering?",
  "Vad händer om jag råkat glömma logga ut från iCloud?",
  "Hur bestäms priset på min iPhone egentligen?",
  "Kan jag avbryta försäljningen om jag ångrar mig?",
];

function useTypewriterPlaceholder() {
  const [text, setText] = useState("");
  const [direction, setDirection] = useState<"forward" | "backward">("forward");
  const [question, setQuestion] = useState(questions[Math.floor(Math.random() * questions.length)]);
  const [cursorVisible, setCursorVisible] = useState(true);

  useEffect(() => {
    const cursor = setInterval(() => setCursorVisible((v) => !v), 500);
    return () => clearInterval(cursor);
  }, []);

  useEffect(() => {
    const interval = setInterval(
      () => {
        setText((prev) => {
          if (direction === "forward") {
            if (prev.length < question.length) {
              return question.slice(0, prev.length + 1);
            } else {
              setTimeout(() => setDirection("backward"), 2000);
              return prev;
            }
          } else {
            if (prev.length > 0) {
              return prev.slice(0, -1);
            } else {
              setQuestion(questions[Math.floor(Math.random() * questions.length)]);
              setTimeout(() => setDirection("forward"), 500);
              return prev;
            }
          }
        });
      },
      direction === "forward" ? 50 : 25,
    );

    return () => clearInterval(interval);
  }, [direction, question]);

  return (
    <span className="text-muted-foreground">
      {text}
      <span>{cursorVisible ? "|" : " "}</span>
    </span>
  );
}

/* -----------------------------
   Step indicator
------------------------------ */

const StepIndicator = ({ step }: { step: number }) => {
  const steps = [
    { number: 1, label: "Fråga" },
    { number: 2, label: "E-post" },
    { number: 3, label: "Klar" },
  ];

  return (
    <div className="mb-8">
      <div className="flex items-center justify-center">
        {steps.map((s, idx) => (
          <div key={s.number} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all
                ${s.number <= step ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
              >
                {s.number < step ? <Check className="w-5 h-5" /> : s.number}
              </div>
              <span
                className={`text-xs mt-2 font-medium ${s.number <= step ? "text-primary" : "text-muted-foreground"}`}
              >
                {s.label}
              </span>
            </div>

            {idx < steps.length - 1 && (
              <div className={`w-16 h-0.5 mb-6 mx-2 transition-all ${s.number < step ? "bg-primary" : "bg-muted"}`} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

/* -----------------------------
   Contact form
------------------------------ */

const ContactForm = () => {
  const [step, setStep] = useState(1);
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [cooldown, setCooldown] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const placeholder = useTypewriterPlaceholder();

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    if (emailError && validateEmail(value)) {
      setEmailError("");
    }
  };

  const handleNextFromEmail = () => {
    if (!validateEmail(email)) {
      setEmailError("Ange en giltig e-postadress");
      return;
    }
    setEmailError("");
    setStep(3);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateEmail(email)) {
      setEmailError("Ange en giltig e-postadress");
      setStep(2);
      return;
    }

    setIsLoading(true);

    try {
      if (!supabase) {
        toast.error("Kontaktformuläret är inte aktiverat ännu.");
        return;
      }

      const { error } = await supabase.functions.invoke("send-contact-email", { body: { message, email } });

      if (error) throw error;

      setSubmitted(true);
      setCooldown(15);
    } catch {
      toast.error("Något gick fel. Försök igen senare.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSubmitted(false);
    setMessage("");
    setEmail("");
    setStep(1);
    setCooldown(null);
  };

  useEffect(() => {
    if (!cooldown) return;
    const t = setInterval(() => setCooldown((c) => (c ? c - 1 : c)), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  const scrollToHero = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (submitted) {
    return (
      <div className="bg-[#F5FFF7] rounded-2xl p-8 md:p-12 shadow-card text-center">
        <div className="w-20 h-20 mx-auto mb-6 bg-primary rounded-full flex items-center justify-center">
          <Check className="w-10 h-10 text-primary-foreground" />
        </div>
        <h3 className="text-2xl md:text-3xl font-bold mb-2">Tack!</h3>
        <p className="text-lg mb-8">Ditt meddelande har skickats.</p>
        <div className="space-y-3">
          <Button size="lg" className="w-full" disabled={cooldown !== 0} onClick={handleReset}>
            {cooldown && cooldown > 0 ? `Ställ en ny fråga (${cooldown})` : "Ställ en ny fråga"}
          </Button>
          <Button
            size="lg"
            variant="outline"
            className="w-full border-2 border-black hover:bg-black/5"
            onClick={scrollToHero}
          >
            Gör en gratis värdering
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div id="contact-form" className="bg-[#F5FFF7] rounded-2xl p-8 md:p-12 shadow-card scroll-mt-20">
      {step > 1 && <StepIndicator step={step} />}

      {/* STEP 1 */}
      {step === 1 && (
        <div className="animate-fade-in space-y-6">
          <div className="text-center mb-6">
            <h2 className="text-3xl md:text-4xl font-bold mb-3">Vad har du på hjärtat?</h2>
            <div className="flex items-center justify-center gap-2 text-muted-foreground mt-3">
              <p className="inline-flex items-center gap-2 text-sm font-medium text-white bg-[#00B87A] rounded-full px-4 py-1.5 mx-auto">
                ⏱️ Vi svarar oftast inom 24 timmar
              </p>
            </div>
          </div>

          <div className="relative">
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="min-h-[150px] resize-none rounded-xl border-2"
            />
            {!message && <div className="absolute top-2 left-3 pointer-events-none">{placeholder}</div>}
          </div>

          <Button size="lg" className="w-full" disabled={!message} onClick={() => setStep(2)}>
            Nästa →
          </Button>
        </div>
      )}

      {/* STEP 2 */}
      {step === 2 && (
        <div className="animate-fade-in space-y-6">
          <div className="text-center mb-6">
            <h2 className="text-3xl md:text-4xl font-bold">Ange mejladress</h2>
          </div>

          <div>
            <Input
              type="email"
              value={email}
              onChange={handleEmailChange}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleNextFromEmail();
                }
              }}
              className={`h-12 rounded-xl border-2 ${emailError ? "border-red-500" : ""}`}
              placeholder="jagälskar@cashmyphone.se"
            />
            {emailError && <p className="text-red-500 text-sm mt-2">{emailError}</p>}
          </div>

          <div className="flex gap-3 pt-2.5">
            <Button variant="outline" size="lg" className="flex-1 border-2 border-black/30" onClick={() => setStep(1)}>
              Tillbaka
            </Button>
            <Button size="lg" className="flex-1" disabled={!email} onClick={handleNextFromEmail}>
              Nästa →
            </Button>
          </div>
        </div>
      )}

      {/* STEP 3 – ONLY FORM */}
      {step === 3 && (
        <form onSubmit={handleSubmit} className="animate-fade-in space-y-6">
          <div className="text-center mb-6">
            <h2 className="text-3xl md:text-4xl font-bold mb-3">Ser allt bra ut?</h2>
          </div>

          <div className="bg-muted/50 rounded-xl p-6 space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Ditt meddelande:</p>
              <p>{message}</p>
            </div>
            <div className="border-t pt-4">
              <p className="text-sm text-muted-foreground mb-2">Din e-post:</p>
              <p>{email}</p>
            </div>
          </div>

          <div className="flex gap-3 pt-2.5">
            <Button
              variant="outline"
              size="lg"
              className="flex-1 border-2 border-black/30"
              type="button"
              onClick={() => setStep(2)}
            >
              Tillbaka
            </Button>

            <Button type="submit" size="lg" className="flex-1" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Skickar...
                </>
              ) : (
                "Bekräfta"
              )}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
};

export default ContactForm;
