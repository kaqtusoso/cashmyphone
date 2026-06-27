import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowRight, Building2, Mail, Phone } from "lucide-react";
import pascalImg from "@/assets/pascal.jpg";

const ABOUT_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "AboutPage",
  name: "Om Televera.se",
  url: "https://televera.se/om-oss",
  description:
    "Om Televera.se - en gratis svensk tjänst som jämför vad uppköpare betalar för din begagnade mobil. Grundad av Pascal.",
};

const wavePath =
  "M0 10 Q10 2 20 10 Q30 18 40 10 Q50 2 60 10 Q70 18 80 10 Q90 2 100 10 Q110 18 120 10 Q130 2 140 10 Q150 18 160 10 Q170 2 180 10 Q190 18 200 10 Q210 2 220 10 Q230 18 240 10 Q250 2 260 10 Q270 18 280 10 Q290 2 300 10 Q310 18 320 10 Q330 2 340 10 Q350 18 360 10 Q370 2 380 10 Q390 18 400 10";

const storyCards = [
  {
    number: "1",
    label: "Problemet",
    title: "Flik-kaoset",
    body: "Jag skulle sälja min gamla iPhone. Jag öppnade en flik per uppköpare, försökte hålla reda på villkoren och gav till slut upp. Prisskillnaden jag missade var flera hundralappar.",
    footer: "Det måste finnas ett bättre sätt",
  },
  {
    number: "2",
    label: "Lösningen",
    title: "Televera byggs",
    body: "Jag byggde en enkel tjänst som samlar bud på ett ställe. Televera köper inga telefoner själv och försöker inte styra dig mot ett visst val - tanken är bara att göra jämförelsen tydligare.",
    footer: "Oberoende, transparent, gratis",
  },
  {
    number: "3",
    label: "Idag",
    title: "Lugnare beslut",
    body: "Idag hjälper Televera tusentals svenskar att fatta ett välgrundat beslut - och se till att de faktiskt får rätt betalt för sin gamla mobil, utan att behöva hålla koll i tio flikar.",
    footer: "Det är det Televera är till för",
    featured: true,
  },
];

const ContactIcon = ({ type }: { type: "mail" | "phone" | "org" }) => {
  const iconClass = "h-[18px] w-[18px] text-[#05B87A]";
  if (type === "mail") return <Mail className={iconClass} aria-hidden />;
  if (type === "phone") return <Phone className={iconClass} aria-hidden />;
  return <Building2 className={iconClass} aria-hidden />;
};

