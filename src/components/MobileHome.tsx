import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BadgePercent,
  ChevronDown,
  Clock,
  Menu,
  Search,
  Shield,
  Scale,
  Truck,
  Wallet,
  X,
} from "lucide-react";

import { useIphoneCatalog } from "@/hooks/useIphoneCatalog";
import { modelToSlug } from "@/utils/modelSlug";

import logoGreen from "@/assets/logo-green.png";
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
  swappieLogo,
  fixmyphoneLogo,
  fixiphoneLogo,
  fixphoneproLogo,
  happyphoneLogo,
  renewedLogo,
  phoneheroLogo,
  telestoreLogo,
];

const steps = [
  {
    title: "Sök & jämför bud",
    text: "Skriv in din modell och se bud från flera återförsäljare direkt - på sekunder.",
    icon: Search,
  },
  {
    title: "Välj & skicka",
    text: "Välj det bästa budet och skicka telefonen gratis med en förbetald fraktsedel.",
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
    text: "Vi frågar flera återförsäljare åt dig, så du slipper mejla runt och jämföra själv.",
    icon: Scale,
  },
  {
    title: "Det kostar dig inget",
    text: "Vi köper inte din telefon - vi hittar köparen som betalar bäst. Du betalar aldrig en krona.",
    icon: BadgePercent,
  },
  {
    title: "Tryggt hela vägen",
    text: "Spårbar frakt, köpare vi känner till och utbetalning via Swish eller bank.",
    icon: Shield,
  },
];

const faqs = [
  {
    q: "Köper ni telefonen själva?",
    a: "Nej. Vi jämför bud från återförsäljare och skickar dig vidare till den köpare du väljer.",
  },
  {
    q: "Vad kostar det?",
    a: "Det är gratis att jämföra bud och frakten är förbetald när du säljer via en köpare i flödet.",
  },
  {
    q: "Hur snabbt får jag pengarna?",
    a: "Efter att köparen har kontrollerat mobilen betalas pengarna vanligtvis ut inom några arbetsdagar.",
  },
  {
    q: "Vad händer om skicket inte stämmer?",
    a: "Köparen kan ge ett nytt bud efter kontroll. Om du tackar nej skickas mobilen tillbaka enligt köparens villkor.",
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

  const filteredModels = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle || selectedModel) return [];
    return iphoneModels.filter((model) => model.toLowerCase().includes(needle)).slice(0, 7);
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
  };

  return (
    <div className="cmp-mobile-home">
      <header className={`cmp-mobile-nav ${navState}`}>
        <a className="cmp-mobile-brand" href="#top" aria-label="CashMyPhone startsida">
          <img src={logoGreen} alt="" />
        </a>
        <button type="button" className="cmp-mobile-sell" onClick={() => startFlow("iPhone 15 Pro")}>
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
          <a href="#how" onClick={() => setMenuOpen(false)}>Så funkar det</a>
          <a href="#why" onClick={() => setMenuOpen(false)}>Varför oss</a>
          <a href="#faq" onClick={() => setMenuOpen(false)}>Vanliga frågor</a>
        </nav>
      ) : null}

      <section className="cmp-mobile-hero" id="top">
        <div className="cmp-mobile-hero-inner">
          <h1>
            Hitta <Highlight>bästa priset</Highlight> för din
            <br />
            mobil
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
              }}
              onFocus={() => {
                window.scrollTo({ top: 0, behavior: "instant" });
                setSearchOpen(Boolean(query.trim()));
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
                    {model}
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <div className="cmp-mobile-pills" aria-label="Fördelar">
            <span><Clock aria-hidden /> Tar 30 sek</span>
            <span><Wallet aria-hidden /> Swish / bank</span>
            <span><Truck aria-hidden /> Fri frakt</span>
          </div>
        </div>
      </section>

      <section className="cmp-mobile-partners" aria-label="Partners">
        <p>Vi jämför bud från Sveriges återförsäljare</p>
        <div>
          {[...partners, ...partners].map((logo, index) => (
            <span key={`${logo}-${index}`}>
              <img src={logo} alt="" />
            </span>
          ))}
        </div>
      </section>

      <section className="cmp-mobile-section cmp-mobile-how" id="how">
        <p className="cmp-mobile-kicker">Så funkar det</p>
        <h2>Tre enkla steg</h2>
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
        <button type="button" onClick={() => startFlow("iPhone 15 Pro")}>
          <Search aria-hidden /> Jämför bud nu
        </button>
        <span>helt gratis!</span>
      </section>

      <footer className="cmp-mobile-footer">
        <div>
          <img src={logoGreen} alt="" />
          <strong>CashMyPhone</strong>
        </div>
        <p>Vi hjälper dig sälja din telefon till återförsäljaren som betalar bäst. Gratis, utan krångel.</p>
        <small>© 2026 CashMyPhone. Alla rättigheter förbehållna.</small>
      </footer>
    </div>
  );
};

export default MobileHome;
