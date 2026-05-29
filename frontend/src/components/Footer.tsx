import { Building2, Mail, Phone } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";

const Footer = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleSellClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (location.pathname === "/") {
      window.scrollTo({ top: 0, left: 0, behavior: "smooth" });
    } else {
      navigate("/");
    }
  };

  const handleAnchorClick = (id: string) => (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (location.pathname === "/") {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      navigate(`/#${id}`);
    }
  };

  return (
    <footer className="py-12 px-6 bg-[hsl(220,20%,14%)] text-[hsl(220,10%,70%)]">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-10 md:gap-8">
        {/* Brand */}
        <div className="space-y-3">
          <div className="flex items-center">
            <img src="/favicon.png" alt="CashMyPhone" className="h-7 w-7" />
          </div>
          <p className="text-sm leading-relaxed">
            Sveriges smartaste mobiltjänst. Jämför vad olika uppköpare betalar för din mobil – helt gratis.
          </p>
        </div>

        {/* Utforska */}
        <div className="space-y-3">
          <h3 className="flex items-center pt-px text-lg font-heading font-bold text-white leading-none">Utforska</h3>
          <ul className="text-sm leading-relaxed">
            <li>
              <a
                href="/#hur-det-fungerar"
                onClick={handleAnchorClick("hur-det-fungerar")}
                className="hover:text-white transition-colors"
              >
                Hur det fungerar
              </a>
            </li>
            <li>
              <a href="/" onClick={handleSellClick} className="hover:text-white transition-colors">
                Sälj din mobil
              </a>
            </li>
            <li>
              <Link to="/artiklar" className="hover:text-white transition-colors">
                Artiklar & guider
              </Link>
            </li>
          </ul>
        </div>

        {/* Om CashMyPhone */}
        <div className="space-y-3">
          <h3 className="flex items-center pt-px text-lg font-heading font-bold text-white leading-none">
            Om CashMyPhone
          </h3>
          <ul className="text-sm leading-relaxed">
            <li>
              <Link to="/om-oss" className="hover:text-white transition-colors">
                Om oss
              </Link>
            </li>
            <li>
              <Link to="/artiklar" className="hover:text-white transition-colors">
                Artiklar & guider
              </Link>
            </li>
            <li>
              <a href="/#faq" onClick={handleAnchorClick("faq")} className="hover:text-white transition-colors">
                Vanliga frågor
              </a>
            </li>
          </ul>
        </div>

        {/* Kontakt */}
        <div className="space-y-3">
          <h3 className="flex items-center pt-px text-lg font-heading font-bold text-white leading-none">Kontakt</h3>
          <ul className="text-sm leading-relaxed space-y-1">
            <li>
              <a
                href="mailto:brjanssonp@gmail.com"
                className="flex items-center gap-2 hover:text-white transition-colors"
              >
                <Mail className="w-4 h-4 shrink-0" />
                <span>brjanssonp@gmail.com</span>
              </a>
            </li>
            <li>
              <a href="tel:+46702320615" className="flex items-center gap-2 hover:text-white transition-colors">
                <Phone className="w-4 h-4 shrink-0" />
                <span>+46 70 232 06 15</span>
              </a>
            </li>
            <li className="flex items-center gap-2">
              <Building2 className="w-4 h-4 shrink-0" />
              <span>Org.nr: 031129-9515</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="max-w-6xl mx-auto mt-10 pt-6 border-t border-[hsl(220,10%,24%)] flex flex-col md:flex-row items-center justify-between gap-2 text-xs">
        <span>© 2026 cashmyphone.se — Alla rättigheter förbehållna.</span>
        <span>Byggd och utvecklad med omtanke i Sverige 🇸🇪</span>
      </div>
    </footer>
  );
};

export default Footer;
