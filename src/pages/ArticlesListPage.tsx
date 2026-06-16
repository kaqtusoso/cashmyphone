import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowLeft, ArrowRight, BookOpen, Clock3, Search, ShieldCheck, Sparkles } from "lucide-react";
import { articleSummaries } from "@/data/article-summaries";

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
    <div className="min-h-screen bg-[#fbfdfb] text-foreground">
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

      <div className="mx-auto max-w-6xl px-4 pb-14 pt-4 md:px-6 md:pb-20 md:pt-6">
        <Link
          to="/"
          className="mb-8 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka
        </Link>

        <section className="grid gap-8 border-b border-[#dfe9e3] pb-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#bfe8d6] bg-white px-3 py-1.5 text-sm font-semibold text-[#007f5d] shadow-sm">
              <Sparkles className="h-4 w-4" />
              Televera guider
            </div>
            <h1 className="max-w-3xl text-4xl font-extrabold leading-[1.05] tracking-normal text-[#11181f] md:text-6xl">
              Smartare beslut när du ska sälja din iPhone.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-[#52605b] md:text-lg">
              Praktiska guider om värdering, trygg försäljning, skickbedömning och hur du får ut mer av en telefon som
              annars riskerar att bli kvar i lådan.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link
                to="/"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground shadow-[0_10px_28px_rgba(0,184,122,0.22)] transition hover:bg-[#009f69]"
              >
                Värdera din iPhone
                <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#artiklar"
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-[#cfe2d8] bg-white px-5 py-3 text-sm font-bold text-[#16211d] transition hover:border-primary/50"
              >
                Bläddra guider
              </a>
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
            {[
              { icon: Search, title: "Prisjämförelse", text: "Förstå varför bud skiljer sig mellan uppköpare." },
              { icon: ShieldCheck, title: "Trygg försäljning", text: "Radera data, välj betalning och undvik krångel." },
              { icon: Clock3, title: "Snabba beslut", text: "Korta guider som hjälper innan du skickar iväg mobilen." },
            ].map((item) => (
              <div key={item.title} className="rounded-lg border border-[#dfe9e3] bg-white p-4 shadow-sm">
                <item.icon className="h-5 w-5 text-primary" />
                <h2 className="mt-3 text-sm font-bold text-[#11181f]">{item.title}</h2>
                <p className="mt-1 text-sm leading-6 text-[#62706b]">{item.text}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="artiklar" className="grid gap-6 py-10 lg:grid-cols-[1.15fr_0.85fr]">
          {featuredArticle && (
            <Link
              to={`/artikel/${featuredArticle.slug}`}
              className="group flex min-h-[320px] flex-col justify-between rounded-lg border border-[#d9e7df] bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-[0_18px_45px_rgba(17,24,31,0.08)] md:p-8"
            >
              <div>
                <div className="mb-5 inline-flex items-center gap-2 rounded-full bg-[#e7f7ef] px-3 py-1.5 text-sm font-bold text-[#007f5d]">
                  <BookOpen className="h-4 w-4" />
                  Rekommenderad guide
                </div>
                <h2 className="max-w-2xl text-3xl font-extrabold leading-tight text-[#11181f] transition group-hover:text-primary md:text-4xl">
                  {featuredArticle.title}
                </h2>
                <p className="mt-4 max-w-2xl text-base leading-7 text-[#52605b]">{featuredArticle.ingress}</p>
              </div>
              <span className="mt-8 inline-flex items-center gap-2 text-sm font-bold text-primary">
                Läs guiden
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
              </span>
            </Link>
          )}

          <div className="grid gap-4">
            {secondaryArticles.map((article) => (
              <Link
                key={article.slug}
                to={`/artikel/${article.slug}`}
                className="group rounded-lg border border-[#d9e7df] bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-[0_14px_36px_rgba(17,24,31,0.07)]"
              >
                <h2 className="text-xl font-extrabold leading-tight text-[#11181f] transition group-hover:text-primary">
                  {article.title}
                </h2>
                <p className="mt-3 text-sm leading-6 text-[#52605b]">{article.ingress}</p>
                <span className="mt-4 inline-flex items-center gap-2 text-sm font-bold text-primary">
                  Läs mer
                  <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
                </span>
              </Link>
            ))}
          </div>
        </section>

        <section className="grid gap-6 rounded-lg border border-[#d9e7df] bg-[#101820] p-6 text-white md:grid-cols-[1fr_auto] md:items-center md:p-8">
          <div>
            <h2 className="text-2xl font-extrabold leading-tight md:text-3xl">Vill du veta vad din iPhone är värd?</h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/72">
              Artiklarna hjälper dig förstå marknaden. Värderingen visar vad uppköpare faktiskt betalar just nu.
            </p>
          </div>
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground transition hover:bg-[#00a06b]"
          >
            Starta värdering
            <ArrowRight className="h-4 w-4" />
          </Link>
        </section>
      </div>
    </div>
  );
};

export default ArticlesListPage;
