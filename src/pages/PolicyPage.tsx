import { useEffect } from "react";
import { Helmet } from "react-helmet-async";
import { Link } from "react-router-dom";
import { ArrowLeft, Building2, Mail, Phone } from "lucide-react";

type PolicyType = "terms" | "privacy" | "cookies";

type PolicySection = {
  heading: string;
  paragraphs: string[];
};

type PolicyContent = {
  title: string;
  description: string;
  canonicalPath: string;
  updated: string;
  intro: string;
  sections: PolicySection[];
};

const contactEmail = "brjanssonp@gmail.com";
const contactPhone = "+46 70 232 06 15";
const orgNumber = "031129-9515";

const policies: Record<PolicyType, PolicyContent> = {
  terms: {
    title: "Villkor",
    description:
      "Villkor för Televera.se, en jämförelsetjänst som hjälper dig jämföra erbjudanden från uppköpare av begagnade enheter.",
    canonicalPath: "/villkor",
    updated: "9 juni 2026",
    intro:
      "Dessa villkor gäller när du använder Televera.se. Tjänsten är byggd för att göra det enklare att jämföra erbjudanden från företag som köper begagnade enheter.",
    sections: [
      {
        heading: "1. Om tjänsten",
        paragraphs: [
          "Televera är en jämförelsetjänst. Vi samlar och visar uppskattade priser, villkor och annan praktisk information från externa uppköpare. Televera köper inte din enhet själv och är inte part i det slutliga köpet.",
          "När du går vidare med ett erbjudande sker affären mellan dig och den uppköpare du väljer. Uppköparens egna köpvillkor gäller för bland annat frakt, kontroll av enheten, betalning, prisjustering och eventuell retur.",
        ],
      },
      {
        heading: "2. Priser och värderingar",
        paragraphs: [
          "Priserna som visas på Televera är uppskattningar baserade på informationen du anger, till exempel modell, lagring, skick och batterihälsa. Det slutliga priset fastställs normalt först efter att uppköparen har tagit emot och kontrollerat enheten.",
          "Vi försöker hålla informationen korrekt och uppdaterad, men kan inte garantera att alla priser, lagerstatusar, kampanjer eller villkor alltid är helt aktuella. Om något skiljer sig är det uppköparens slutliga besked som gäller.",
        ],
      },
      {
        heading: "3. Ditt ansvar",
        paragraphs: [
          "Du ansvarar för att uppgifterna du lämnar är korrekta och att du har rätt att sälja enheten. Enheten får inte vara stulen, spärrad, operatörslåst på ett sätt som hindrar försäljning eller föremål för obetalda avbetalningar.",
          "Du ansvarar också för att ta bort personligt innehåll, säkerhetslås och kontokopplingar, till exempel Hitta min iPhone eller motsvarande funktioner, innan enheten skickas till uppköparen.",
        ],
      },
      {
        heading: "4. Beställningar och förmedling",
        paragraphs: [
          "Om du fyller i dina kontakt- och orderuppgifter via Televera skickar vi de uppgifter som behövs vidare till den uppköpare du har valt, så att uppköparen kan hantera affären och kontakta dig.",
          "Televera ansvarar inte för uppköparens handläggning, betalning, frakt, tekniska kontroll, prisjustering eller kundsupport. Kontakta uppköparen direkt i frågor som rör den slutliga försäljningen.",
        ],
      },
      {
        heading: "5. Ansvarsbegränsning",
        paragraphs: [
          "Televera tillhandahålls i befintligt skick. Vi ansvarar inte för indirekta skador, utebliven vinst, förlorad data eller andra följder som beror på användningen av tjänsten eller information från externa uppköpare.",
          "Vi kan när som helst ändra, pausa eller avsluta delar av tjänsten, till exempel om en uppköpare ändrar sitt erbjudande eller om tekniska problem uppstår.",
        ],
      },
      {
        heading: "6. Ändringar av villkoren",
        paragraphs: [
          "Vi kan uppdatera dessa villkor vid behov. Den senaste versionen publiceras alltid på denna sida och gäller från det datum som anges längst upp.",
        ],
      },
    ],
  },
  privacy: {
    title: "Integritetspolicy",
    description:
      "Integritetspolicy för Televera.se. Läs hur vi samlar in, använder, delar och skyddar personuppgifter när du använder tjänsten.",
    canonicalPath: "/integritet",
    updated: "9 juni 2026",
    intro:
      "Den här policyn beskriver hur Televera behandlar personuppgifter när du använder vår webbplats och våra formulär.",
    sections: [
      {
        heading: "1. Personuppgiftsansvarig",
        paragraphs: [
          `Televera ansvarar för den behandling av personuppgifter som sker inom vår egen tjänst. Kontakt: ${contactEmail}, ${contactPhone}. Org.nr: ${orgNumber}.`,
          "När du väljer en uppköpare kan uppköparen bli självständigt personuppgiftsansvarig för sin behandling av dina uppgifter, till exempel för att hantera köp, frakt, betalning och kundsupport.",
        ],
      },
      {
        heading: "2. Uppgifter vi behandlar",
        paragraphs: [
          "Vi kan behandla kontaktuppgifter som namn, e-postadress, telefonnummer och adress, uppgifter om den enhet du vill sälja, valt erbjudande, orderinformation och teknisk information från webbplatsen.",
          "Vi ber dig att inte skicka känsliga personuppgifter till oss. Innan du säljer en enhet bör du själv radera personligt innehåll från enheten och logga ut från relevanta konton.",
        ],
      },
      {
        heading: "3. Varför vi behandlar uppgifter",
        paragraphs: [
          "Vi behandlar uppgifter för att kunna visa relevanta värderingar, skapa och förmedla din förfrågan till vald uppköpare, kommunicera med dig, felsöka tjänsten, förebygga missbruk och förbättra användarupplevelsen.",
          "Behandlingen sker främst för att kunna tillhandahålla tjänsten, hantera din begäran, uppfylla rättsliga skyldigheter och för vårt berättigade intresse av att driva och förbättra Televera.",
        ],
      },
      {
        heading: "4. Delning med uppköpare och leverantörer",
        paragraphs: [
          "När du väljer ett erbjudande delar vi de uppgifter som behövs med den uppköpare du har valt. Det kan omfatta kontaktuppgifter, adress, uppgifter om enheten och information om valt erbjudande.",
          "Vi kan även använda tekniska leverantörer för drift, analys, e-post, databaser och säkerhet. Sådana leverantörer får bara behandla uppgifter för de ändamål vi anlitar dem för.",
        ],
      },
      {
        heading: "5. Lagringstid",
        paragraphs: [
          "Vi sparar personuppgifter så länge det behövs för att tillhandahålla tjänsten, hantera ärenden, följa upp förfrågningar, uppfylla bokförings- eller andra lagkrav och skydda våra rättigheter.",
          "Uppgifter som inte längre behövs raderas eller anonymiseras löpande.",
        ],
      },
      {
        heading: "6. Dina rättigheter",
        paragraphs: [
          "Du kan begära tillgång till dina personuppgifter, rättelse av felaktiga uppgifter, radering, begränsning av behandling, dataportabilitet och invända mot viss behandling.",
          `Kontakta oss på ${contactEmail} om du vill använda dina rättigheter. Du har också rätt att lämna klagomål till Integritetsskyddsmyndigheten om du anser att vår behandling är felaktig.`,
        ],
      },
      {
        heading: "7. Säkerhet",
        paragraphs: [
          "Vi arbetar med rimliga tekniska och organisatoriska säkerhetsåtgärder för att skydda uppgifter mot obehörig åtkomst, förlust och missbruk. Ingen digital tjänst kan dock garantera absolut säkerhet.",
        ],
      },
    ],
  },
  cookies: {
    title: "Cookiepolicy",
    description:
      "Cookiepolicy för Televera.se. Läs vilka cookies och liknande tekniker vi använder och hur du kan hantera dem.",
    canonicalPath: "/cookies",
    updated: "9 juni 2026",
    intro:
      "Den här policyn förklarar hur Televera använder cookies och liknande tekniker på webbplatsen.",
    sections: [
      {
        heading: "1. Vad är cookies?",
        paragraphs: [
          "Cookies är små textfiler som sparas i din webbläsare. De kan användas för att webbplatsen ska fungera, komma ihåg val, förstå hur sidan används och förbättra tjänsten.",
          "Liknande tekniker kan också användas, till exempel lokal lagring i webbläsaren.",
        ],
      },
      {
        heading: "2. Cookies vi använder",
        paragraphs: [
          "Nödvändiga cookies och lokal lagring används för grundläggande funktioner, till exempel formulärflöden, sparade val och teknisk drift. Dessa behövs för att tjänsten ska fungera på ett bra sätt.",
          "Analyscookies kan användas för att förstå hur besökare använder webbplatsen, vilka sidor som fungerar bra och var tekniska problem uppstår. Sådan information används på aggregerad nivå för att förbättra Televera.",
          "Om vi använder externa tjänster för exempelvis analys, formulär, hosting eller felrapportering kan dessa leverantörer sätta egna cookies eller behandla teknisk information enligt sina villkor.",
        ],
      },
      {
        heading: "3. Samtycke och inställningar",
        paragraphs: [
          "Cookies som inte är nödvändiga ska bara användas när det finns stöd för det, till exempel genom samtycke. Du kan när som helst rensa eller blockera cookies i din webbläsare.",
          "Om du blockerar vissa cookies kan delar av webbplatsen fungera sämre, till exempel sparade val eller formulärsteg.",
        ],
      },
      {
        heading: "4. Tredjepartstjänster",
        paragraphs: [
          "Televera kan länka vidare till externa uppköpare. När du lämnar Televera gäller den externa webbplatsens egna cookie- och integritetspolicys.",
          "Vi ansvarar inte för hur externa webbplatser använder cookies, men försöker samarbeta med seriösa aktörer.",
        ],
      },
      {
        heading: "5. Uppdateringar",
        paragraphs: [
          "Vi kan uppdatera denna cookiepolicy när webbplatsen eller de tekniska tjänster vi använder förändras. Den senaste versionen finns alltid på denna sida.",
        ],
      },
    ],
  },
};

