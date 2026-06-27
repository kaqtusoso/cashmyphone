import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import logoImg from "@/assets/televera-logo-full.png";

const navLinks = [
  { href: "https://televera.se/#how", section: "how", label: "Så funkar det" },
  { href: "https://televera.se/#why", section: "why", label: "Varför oss" },
  { href: "https://televera.se/#faq", section: "faq", label: "Vanliga frågor" },
];

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const [atTop, setAtTop] = useState(true);
  const [hidden, setHidden] = useState(false);
  const useArticleHeader = location.pathname === "/artiklar" || location.pathname.startsWith("/artikel/");
  const useHeroHeader = useArticleHeader || location.pathname === "/om-oss";

  useEffect(() => {
    if (!useHeroHeader) {
      setAtTop(false);
      setHidden(false);
      return;
    }

    let lastY = window.scrollY;
    const onScroll = () => {
      const y = window.scrollY;
      setAtTop(y < 24);
      if (useArticleHeader && y > lastY && y > 150) setHidden(true);
      if (useArticleHeader && y < lastY - 4) setHidden(false);
      lastY = y;
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [useArticleHeader, useHeroHeader]);

  const articleHeaderTop = useHeroHeader && atTop && !menuOpen;
  const articleHeaderSolid = useHeroHeader && (!atTop || menuOpen);
  const articleHeaderHidden = useArticleHeader && hidden && !menuOpen;
  const mobileCtaTop = useHeroHeader && atTop;

  const goToHomeSection = (section: string) => {
    try {
      window.sessionStorage.setItem("televera:home-section", section);
    } catch {
      // Navigation still works without sessionStorage; hash handles the fallback.
    }
    setMenuOpen(false);
    navigate({ pathname: "/", hash: section });
  };

  return (
    <header
      className={[
        useHeroHeader ? "fixed inset-x-0 top-0" : "sticky top-0",
        "z-50 border-b transition-[transform,background-color,border-color,box-shadow,backdrop-filter] duration-300",
        articleHeaderTop
          ? "border-transparent bg-transparent shadow-none backdrop-blur-0"
          : "border-[#e7e3d8] bg-[#fffdf8]/95 shadow-[0_2px_16px_rgba(20,24,31,0.05)] backdrop-blur-md",
        articleHeaderHidden ? "-translate-y-full" : "translate-y-0",
      ].join(" ")}
    >
      <div className="mx-auto flex h-[68px] max-w-[1140px] items-center gap-3 px-4 sm:px-7 md:gap-7">
        <Link to="/" className="flex items-center" aria-label="Televera startsida" onClick={() => setMenuOpen(false)}>
          <img
            src={logoImg}
            alt="Televera"
            className="h-auto w-[116px] object-contain sm:w-[132px]"
            width={132}
            fetchPriority="high"
            decoding="async"
          />
        </Link>

        <nav className="ml-auto hidden items-center gap-7 md:flex" aria-label="Huvudmeny">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className={[
                "text-[15px] font-medium transition-colors",
                articleHeaderTop ? "text-white/90 hover:text-white" : "text-[#5b626d] hover:text-[#00936a]",
              ].join(" ")}
            >
              {link.label}
            </a>
          ))}
        </nav>

        <a
          href="/#top"
          className={[
            "ml-auto hidden rounded-xl px-5 py-2.5 font-heading text-[15px] font-bold transition hover:-translate-y-0.5 hover:rotate-[-1deg] hover:shadow-[0_6px_18px_rgba(0,150,100,0.3)] md:ml-0 md:inline-flex",
            articleHeaderTop ? "bg-white text-[#00936a] hover:bg-[#f7f5ef]" : "bg-[#00b87a] text-white hover:bg-[#00936a]",
          ].join(" ")}
        >
          Sälj nu
        </a>

        <a
          href="/#top"
          className={[
            "ml-auto inline-flex min-h-9 items-center rounded-[10px] px-3 py-2 text-[13px] font-extrabold leading-none md:hidden sm:px-3.5",
            mobileCtaTop ? "bg-white text-[#00936a]" : "bg-[#00b87a] text-white",
          ].join(" ")}
        >
          Sälj nu
        </a>

        <button
          type="button"
          className={[
            "inline-flex h-9 w-9 items-center justify-center transition-colors md:hidden",
            articleHeaderTop ? "text-white" : "text-[#14181f]",
          ].join(" ")}
          onClick={() => setMenuOpen((current) => !current)}
          aria-label={menuOpen ? "Stäng meny" : "Öppna meny"}
          aria-expanded={menuOpen}
        >
          {menuOpen ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
        </button>
      </div>

      {menuOpen ? (
        <nav
          className={[
            "border-t px-4 py-3 md:hidden",
            articleHeaderSolid ? "border-[#e7e3d8] bg-[#fffdf8]" : "border-[#e7e3d8] bg-[#fffdf8]",
          ].join(" ")}
          aria-label="Mobilmeny"
        >
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="block rounded-lg px-3 py-3 text-sm font-bold text-[#14181f] transition hover:bg-[#e7f7ef] hover:text-[#00936a]"
              onClick={(event) => {
                event.preventDefault();
                goToHomeSection(link.section);
              }}
            >
              {link.label}
            </a>
          ))}
          <a
            href="/artiklar"
            className="block rounded-lg px-3 py-3 text-sm font-bold text-[#14181f] transition hover:bg-[#e7f7ef] hover:text-[#00936a]"
            onClick={() => setMenuOpen(false)}
          >
            Artiklar
          </a>
          <a
            href="/om-oss"
            className="block rounded-lg px-3 py-3 text-sm font-bold text-[#14181f] transition hover:bg-[#e7f7ef] hover:text-[#00936a]"
            onClick={() => setMenuOpen(false)}
          >
            Om oss
          </a>
        </nav>
      ) : null}
    </header>
  );
};

export default Header;
