import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowRight, BookOpen, Check, Clock3, Search, ShieldCheck } from "lucide-react";
import { articleSummaries } from "@/data/article-summaries";
import televeraMockupHand from "@/assets/televera_mockup_hand.png";

const formatArticleDate = (date: string) =>
  new Intl.DateTimeFormat("sv-SE", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(`${date}T00:00:00`));

const estimateReadingMinutes = (content: string) => {
  const words = content.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(2, Math.ceil(words / 180));
};

const articleThemes = [
  { icon: Search, title: "Prisjämförelse", text: "Förstå varför bud kan skilja sig mellan uppköpare." },
  { icon: ShieldCheck, title: "Trygg försäljning", text: "Radera data, kontrollera skick och undvik överraskningar." },
  { icon: Clock3, title: "Snabba beslut", text: "Korta guider som hjälper innan mobilen skickas iväg." },
];

const ArticlesListPage = () => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const itemListJsonLd = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    itemListElement: articleSummaries.map((a, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: `https://televera.se/artikel/${a.slug}`,
      name: a.title,
    })),
  };
  const featuredArticle = articleSummaries[0];
  const secondaryArticles = articleSummaries.slice(1);

  return (
    <div className="min-h-screen bg-[#f7f5ef] text-[#111111]">
      <Helmet>
        <title>Guider om att sälja mobil | Televera.se</title>
        <meta
          name="description"
          content="Läs våra guider om att sälja begagnade mobiler – allt från värdering och prisskillnader till praktiska tips innan du säljer."
        />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://televera.se/artiklar" />
        <script type="application/ld+json">{JSON.stringify(itemListJsonLd)}</script>
      </Helmet>

      <header className="overflow-hidden bg-[#05B87A] text-white">
        <div className="mx-auto max-w-[1120px] px-5 pt-[68px] sm:px-8 lg:px-10">
          <section className="grid gap-8 pt-8 sm:gap-12 sm:pt-10 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-center">
            <div>
              <h1 className="max-w-[760px] text-balance font-heading text-[38px] font-extrabold leading-[1.07] text-white sm:text-[52px] md:text-[60px]">
                Gör smarta beslut innan du ska sälja
              </h1>
              <p className="mt-5 max-w-[560px] text-base leading-8 text-white/80 sm:text-lg">
                Praktiska artiklar om värdering, trygg försäljning, skickbedömning och vad du bör veta innan du väljer
                ett bud.
              </p>
              <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <Link
                  to="/"
                  className="inline-flex items-center justify-center gap-2 rounded-md bg-white px-[22px] py-[13px] text-sm font-bold text-[#044a30] shadow-[0_2px_12px_rgba(0,0,0,0.12)] transition hover:bg-[#f7f5ef]"
                >
                  Värdera din iPhone
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </Link>
                <a
                  href="#artiklar"
                  className="inline-flex items-center justify-center gap-2 rounded-md border-[1.5px] border-white/35 bg-black/10 px-[22px] py-[13px] text-sm font-bold text-white transition hover:bg-black/15"
                >
                  Bläddra guider
                </a>
              </div>
            </div>

            <div className="h-[288px] overflow-hidden self-end justify-self-center sm:h-[342px] lg:h-[414px] lg:justify-self-end">
              <img
                src={televeraMockupHand}
                alt="Televera på mobil"
                className="block h-[320px] w-auto max-w-none sm:h-[380px] lg:h-[460px]"
              />
            </div>
          </section>
        </div>
      </header>

      <section className="bg-[#f7f5ef] py-12 pb-5">
        <div className="mx-auto max-w-[1120px] px-5 sm:px-8 lg:px-10">
          <div className="relative grid gap-6 md:grid-cols-3">
            <div
              className="absolute left-[16%] right-[16%] top-[56px] z-0 hidden h-0.5 opacity-40 md:block [background-image:linear-gradient(90deg,#00b87a_55%,transparent_55%)] [background-size:14px_2px]"
              aria-hidden
            />
            {articleThemes.map((item, index) => (
              <article
                key={item.title}
                className="relative z-10 rounded-[18px] border-[1.5px] border-[#e7e3d8] bg-[#fffdf8] px-[26px] py-[30px] shadow-[0_1px_2px_rgba(20,24,31,0.04),0_2px_8px_rgba(20,24,31,0.05)] transition hover:-translate-y-1 hover:-rotate-[0.6deg] hover:shadow-[0_6px_20px_rgba(20,24,31,0.08),0_2px_6px_rgba(20,24,31,0.05)]"
              >
                <span className="mb-5 flex h-[52px] w-[52px] items-center justify-center rounded-full bg-[#00b87a] font-heading text-[22px] font-extrabold text-white shadow-[0_0_0_6px_#fffdf8,0_0_0_7.5px_#e7f7ef]">
                  {index + 1}
                </span>
                <item.icon
                  className="absolute right-[26px] top-8 h-6 w-6 text-[#00b87a] opacity-85"
                  strokeWidth={2.4}
                  aria-hidden
                />
                <h2 className="font-heading text-xl font-extrabold leading-tight text-[#14181f]">{item.title}</h2>
                <p className="mt-2 text-[15.5px] leading-[1.55] text-[#5b626d]">{item.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <main id="artiklar" className="mx-auto max-w-[1120px] px-5 pt-3.5 sm:px-8 lg:px-10">
        <section>
          <div className="mb-7 flex flex-wrap items-center gap-x-8 gap-y-3 rounded-xl border border-[rgba(255,210,63,0.45)] bg-[#fefcf0] px-[22px] py-4">
            {[
              `${articleSummaries.length} publicerade guider`,
              "Svensk jämförelsetjänst",
              "Uppdateras löpande",
		"Hjälp- och trygghetsguider",
            ].map((fact) => (
              <div key={fact} className="flex items-baseline gap-2 text-sm leading-6 text-[#333333]">
                <Check className="h-[15px] w-[15px] shrink-0 text-[#05B87A]" strokeWidth={2.5} aria-hidden />
                <span>{fact}</span>
              </div>
            ))}
          </div>

          <div className="grid gap-6 rounded-[18px] bg-white p-5 shadow-[0_4px_40px_rgba(0,0,0,0.07),0_1px_4px_rgba(0,0,0,0.04)] sm:p-8 lg:grid-cols-[minmax(0,1.08fr)_minmax(280px,0.92fr)]">
            {featuredArticle ? (
              <Link
                to={`/artikel/${featuredArticle.slug}`}
                className="group flex min-h-[360px] flex-col justify-between rounded-xl border border-[#edeae4] bg-[#fbfaf6] p-6 transition hover:border-[#05B87A]/50 hover:bg-white sm:p-8"
              >
                <div>
                  <div className="mb-[22px] inline-flex items-center gap-2 rounded-md bg-[#e7f7ef] px-3 py-[7px] text-[13px] font-bold text-[#007f5d]">
                    <BookOpen className="h-4 w-4" aria-hidden />
                    Senaste guiden
                  </div>
                  <h2 className="max-w-[540px] text-balance font-heading text-[24px] font-extrabold leading-[1.2] text-[#111111] transition group-hover:text-[#05B87A] sm:text-[34px]">
                    {featuredArticle.title}
                  </h2>
                  <p className="mt-3.5 max-w-[520px] text-base leading-[1.7] text-[#444444]">{featuredArticle.ingress}</p>
                </div>
                <div className="mt-8 flex flex-wrap items-center gap-x-2.5 gap-y-2 text-sm text-[#888888]">
                  <span>{formatArticleDate(featuredArticle.datePublished)}</span>
                  <span aria-hidden>·</span>
                  <span>{estimateReadingMinutes(featuredArticle.content)} min läsning</span>
                  <span className="ml-auto inline-flex items-center gap-1.5 font-bold text-[#05B87A]">
                    Läs guiden
                    <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" aria-hidden />
                  </span>
                </div>
              </Link>
            ) : null}

            <div className="grid gap-4">
              {secondaryArticles.map((article) => (
                <Link
                  key={article.slug}
                  to={`/artikel/${article.slug}`}
                  className="group rounded-[10px] border border-[#edeae4] bg-white p-5 transition hover:border-[#05B87A]/50 hover:bg-[#fbfaf6]"
                >
                  <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.06em] text-[#bbbbbb]">
                    <BookOpen className="h-3.5 w-3.5" aria-hidden />
                    Guide
                  </div>
                  <h2 className="mt-2.5 text-balance font-heading text-[17px] font-bold leading-[1.35] text-[#111111] transition group-hover:text-[#05B87A]">
                    {article.title}
                  </h2>
                  <p className="mt-2 text-sm leading-[1.6] text-[#555555]">{article.ingress}</p>
                  <div className="mt-3.5 flex flex-wrap items-center gap-x-2 gap-y-2 text-xs font-semibold text-[#999999]">
                    <span>{formatArticleDate(article.datePublished)}</span>
                    <span aria-hidden>·</span>
                    <span>{estimateReadingMinutes(article.content)} min</span>
                    <span className="ml-auto inline-flex items-center gap-1 text-[13px] text-[#05B87A]">
                      Läs mer
                      <ArrowRight className="h-3.5 w-3.5 transition group-hover:translate-x-1" aria-hidden />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-[calc(50%-50vw)] bg-[#111111] px-5 py-[72px] text-center text-white sm:px-10">
          <h2 className="mx-auto max-w-[560px] font-heading text-2xl font-bold leading-tight sm:text-3xl">
            Redo att se vad din telefon kan vara värd?
          </h2>
          <p className="mx-auto mt-3.5 max-w-[460px] text-[15px] leading-[1.7] text-white/50">
            Artiklarna hjälper dig förstå marknaden. Värderingen visar vad flera uppköpare erbjuder just nu.
          </p>
          <Link
            to="/"
            className="mt-8 inline-flex items-center justify-center gap-2 rounded-md bg-[#05B87A] px-[26px] py-3.5 text-[15px] font-bold text-white transition hover:bg-[#009f69]"
          >
            Jämför priser gratis
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </section>
      </main>
    </div>
  );
};

export default ArticlesListPage;
