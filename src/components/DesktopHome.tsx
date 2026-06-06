import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BadgePercent, Clock, Search, Shield, Scale, Truck, Wallet } from "lucide-react";

import { useIphoneCatalog } from "@/hooks/useIphoneCatalog";
import { modelToSlug } from "@/utils/modelSlug";

import logoGreen from "@/assets/logo-green.png";
import cmpLogo from "@/assets/logo.png";
import swappieLogo from "@/assets/swappie-logo.png";
import fixmyphoneLogo from "@/assets/fixmyphone-logo.png";
import fixiphoneLogo from "@/assets/fixiphone-logo.png";
import fixphoneproLogo from "@/assets/fixphonepro-logo.png";
import happyphoneLogo from "@/assets/happyphone-logo.png";
import renewedLogo from "@/assets/renewed-logo.png";
import phoneheroLogo from "@/assets/phonehero-logo.svg";
import telestoreLogo from "@/assets/telestore-logo.png";
import "./DesktopHome.css";

const steps = [
  {
    title: "Sök & jämför bud",
    text: "Skriv in din modell och se bud från flera återförsäljare direkt — på sekunder.",
    icon: Search,
  },
  {
    title: "Välj & skicka",
    text: "Välj det bästa budet och skicka telefonen gratis med en förbetald fraktsedel.",
    icon: Truck,
  },
  {
    title: "Få betalt",
    text: "Återförsäljaren kontrollerar mobilen och betalar ut — i snitt inom 4–5 dagar.",
    icon: Wallet,
  },
];

const values = [
  {
    title: "Alla bud på ett ställe",
    text: "Vi frågar flera återförsäljare åt dig, så du slipper mejla runt och jämföra själv.",
    icon: Scale,
  },
  {
    title: "Det kostar dig inget",
    text: "Vi köper inte din telefon — vi hittar köparen som betalar bäst. Du betalar aldrig en krona för det.",
    icon: BadgePercent,
  },
  {
    title: "Tryggt hela vägen",
    text: "Spårbar frakt, köpare vi känner till och utbetalning via Swish eller bank. Ångrar du dig skickar vi tillbaka mobilen gratis.",
    icon: Shield,
  },
];

const faqs = [
  {
    q: "Köper ni telefonen själva?",
    a: "Nej, det gör vi inte. Vi visar vilka återförsäljare som vill ha din mobil och vad de betalar — sen säljer du direkt till den du gillar bäst.",
  },
  {
    q: "Hur snabbt får jag pengarna?",
    a: "När köparen fått och kollat din telefon betalar de ut. Det brukar ta runt 4–5 dagar från att du skickat paketet.",
  },
  {
    q: "Vad kostar det?",
    a: "Inget för dig. Att jämföra bud är gratis, frakten är förbetald och du bestämmer själv om du vill sälja.",
  },
  {
    q: "Hur skickar jag telefonen?",
    a: "Du får en färdig fraktsedel på mejl. Skriv ut, tejpa fast den på paketet och lämna in det hos närmaste ombud.",
  },
  {
    q: "Tänk om budet ändras när de kollat mobilen?",
    a: "Om skicket inte stämmer med det du angett får du ett nytt bud. Säger du nej skickar vi tillbaka telefonen utan att det kostar dig något.",
  },
  {
    q: "Hur betalas pengarna ut?",
    a: "Via Swish eller vanlig banköverföring — du väljer det som passar dig.",
  },
];

const partners = [
  { src: swappieLogo, alt: "Swappie" },
  { src: fixmyphoneLogo, alt: "FixMyPhone" },
  { src: fixiphoneLogo, alt: "Fixiphone" },
  { src: fixphoneproLogo, alt: "FixPhonePro" },
  { src: happyphoneLogo, alt: "HappyPhone" },
  { src: renewedLogo, alt: "reNewed" },
  { src: phoneheroLogo, alt: "PhoneHero" },
  { src: telestoreLogo, alt: "Telestore" },
];

const Highlight = ({ children }: { children: React.ReactNode }) => (
  <span className="cmp-home-highlight">
    {children}
    <svg viewBox="0 0 200 12" preserveAspectRatio="none" aria-hidden>
      <path d="M3 8 C 45 3, 90 3, 130 6 S 185 9, 197 5" />
    </svg>
  </span>
);

