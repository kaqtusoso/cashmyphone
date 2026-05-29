import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowLeft, Mail, Phone, Building2 } from "lucide-react";
import pascalImg from "@/assets/pascal.webp";

const ABOUT_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "AboutPage",
  name: "Om CashMyPhone.se",
  url: "https://cashmyphone.se/om-oss",
  description:
    "Om CashMyPhone.se – en gratis svensk tjänst som jämför vad uppköpare betalar för din begagnade mobil. Grundad av Pascal.",
};

const AboutPage = () => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>Om oss – CashMyPhone.se</title>
        <meta
          name="description"
          content="Lär känna personen bakom CashMyPhone.se – Sveriges gratis tjänst för att jämföra vad uppköpare betalar för din mobil."
        />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://cashmyphone.se/om-oss" />
        <meta property="og:title" content="Om oss – CashMyPhone.se" />
        <meta
          property="og:description"
          content="Historien bakom CashMyPhone – grundad av Pascal för att hjälpa svenskar få bäst betalt för sin gamla mobil."
        />
        <meta property="og:url" content="https://cashmyphone.se/om-oss" />
        <script type="application/ld+json">{JSON.stringify(ABOUT_JSON_LD)}</script>
      </Helmet>

      <div className="max-w-3xl mx-auto px-4 pt-4 pb-12 md:pt-6 md:pb-20">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka till startsidan
        </Link>

        <header className="mb-10 md:mb-14">
          <h1 className="text-3xl md:text-5xl font-heading font-bold text-foreground leading-tight">
            Historien bakom <span className="text-primary">CashMyPhone</span>
          </h1>
          <p className="mt-4 text-lg text-muted-foreground leading-relaxed">
            En gratis tjänst byggd för att svenskar ska slippa gissa sig fram till vem som faktiskt betalar bäst för
            deras begagnade mobil.
          </p>
        </header>

        <section className="grid md:grid-cols-[220px_1fr] gap-6 md:gap-10 items-start mb-10">
          <div className="relative mx-auto md:mx-0 w-40 md:w-[220px]">
            <div
              aria-hidden
              className="absolute inset-0 rounded-2xl bg-primary translate-x-2 translate-y-2 md:translate-x-3 md:translate-y-3"
            />
            <img
              src={pascalImg}
              alt="Pascal, grundare av CashMyPhone.se"
              width={220}
              height={241}
              loading="lazy"
              decoding="async"
              className="relative w-40 md:w-[220px] h-auto rounded-2xl object-cover border border-border"
            />
          </div>
          <div>
            <h2 className="text-2xl md:text-3xl font-heading font-bold text-foreground mb-3">Hej, jag heter Pascal</h2>
            <div className="space-y-4 text-foreground/90 leading-relaxed">
              <p>
                och är grundaren av CashMyPhone. Projektet startade efter att jag själv skulle sälja min gamla iPhone.
                Vad jag trodde skulle bli en enkel process visade sig snabbt bli rörigt: priserna varierade kraftigt
                mellan uppköpare och det var nästan omöjligt att veta vem som faktiskt betalade bäst just den dagen.
              </p>
              <p>
                Efter att ha klickat mig igenom flera olika sajter insåg jag att det här borde gå att lösa på 30
                sekunder istället för en hel eftermiddag. Därför byggde jag CashMyPhone.se – en gratis tjänst som visar
                dig direkt vem som betalar mest för just din mobil.
              </p>
            </div>
          </div>
        </section>

        <section className="bg-card border border-border rounded-2xl p-6 md:p-8 mb-10">
          <h2 className="text-lg font-heading font-bold text-foreground mb-4">Kontakt & företagsuppgifter</h2>
          <ul className="space-y-3 text-sm text-foreground/90">
            <li className="flex items-center gap-3">
              <Mail className="w-4 h-4 text-primary shrink-0" />
              <a href="mailto:brjanssonp@gmail.com" className="hover:text-primary transition-colors">
                brjanssonp@gmail.com
              </a>
            </li>
            <li className="flex items-center gap-3">
              <Phone className="w-4 h-4 text-primary shrink-0" />
              <a href="tel:+46702320615" className="hover:text-primary transition-colors">
                +46 70 232 06 15
              </a>
            </li>
            <li className="flex items-center gap-3">
              <Building2 className="w-4 h-4 text-primary shrink-0" />
              <span>Org.nr: 031129-9515</span>
            </li>
          </ul>
        </section>

        <div className="text-center">
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 bg-primary text-primary-foreground font-semibold px-6 py-3 rounded-xl hover:opacity-90 transition-opacity"
          >
            Värdera din mobil nu →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
