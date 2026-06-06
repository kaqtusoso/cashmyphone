import logoGreen from "@/assets/logo-green.png";
import "./SiteFooter.css";

const SiteFooter = () => (
  <>
    <footer className="cmp-site-footer cmp-site-footer-desktop">
      <div className="cmp-site-footer-wrap">
        <div className="cmp-site-footer-grid">
          <div>
            <a className="cmp-site-footer-brand" href="/">
              <img src={logoGreen} alt="" />
              CashMyPhone
            </a>
            <p>Vi hjälper dig sälja din telefon till återförsäljaren som betalar bäst. Gratis, och utan krångel.</p>
          </div>
          <nav>
            <h3>Tjänsten</h3>
            <a href="/#how">Så funkar det</a>
            <a href="/#why">Varför oss</a>
            <a href="/#faq">Vanliga frågor</a>
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
        <div className="cmp-site-footer-bottom">
          <span>© 2026 CashMyPhone. Alla rättigheter förbehållna.</span>
          <span>Utbetalning via Swish &amp; banköverföring</span>
        </div>
      </div>
    </footer>

    <footer className="cmp-site-footer-mobile">
      <div>
        <img src={logoGreen} alt="" />
        <strong>CashMyPhone</strong>
      </div>
      <p>Vi hjälper dig sälja din telefon till återförsäljaren som betalar bäst. Gratis, utan krångel.</p>
      <small>© 2026 CashMyPhone. Alla rättigheter förbehållna.</small>
    </footer>
  </>
);

export default SiteFooter;