const DesktopHome = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [open, setOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [atTop, setAtTop] = useState(true);
  const [hidden, setHidden] = useState(false);
  const [loading, setLoading] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { models: iphoneModels } = useIphoneCatalog();

  const filteredModels = useMemo(() => {
    if (!query.trim() || selectedModel) return [];
    const needle = query.toLowerCase();
    return iphoneModels.filter((model) => model.toLowerCase().includes(needle)).slice(0, 7);
  }, [iphoneModels, query, selectedModel]);

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  useEffect(() => {
    let lastY = window.scrollY;
    const onScroll = () => {
      const y = window.scrollY;
      setAtTop(y < 24);
      if (y > lastY && y > 150) setHidden(true);
      if (y < lastY - 4) setHidden(false);
      lastY = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const startFlow = (model = selectedModel) => {
    if (!model) {
      inputRef.current?.focus();
      setOpen(true);
      return;
    }
    setLoading(true);
    window.setTimeout(() => navigate(`/salja/${modelToSlug(model)}`), 450);
  };

  const pickModel = (model: string) => {
    setSelectedModel(model);
    setQuery(model);
    setOpen(false);
  };

  return (
    <div className="cmp-home">
      <header className={`cmp-home-header ${atTop ? "attop" : ""} ${hidden ? "hidden" : ""}`}>
        <div className="cmp-home-wrap cmp-home-nav">
          <a className="cmp-home-brand" href="#top" aria-label="CashMyPhone startsida">
            <span><img src={logoGreen} alt="" /></span>
          </a>
          <nav>
            <a href="#how">Så funkar det</a>
            <a href="#why">Varför oss</a>
            <a href="#faq">Vanliga frågor</a>
          </nav>
          <button type="button" onClick={() => startFlow()} className="cmp-home-nav-cta">
            Sälj nu
          </button>
        </div>
      </header>

      <section className="cmp-home-hero" id="top">
        <div className="cmp-home-wrap">
          <div className="cmp-home-hero-inner">
            <h1>
              Hitta <Highlight>bästa priset</Highlight> för din mobil
            </h1>
            <p className="cmp-home-accent">helt gratis!</p>

            <div className="cmp-home-searchbox" ref={searchRef}>
              <div className="cmp-home-search">
                <Search aria-hidden />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setSelectedModel("");
                    setOpen(true);
                  }}
                  onFocus={() => setOpen(filteredModels.length > 0)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && selectedModel) startFlow(selectedModel);
                  }}
                  placeholder="Sök modell, t.ex. iPhone 14 Pro..."
                />
                <button
                  type="button"
                  onClick={() => startFlow()}
                  disabled={!selectedModel || loading}
                  data-disabled={!selectedModel}
                  data-loading={loading}
                >
                  <span>Jämför bud</span>
                </button>
              </div>
              {open && filteredModels.length > 0 ? (
                <div className="cmp-home-search-drop">
                  {filteredModels.map((model) => (
                    <button key={model} type="button" onMouseDown={() => pickModel(model)}>
                      {model}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="cmp-home-trust">
              <div>
                <span><Clock aria-hidden />Tar 30 sek</span>
                <i />
                <span><img src={cmpLogo} alt="" />Swish / banköverföring</span>
                <i />
                <span><Truck aria-hidden />Fri frakt</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="cmp-home-marquee" aria-label="Återförsäljare">
        <p>Vi jämför bud från Sveriges återförsäljare</p>
        <div>
          <div>
            {[...partners, ...partners].map((partner, index) => (
              <span key={`${partner.alt}-${index}`}>
                <img src={partner.src} alt={partner.alt} />
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="cmp-home-block cmp-home-how" id="how">
        <div className="cmp-home-wrap">
          <div className="cmp-home-steps">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <article key={step.title}>
                  <Icon className="cmp-home-step-icon" aria-hidden />
                  <span>{index + 1}</span>
                  <h2>{step.title}</h2>
                  <p>{step.text}</p>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="cmp-home-block cmp-home-values" id="why">
        <div className="cmp-home-wrap">
          <div className="cmp-home-section-head">
            <p>Varför oss</p>
            <h2>Mindre krångel, mer betalt</h2>
          </div>
          <div className="cmp-home-value-grid">
            {values.map((value) => {
              const Icon = value.icon;
              return (
                <article key={value.title}>
                  <span><Icon aria-hidden /></span>
                  <div>
                    <h3>{value.title}</h3>
                    <p>{value.text}</p>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="cmp-home-block cmp-home-faq-section" id="faq">
        <div className="cmp-home-wrap">
          <div className="cmp-home-section-head">
            <p>Vanliga frågor</p>
            <h2>Bra att veta innan du säljer</h2>
          </div>
          <div className="cmp-home-faq">
            {faqs.map((faq, index) => {
              const isOpen = openFaq === index;
              return (
                <article key={faq.q} className={isOpen ? "open" : ""}>
                  <button type="button" onClick={() => setOpenFaq(isOpen ? null : index)} aria-expanded={isOpen}>
                    <span>{faq.q}</span>
                    <i>+</i>
                  </button>
                  <div>
                    <p>{faq.a}</p>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="cmp-home-cta">
        <div className="cmp-home-wrap">
          <h2>Redo att sälja din mobil?</h2>
          <p>Se bud från flera återförsäljare på ett par minuter.</p>
          <div>
            <button type="button" onClick={() => startFlow()}>
              <Search aria-hidden />
              Jämför bud nu
            </button>
            <span>
              helt gratis!
              <svg viewBox="0 0 48 34" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
                <path d="M44 5 C 30 2, 8 8, 4 26" />
                <path d="M4 26 L11 21 M4 26 L10 31" />
              </svg>
            </span>
          </div>
        </div>
      </section>

      <footer className="cmp-home-footer">
        <div className="cmp-home-wrap">
          <div className="cmp-home-footer-grid">
            <div>
              <a className="cmp-home-footer-brand" href="#top">
                <img src={logoGreen} alt="" />
                CashMyPhone
              </a>
              <p>Vi hjälper dig sälja din telefon till återförsäljaren som betalar bäst. Gratis, och utan krångel.</p>
            </div>
            <nav>
              <h3>Tjänsten</h3>
              <a href="#how">Så funkar det</a>
              <a href="#why">Varför oss</a>
              <a href="#faq">Vanliga frågor</a>
            </nav>
            <nav>
              <h3>Företaget</h3>
              <a href="/om-oss">Om oss</a>
              <a href="/artiklar">Artiklar</a>
              <a href="mailto:info@cashmyphone.se">Kontakt</a>
            </nav>
            <nav>
              <h3>Juridik</h3>
              <a href="#villkor">Villkor</a>
              <a href="#integritet">Integritet</a>
              <a href="#cookies">Cookies</a>
            </nav>
          </div>
          <div className="cmp-home-footer-bottom">
            <span>© 2026 CashMyPhone. Alla rättigheter förbehållna.</span>
            <span>Utbetalning via Swish &amp; banköverföring</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default DesktopHome;
