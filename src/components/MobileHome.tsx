import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BadgePercent,
  Check,
  ChevronDown,
  Menu,
  Search,
  Shield,
  Scale,
  Truck,
  Wallet,
  X,
} from "lucide-react";

import { useIphoneCatalog } from "@/hooks/useIphoneCatalog";
import { getIphoneImage } from "@/utils/iphoneImage";
import { modelToSlug } from "@/utils/modelSlug";
import { trackEvent } from "@/utils/tracking";

import logoGreen from "@/assets/televera-logo-full.png";
import swappieLogo from "@/assets/swappie-logo.png";
import fixmyphoneLogo from "@/assets/fixmyphone-logo.png";
import fixiphoneLogo from "@/assets/fixiphone-logo.png";
import fixphoneproLogo from "@/assets/fixphonepro-logo.png";
import happyphoneLogo from "@/assets/happyphone-logo.png";
import renewedLogo from "@/assets/renewed-logo.png";
import phoneheroLogo from "@/assets/phonehero-logo.svg";
import telestoreLogo from "@/assets/telestore-logo.png";
import "./MobileHome.css";

const partners = [
  { src: swappieLogo, alt: "Swappie" },
  { src: fixmyphoneLogo, alt: "FixMyPhone" },
  { src: fixiphoneLogo, alt: "Fixiphone" },
  { src: fixphoneproLogo, alt: "FixTech", compact: true },
  { src: happyphoneLogo, alt: "HappyPhone" },
  { src: renewedLogo, alt: "reNewed" },
  { src: phoneheroLogo, alt: "PhoneHero", className: "phonehero" },
  { src: telestoreLogo, alt: "Telestore" },
];

const marqueeGroups = Array.from({ length: 5 }, (_, index) => index);

const trustChips = ["Tar 30 sekunder", "Bud direkt", "8+ återförsäljare"];

const steps = [
  {
    title: "Sök & jämför bud",
    text: "Skriv in modell, skick och lagring och se bud från flera återförsäljare direkt.",
    icon: Search,
  },
  {
    title: "Välj & skicka",
    text: "Välj det bästa budet och följ köparens instruktioner för inlämning eller frakt.",
    icon: Truck,
  },
  {
    title: "Få betalt",
    text: "Återförsäljaren kontrollerar mobilen och betalar ut - i snitt inom 4-5 dagar.",
    icon: Wallet,
  },
];

const values = [
  {
    title: "Alla bud på ett ställe",
    text: "Vi samlar bud från flera återförsäljare åt dig, så du slipper leta runt själv.",
    icon: Scale,
  },
  {
    title: "Det kostar dig inget",
    text: "Vi köper inte din telefon. Vi hittar köparen som betalar bäst för din mobil helt gratis.",
    icon: BadgePercent,
  },
  {
    title: "Tryggt hela vägen",
    text: "Vi har granskat alla köpare så att du kan känna dig trygg genom processen.",
    icon: Shield,
  },
];

const faqs = [
  {
    q: "Köper ni telefonen själva?",
    a: "Nej, det gör vi inte. Vi visar vilka återförsäljare som vill ha din mobil och vad de betalar. Du säljer sedan direkt till den du gillar bäst.",
  },
  {
    q: "Hur snabbt får jag pengarna?",
    a: "När köparen fått, granskat och godkänt skicket på din telefon betalar de ut enligt det betalningssätt du har valt. Utbetalningstiden beror på återförsäljaren, men generellt brukar det ta runt 4-5 dagar från att du skickat paketet.",
  },
  {
    q: "Vad kostar det?",
    a: "Det kostar inget att jämföra bud hos Televera. Eventuella frakt- och hanteringsvillkor kan tillkomma av köparen du väljer.",
  },
  {
    q: "Hur skickar jag telefonen?",
    a: "Det beror på köparen du väljer. Vissa erbjuder fraktsedel, andra kan ha inlämning i butik eller egna instruktioner. Instruktioner för hur du skickar in din telefon skickas alltid med i samband med orderbekräftelsen via mail.",
  },
  {
    q: "Tänk om budet ändras när de kollat mobilen?",
    a: "Om skicket inte stämmer med det du angett får du ett nytt bud. Säger du nej har du rätt till att köparen skickar tillbaka telefonen enligt köparens villkor.",
  },
  {
    q: "Hur betalas pengarna ut?",
    a: "När du har värderat din telefon och valt en köpare att gå vidare med listas betalningssätten som de erbjuder. Oftast erbjuds vara Swish eller banköverföring, men andra betalningsmetoder som PayPal kan även finnas tillgängliga.",
  },
];