const PolicyPage = ({ type }: { type: PolicyType }) => {
  const policy = policies[type];

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [type]);

  return (
    <div className="min-h-screen bg-[#f7f5ef] text-[#14181f]">
      <Helmet>
        <title>{policy.title} - Televera.se</title>
        <meta name="description" content={policy.description} />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href={`https://televera.se${policy.canonicalPath}`} />
        <meta property="og:title" content={`${policy.title} - Televera.se`} />
        <meta property="og:description" content={policy.description} />
        <meta property="og:url" content={`https://televera.se${policy.canonicalPath}`} />
      </Helmet>

      <main className="mx-auto max-w-4xl px-5 py-10 md:px-8 md:py-16">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm font-semibold text-[#3d444d] transition-colors hover:text-[#00936a]"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Startsidan
        </Link>

        <header className="mt-10 border-b border-[#e1ddd2] pb-8">
          <h1 className="text-4xl font-extrabold leading-tight md:text-5xl">{policy.title}</h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-[#3d444d]">{policy.intro}</p>
          <p className="mt-5 text-sm text-[#69717c]">Senast uppdaterad: {policy.updated}</p>
        </header>

        <div className="mt-10 space-y-10">
          {policy.sections.map((section) => (
            <section key={section.heading}>
              <h2 className="text-xl font-extrabold">{section.heading}</h2>
              <div className="mt-4 space-y-4 text-base leading-8 text-[#3d444d]">
                {section.paragraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </div>
            </section>
          ))}
        </div>

        <section className="mt-12 border-t border-[#e1ddd2] pt-8">
          <h2 className="text-xl font-extrabold">Kontakt</h2>
          <ul className="mt-4 space-y-3 text-sm text-[#3d444d]">
            <li className="flex items-center gap-3">
              <Mail className="h-4 w-4 text-[#00b87a]" aria-hidden />
              <a href={`mailto:${contactEmail}`} className="transition-colors hover:text-[#00936a]">
                {contactEmail}
              </a>
            </li>
            <li className="flex items-center gap-3">
              <Phone className="h-4 w-4 text-[#00b87a]" aria-hidden />
              <a href="tel:+46702320615" className="transition-colors hover:text-[#00936a]">
                {contactPhone}
              </a>
            </li>
            <li className="flex items-center gap-3">
              <Building2 className="h-4 w-4 text-[#00b87a]" aria-hidden />
              <span>Org.nr: {orgNumber}</span>
            </li>
          </ul>
        </section>
      </main>
    </div>
  );
};

export default PolicyPage;
