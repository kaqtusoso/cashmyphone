import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowLeft, Building2, Mail, Phone } from "lucide-react";
import pascalImg from "@/assets/pascal.webp";
import televeraLogo from "@/assets/televera-logo-full.png";

const ABOUT_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "AboutPage",
  name: "Om Televera.se",
  url: "https://televera.se/om-oss",
  description:
    "Om Televera.se – en gratis svensk tjänst som jämför vad uppköpare betalar för din begagnade mobil. Grundad av Pascal.",
};

const AboutPage = () => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-[#f7f5ef] text-[#14181f]">
      <Helmet>
        <title>Om oss – Televera.se</title>
        <meta
          name="description"
          content="Lär känna personen bakom Televera.se – Sveriges gratis tjänst för att jämföra vad uppköpare betalar för din mobil."
        />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://televera.se/om-oss" />
        <meta property="og:title" content="Om oss – Televera.se" />
        <meta
          property="og:description"
          content="Historien bakom Televera – grundad av Pascal för att hjälpa svenskar få bäst betalt för sin gamla mobil."
        />
        <meta property="og:url" content="https://televera.se/om-oss" />
        <script type="application/ld+json">{JSON.stringify(ABOUT_JSON_LD)}</script>
      </Helmet>

      <header className="border-b border-[#e7e3d8] bg-[#fffdf8]">
      </header>

      <main>
        <section className="mx-auto grid max-w-4xl gap-9 px-5 py-12 md:grid-cols-[1fr_220px] md:px-8 md:py-16">
          <div className="md:order-2 md:pt-16">
            <img
              src={pascalImg}
              alt="Pascal, grundare av Televera.se"
              width={220}
              height={241}
              loading="lazy"
              decoding="async"
              className="aspect-[11/12] w-40 rounded-lg border border-[#e7e3d8] object-cover md:w-[220px]"
            />
          </div>

          <article className="md:order-1">
            <h1 className="max-w-2xl text-4xl font-extrabold leading-tight md:text-5xl">
              Hej, jag heter Pascal
            </h1>
            <div className="mt-7 space-y-5 text-lg leading-8 text-[#3d444d]">
              <p>
                och är grundaren bakom Televera. Projektet startade efter att jag själv skulle sälja min gamla iPhone. Det borde ha varit enkelt, men
                jag hamnade i samma flik-kaos som många andra: olika uppköpare, olika villkor och priser som skilde
                sig mer än man först tror.
              </p>
              <p>
                Därför byggde jag en enkel tjänst som samlar bud på ett ställe. Televera köper inte telefonen själv
                och försöker inte låsa in någon i ett visst val. Tanken är bara att göra jämförelsen tydligare, så att
                du kan fatta ett lugnare beslut.
              </p>
            </div>
          </article>
        </section>

        <section className="mx-auto max-w-4xl px-4 pb-14 md:px-8 md:pb-10">
          <div className="border-t border-[#e7e3d8] pt-8">
            <h2 className="text-xl font-extrabold">Kontakt & företagsuppgifter</h2>
            <ul className="mt-4 space-y-3 text-sm text-[#3d444d]">
              <li className="flex items-center gap-3">
                <Mail className="h-4 w-4 text-[#00b87a]" aria-hidden />
                <a href="mailto:televerasverige@gmail.com" className="transition-colors hover:text-[#00936a]">
                  televerasverige@gmail.com
                </a>
              </li>
              <li className="flex items-center gap-3">
                <Phone className="h-4 w-4 text-[#00b87a]" aria-hidden />
                <a href="tel:+46702320615" className="transition-colors hover:text-[#00936a]">
                  +46 70 232 06 15
                </a>
              </li>
              <li className="flex items-center gap-3">
                <Building2 className="h-4 w-4 text-[#00b87a]" aria-hidden />
                <span>Org.nr: 031129-9515</span>
              </li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
};

export default AboutPage;