const Highlight = ({ children }: { children: React.ReactNode }) => (
  <span className="cmp-mobile-highlight">
    {children}
    <svg viewBox="0 0 200 12" preserveAspectRatio="none" aria-hidden>
      <path d="M3 8 C 45 3, 90 3, 130 6 S 185 9, 197 5" />
    </svg>
  </span>
);

const MobileHome = () => {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const searchStartedTrackedRef = useRef(false);
  const [query, setQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [navState, setNavState] = useState<"top" | "hidden" | "solid">("top");
  const [loading, setLoading] = useState(false);
  const { models: iphoneModels } = useIphoneCatalog();

  useEffect(() => {
    document.documentElement.classList.add("cmp-mobile-home-active");
    let lastY = window.scrollY;
    const onScroll = () => {
      const y = window.scrollY;
      setNavState(y < 24 ? "top" : y > lastY ? "hidden" : "solid");
      lastY = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      document.documentElement.classList.remove("cmp-mobile-home-active");
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  useEffect(() => {
    const sectionFromHash = window.location.hash.replace(/^#/, "");
    let sectionFromStorage = "";

    try {
      sectionFromStorage = window.sessionStorage.getItem("televera:home-section") ?? "";
      window.sessionStorage.removeItem("televera:home-section");
    } catch {
      sectionFromStorage = "";
    }

    const target = sectionFromStorage || sectionFromHash;
    if (!["how", "why", "faq"].includes(target)) return;

    let attempts = 0;
    const scrollToSection = () => {
      const element = document.getElementById(target);
      if (!element) {
        if (attempts++ < 20) window.setTimeout(scrollToSection, 50);
        return;
      }
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      window.history.replaceState(null, "", `/#${target}`);
      setMenuOpen(false);
    };

    window.requestAnimationFrame(scrollToSection);
  }, []);

  const filteredModels = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle || selectedModel) return [];
    return iphoneModels.filter((model) => model.toLowerCase().includes(needle));
  }, [iphoneModels, query, selectedModel]);

  const startFlow = (model = selectedModel) => {
    const fallback = model || (query.trim() ? iphoneModels.find((item) => item.toLowerCase() === query.trim().toLowerCase()) : "");
    if (!fallback) {
      inputRef.current?.focus();
      setSearchOpen(true);
      return;
    }
    setLoading(true);
    window.setTimeout(() => navigate(`/salja/${modelToSlug(fallback)}`), 450);
  };

  const chooseModel = (model: string) => {
    setSelectedModel(model);
    setQuery(model);
    setSearchOpen(false);
    trackEvent("model_selected", {
      funnel: "quote",
      surface: "mobile",
      entry_point: "home_search",
      model,
    });
    trackEvent("quote_started", {
      funnel: "quote",
      surface: "mobile",
      entry_point: "home_search",
      model,
    });
  };

  const trackSearchStarted = () => {
    if (searchStartedTrackedRef.current) return;
    searchStartedTrackedRef.current = true;
    trackEvent("quote_search_started", {
      funnel: "quote",
      surface: "mobile",
      entry_point: "home_search",
    });
  };

  const handleSellNow = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    window.setTimeout(() => startFlow(), 160);
  };

  return (
    <div className="cmp-mobile-home">
      <header className={`cmp-mobile-nav ${navState}`}>
        <a className="cmp-mobile-brand" href="#top" aria-label="Televera startsida">
          <img src={logoGreen} alt="" />
        </a>
        <button type="button" className="cmp-mobile-sell" onClick={handleSellNow}>
          Sälj nu
        </button>
        <button
          type="button"
          className="cmp-mobile-menu-btn"
          onClick={() => setMenuOpen((current) => !current)}
          aria-label={menuOpen ? "Stäng meny" : "Öppna meny"}
        >
          {menuOpen ? <X aria-hidden /> : <Menu aria-hidden />}
        </button>
      </header>

      {menuOpen ? (
        <nav className="cmp-mobile-menu" aria-label="Mobilmeny">
          <a href="https://televera.se/#how" onClick={() => setMenuOpen(false)}>Så funkar det</a>
          <a href="https://televera.se/#why" onClick={() => setMenuOpen(false)}>Varför oss</a>
          <a href="https://televera.se/#faq" onClick={() => setMenuOpen(false)}>Vanliga frågor</a>
          <a href="/artiklar" onClick={() => setMenuOpen(false)}>Artiklar</a>
          <a href="/om-oss" onClick={() => setMenuOpen(false)}>Om oss</a>
        </nav>
      ) : null}

      <section className="cmp-mobile-hero" id="top">
        <div className="cmp-mobile-hero-inner">
          <h1>
            Hitta <Highlight>bästa priset</Highlight>
            <br />
            för din mobil
          </h1>
          <p className="cmp-mobile-hand">helt gratis!</p>

          <div className="cmp-mobile-search">
            <Search aria-hidden />
            <input
              ref={inputRef}
              value={query}
              placeholder="Sök modell, t.ex. iPhone 14 Pro..."
              onChange={(event) => {
                setQuery(event.target.value);
                setSelectedModel("");
                setSearchOpen(true);
                trackSearchStarted();
              }}
              onFocus={() => {
                window.scrollTo({ top: 0, behavior: "instant" });
                setSearchOpen(Boolean(query.trim()));
                trackSearchStarted();
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") startFlow();
              }}
            />
            <button type="button" onClick={() => startFlow()} disabled={!selectedModel || loading} data-active={Boolean(selectedModel)} data-loading={loading}>
              <span>Jämför bud</span>
            </button>
            {searchOpen && filteredModels.length > 0 ? (
              <div className="cmp-mobile-search-menu">
                {filteredModels.map((model) => (
                  <button key={model} type="button" onMouseDown={() => chooseModel(model)}>
                    <span className="cmp-mobile-search-thumb" aria-hidden>
                      <img src={getIphoneImage(model)} alt="" loading="lazy" decoding="async" />
                    </span>
                    <span>{model}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <div className="cmp-mobile-trust-chips" aria-label="Fördelar">
            {trustChips.map((item) => (
              <span key={item}>
                <Check aria-hidden />
                {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="cmp-mobile-partners" aria-label="Partners">
        <p>Vi jämför bud från Sveriges återförsäljare</p>
        <div className="cmp-mobile-partners-track">
          {marqueeGroups.map((groupIndex) => (
            <div
              className="cmp-mobile-partners-group"
              key={groupIndex}
              aria-hidden={groupIndex === 1}
            >
              {partners.map((partner) => (
                <span
                  className={[partner.compact ? "compact" : "", partner.className ?? ""]
                    .filter(Boolean)
                    .join(" ") || undefined}
                  key={`${partner.alt}-${groupIndex}`}
                >
                  <img src={partner.src} alt={groupIndex === 0 ? partner.alt : ""} />
                </span>
              ))}
            </div>
          ))}
        </div>
      </section>

      <section className="cmp-mobile-section cmp-mobile-how" id="how">
        {steps.map((step, index) => {
          const Icon = step.icon;
          return (
            <article key={step.title} className="cmp-mobile-step-card">
              <span>{index + 1}</span>
              <Icon aria-hidden />
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </article>
          );
        })}
      </section>

      <section className="cmp-mobile-section cmp-mobile-why" id="why">
        <p className="cmp-mobile-kicker">Varför oss</p>
        <h2>Mindre krångel, mer betalt</h2>
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
      </section>

      <section className="cmp-mobile-section cmp-mobile-faq" id="faq">
        <p className="cmp-mobile-kicker">Vanliga frågor</p>
        <h2>Bra att veta</h2>
        <div>
          {faqs.map((faq, index) => {
            const open = openFaq === index;
            return (
              <article key={faq.q} className={open ? "open" : ""}>
                <button type="button" onClick={() => setOpenFaq(open ? null : index)}>
                  <span>{faq.q}</span>
                  <ChevronDown aria-hidden />
                </button>
                {open ? <p>{faq.a}</p> : null}
              </article>
            );
          })}
        </div>
      </section>

      <section className="cmp-mobile-final-cta">
        <h2>Redo att sälja din mobil?</h2>
        <p>Se bud från flera återförsäljare på ett par minuter.</p>
        <button type="button" onClick={handleSellNow}>
          <Search aria-hidden /> Jämför bud nu
        </button>
        <span>helt gratis!</span>
      </section>

      <footer className="cmp-mobile-footer">
        <div>
          <img src={logoGreen} alt="" />
        </div>
        <p>Vi hjälper dig sälja din telefon till återförsäljaren som betalar bäst. Gratis, utan krångel.</p>
        <div className="cmp-mobile-footer-links">
          <nav aria-label="Tjänsten">
            <h3>Tjänsten</h3>
            <a href="https://televera.se/#how">Så funkar det</a>
            <a href="https://televera.se/#why">Varför oss</a>
            <a href="https://televera.se/#faq">Vanliga frågor</a>
          </nav>
          <nav aria-label="Företaget">
            <h3>Företaget</h3>
            <a href="/om-oss">Om oss</a>
            <a href="/artiklar">Artiklar</a>
            <a href="mailto:info@televera.se">Kontakt</a>
          </nav>
          <nav aria-label="Juridik">
            <h3>Juridik</h3>
            <a href="/villkor">Villkor</a>
            <a href="/integritet">Integritet</a>
            <a href="/cookies">Cookies</a>
          </nav>
        </div>
        <small>© 2026 Televera. Alla rättigheter förbehållna.</small>
      </footer>
    </div>
  );
};

export default MobileHome;
