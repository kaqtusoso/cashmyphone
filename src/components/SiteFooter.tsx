import logoGreen from "@/assets/televera-logo-full.png";
import "./SiteFooter.css";

const SiteFooter = () => (
  <>
    <footer className="cmp-site-footer cmp-site-footer-desktop">
      <div className="cmp-site-footer-wrap">
        <div className="cmp-site-footer-grid">
          <div>
            <a className="cmp-site-footer-brand" href="/">
              <img src={logoGreen} alt="" />
            </a>
            <p>Vi hjälper dig sälja din telefon till återförsäljaren som betalar bäst. Gratis, och utan krångel.</p>
          </div>
          <nav>
            <h3>Tjänsten</h3>
            <a href="https://televera.se/#how">Så funkar det</a>
            <a href="https://televera.se/#why">Varför oss</a>
            <a href="https://televera.se/#faq">Vanliga frågor</a>
          </nav>
          <nav>
            <h3>Företaget</h3>
            <a href="/om-oss">Om oss</a>
            <a href="/artiklar">Artiklar</a>
            <a href="mailto:info@televera.se">Kontakt</a>
          </nav>
          <nav>
            <h3>Juridik</h3>
            <a href="/villkor">Villkor</a>
            <a href="/integritet">Integritet</a>
            <a href="/cookies">Cookies</a>
          </nav>
        </div>
        <div className="cmp-site-footer-bottom">
          <span>© 2026 Televera. Alla rättigheter förbehållna.</span>
          <span>Byggd och utvecklad med omtanke i Sverige 🇸🇪</span>
        </div>
      </div>
    </footer>

    <footer className="cmp-site-footer-mobile">
      <div>
        <img src={logoGreen} alt="" />
      </div>
      <p>Vi hjälper dig sälja din telefon till återförsäljaren som betalar bäst. Gratis, utan krångel.</p>
      <div className="cmp-site-footer-mobile-links">
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
  </>
);

export default SiteFooter;