const AboutPage = () => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-[#f7f5ef] text-[#14181f] [font-family:'Plus_Jakarta_Sans',var(--font-body)]">
      <Helmet>
        <title>Om oss - Televera.se</title>
        <meta
          name="description"
          content="Lär känna personen bakom Televera.se - Sveriges gratis tjänst för att jämföra vad uppköpare betalar för din mobil."
        />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://televera.se/om-oss" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
        <meta property="og:title" content="Om oss - Televera.se" />
        <meta
          property="og:description"
          content="Historien bakom Televera - grundad av Pascal för att hjälpa svenskar få bättre överblick när de säljer sin gamla mobil."
        />
        <meta property="og:url" content="https://televera.se/om-oss" />
        <script type="application/ld+json">{JSON.stringify(ABOUT_JSON_LD)}</script>
      </Helmet>

      <main>
        <section className="relative overflow-hidden bg-[#05B87A]">
          <div className="mx-auto grid max-w-[960px] items-end gap-10 px-5 pt-28 sm:px-10 md:grid-cols-[1fr_340px] md:gap-12 md:px-20 md:pt-[120px]">
            <div className="pb-10 md:pb-[52px]">
              <h1 className="max-w-[620px] text-[clamp(38px,5vw,62px)] font-extrabold leading-[1.04] tracking-normal text-white [text-wrap:balance]">
                Hej, jag heter Pascal
              </h1>
              <p className="mt-4 max-w-[560px] text-[17px] leading-[1.7] text-white/75">
                Jag grundade Televera för att göra det enkelt att jämföra vad uppköpare betalar för din begagnade
                mobil - allt på ett ställe, gratis.
              </p>
            </div>

            <div className="relative mx-auto flex w-full max-w-[340px] items-end justify-center self-end md:mx-0">
              <div className="relative z-10 h-[360px] w-full max-w-[340px] flex-none overflow-hidden rounded-t-xl border-[2.5px] border-white/35 shadow-[0_0_0_5px_rgba(255,255,255,0.1),0_16px_40px_rgba(0,0,0,0.2)] sm:h-[420px]">
                <img
                  src={pascalImg}
                  alt="Pascal, grundare av Televera"
                  className="mt-[-6%] block h-[118%] w-full object-cover object-center"
                  width={340}
                  height={420}
                  loading="eager"
                  decoding="async"
                />
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-[1120px] px-5 pt-14 sm:px-10 md:pt-16">
          <div className="mb-10 flex items-center gap-4">
            <div className="h-5 flex-1 overflow-hidden">
              <svg width="100%" height="20" viewBox="0 0 400 20" preserveAspectRatio="none" fill="none" aria-hidden>
                <path d={wavePath} stroke="#05B87A" strokeWidth="2.2" strokeLinecap="round" />
              </svg>
            </div>
            <h2 className="flex-none whitespace-nowrap text-[28px] font-bold tracking-normal text-[#14181f] [font-family:'Caveat',cursive]">
              Historien bakom Televera
            </h2>
            <div className="h-5 flex-1 overflow-hidden">
              <svg width="100%" height="20" viewBox="0 0 400 20" preserveAspectRatio="none" fill="none" aria-hidden>
                <path d={wavePath} stroke="#05B87A" strokeWidth="2.2" strokeLinecap="round" />
              </svg>
            </div>
          </div>

          <div className="relative">
            <div
              className="pointer-events-none absolute left-[calc(16.66%+24px)] right-[calc(16.66%+24px)] top-14 hidden h-0.5 bg-[linear-gradient(90deg,#00b87a_55%,transparent_55%)] bg-[length:14px_2px] opacity-35 md:block"
              aria-hidden="true"
            />

            <div className="relative z-10 grid gap-5 md:grid-cols-3">
              {storyCards.map((card) => (
                <article
                  key={card.number}
                  className={[
                    "rounded-[18px] border-[1.5px] p-[32px_26px_28px] transition duration-200 hover:-translate-y-1 hover:rotate-[-0.4deg]",
                    card.featured
                      ? "border-[#04a36c] bg-[#05B87A] shadow-[0_1px_2px_rgba(20,24,31,0.08),0_4px_16px_rgba(5,184,122,0.25)] hover:shadow-[0_8px_24px_rgba(5,184,122,0.35)]"
                      : "border-[#e7e3d8] bg-[#fffdf8] shadow-[0_1px_2px_rgba(20,24,31,0.04),0_2px_8px_rgba(20,24,31,0.05)] hover:shadow-[0_8px_24px_rgba(20,24,31,0.09)]",
                  ].join(" ")}
                >
                  <div className="mb-5 flex items-center gap-2.5">
                    <span
                      className={[
                        "flex h-12 w-12 flex-none items-center justify-center rounded-full text-xl font-extrabold",
                        card.featured
                          ? "bg-white text-[#05B87A] shadow-[0_0_0_6px_rgba(255,255,255,0.2)]"
                          : "bg-[#05B87A] text-white shadow-[0_0_0_6px_#fffdf8,0_0_0_7.5px_#e7f7ef]",
                      ].join(" ")}
                    >
                      {card.number}
                    </span>
                    <span
                      className={[
                        "text-[11px] font-bold uppercase tracking-[0.08em]",
                        card.featured ? "text-white/65" : "text-[#b0b8c1]",
                      ].join(" ")}
                    >
                      {card.label}
                    </span>
                  </div>
                  <h3 className={["mb-3 text-xl font-extrabold leading-[1.2]", card.featured ? "text-white" : "text-[#14181f]"].join(" ")}>
                    {card.title}
                  </h3>
                  <p className={["text-[14.5px] leading-[1.7]", card.featured ? "text-white/85" : "text-[#5b626d]"].join(" ")}>
                    {card.body}
                  </p>
                  <div
                    className={[
                      "mt-[18px] flex items-center gap-1.5 border-t pt-4 text-[13px] font-semibold",
                      card.featured ? "border-white/20 text-white" : "border-[#e7e3d8] text-[#05B87A]",
                    ].join(" ")}
                  >
                    <ArrowRight className="h-3.5 w-3.5" aria-hidden />
                    {card.footer}
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-16 bg-[#F0EDE4]">
          <div className="mx-auto max-w-[1120px] px-5 py-14 sm:px-10 md:pb-16 md:pt-[52px]">
            <h2 className="mb-6 text-[22px] font-extrabold text-[#14181f]">Kontakt &amp; företagsuppgifter</h2>
            <div className="grid gap-4 md:grid-cols-3">
              {[
                { type: "mail" as const, label: "E-post", value: "televerasverige@gmail.com", href: "mailto:televerasverige@gmail.com" },
                { type: "phone" as const, label: "Telefon", value: "+46 70 232 06 15", href: "tel:+46702320615" },
                { type: "org" as const, label: "Organisationsnummer", value: "031129-9515" },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-2xl border-[1.5px] border-[#e7e3d8] bg-[#fffdf8] p-[24px_22px] shadow-[0_1px_2px_rgba(20,24,31,0.04)]"
                >
                  <div className="mb-3.5 flex h-10 w-10 items-center justify-center rounded-[10px] bg-[#e7f7ef]">
                    <ContactIcon type={item.type} />
                  </div>
                  <div className="mb-1.5 text-xs font-bold uppercase tracking-[0.06em] text-[#aaa]">{item.label}</div>
                  {item.href ? (
                    <a href={item.href} className="text-sm font-semibold text-[#14181f] transition-colors hover:text-[#05B87A]">
                      {item.value}
                    </a>
                  ) : (
                    <span className="text-sm font-semibold text-[#14181f]">{item.value}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-[#F4F4ED] px-5 py-[72px] text-center sm:px-10">
          <h2 className="mx-auto max-w-[520px] text-[clamp(22px,3vw,32px)] font-extrabold leading-tight tracking-normal text-[#14181f] [text-wrap:balance]">
            Redo att se vad din telefon kan vara värd?
          </h2>
          <p className="mx-auto mt-3.5 max-w-[420px] text-[15px] leading-[1.7] text-[#5b626d]">
            Artiklarna hjälper dig förstå marknaden. Värderingen visar vad flera uppköpare erbjuder just nu.
          </p>
          <Link
            to="/"
            className="mt-7 inline-flex items-center gap-2 rounded-lg bg-[#05B87A] px-[26px] py-3.5 text-[15px] font-bold text-white transition-colors hover:bg-[#009f69]"
          >
            Jämför priser gratis
            <ArrowRight className="h-3.5 w-3.5" aria-hidden />
          </Link>
        </section>
      </main>
    </div>
  );
};

export default AboutPage;
