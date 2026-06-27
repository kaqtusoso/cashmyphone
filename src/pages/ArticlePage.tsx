import { useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft, ArrowRight, BookOpen, Check, Sparkles } from "lucide-react";
import ArticleHeroIllustration from "@/components/ArticleHeroIllustration";
import { articleSummaries } from "@/data/article-summaries";

const estimateReadingMinutes = (content: string) => {
  const words = content.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(2, Math.ceil(words / 180));
};

const formatArticleDate = (date: string) =>
  new Intl.DateTimeFormat("sv-SE", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(`${date}T00:00:00`));

const ArticlePage = () => {
  const { slug } = useParams<{ slug: string }>();
  const article = articleSummaries.find((a) => a.slug === slug);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  if (!article) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f7f5ef] px-4">
        <div className="max-w-sm text-center">
          <h1 className="text-2xl font-heading font-bold text-[#111111]">Artikeln hittades inte.</h1>
          <Link to="/artiklar" className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-primary">
            <ArrowLeft className="h-4 w-4" aria-hidden />
            Tillbaka till artiklar
          </Link>
        </div>
      </div>
    );
  }

  const url = `https://televera.se/artikel/${article.slug}`;
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.ingress,
    url,
    datePublished: article.datePublished,
    dateModified: article.dateModified,
    publisher: {
      "@type": "Organization",
      name: "Televera",
      url: "https://televera.se",
    },
  };
  const readingMinutes = estimateReadingMinutes(article.content);
  const publishedLabel = formatArticleDate(article.datePublished);
  const modifiedLabel = formatArticleDate(article.dateModified);

  return (
    <div className="min-h-screen bg-[#f7f5ef] text-[#111111]">
      <Helmet>
        <title>{article.title} | Televera.se</title>
        <meta name="description" content={article.ingress} />
        <meta property="og:title" content={`${article.title} | Televera.se`} />
        <meta property="og:description" content={article.ingress} />
        <meta property="og:url" content={url} />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href={url} />
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>

      <header className="bg-[#05B87A] text-white">
        <div className="mx-auto max-w-[1120px] px-5 pt-[68px] sm:px-8 lg:px-10">
          <Link
            to="/artiklar"
            className="inline-flex items-center gap-1.5 pt-6 text-sm font-semibold text-white/60 transition hover:text-white"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden />
            Alla guider
          </Link>

          <div className="grid gap-10 py-11 pb-[68px] lg:grid-cols-[minmax(0,620px)_360px] lg:items-center lg:justify-between">
            <div>
              <h1 className="max-w-[620px] text-balance font-heading text-[32px] font-extrabold leading-[1.09] text-white sm:text-[46px] md:text-[54px]">
                {article.title}
              </h1>
              <p className="mt-5 max-w-[560px] text-base leading-8 text-white/80 sm:text-lg">
                {article.ingress}
              </p>
              <div className="mt-6 flex flex-wrap items-center gap-x-2.5 gap-y-2 text-sm text-white/55">
                <span>Publicerad {publishedLabel}</span>
                <span className="hidden sm:inline" aria-hidden>
                  ·
                </span>
                <span>Uppdaterad {modifiedLabel}</span>
                <span className="hidden sm:inline" aria-hidden>
                  ·
                </span>
                <span>{readingMinutes} min läsning</span>
              </div>
              <Link
                to="/"
                className="mt-8 inline-flex items-center justify-center gap-2 rounded-md bg-white px-[22px] py-[13px] text-sm font-bold text-[#044a30] shadow-[0_2px_12px_rgba(0,0,0,0.12)] transition hover:bg-[#f7f5ef]"
              >
                Jämför priser nu
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </div>
            <ArticleHeroIllustration slug={article.slug} />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[940px] px-5 pb-[60px] pt-7 sm:px-8 lg:px-10">
        <div className="mx-auto overflow-hidden rounded-[18px] bg-white shadow-[0_4px_40px_rgba(0,0,0,0.07),0_1px_4px_rgba(0,0,0,0.04)]">
          <div className="px-5 pt-6 sm:px-10">
            <nav className="flex flex-wrap items-center gap-1.5 text-[13px]" aria-label="Brödsmulor">
              <Link to="/" className="text-[#aaaaaa] transition hover:text-[#111111]">
                Hem
              </Link>
              <span className="text-[#dddddd]" aria-hidden>
                ›
              </span>
              <Link to="/artiklar" className="text-[#aaaaaa] transition hover:text-[#111111]">
                Guider
              </Link>
              <span className="text-[#dddddd]" aria-hidden>
                ›
              </span>
              <span className="max-w-full truncate text-[#666666]">{article.title}</span>
            </nav>

            <section className="mt-5 rounded-xl border border-[rgba(255,210,63,0.45)] bg-[#fefcf0] px-[22px] py-[18px]">
              <div className="mb-3 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-[0.08em] text-[#a07800]">
                <Sparkles className="h-3.5 w-3.5" strokeWidth={2.5} aria-hidden />
                Snabbfakta
              </div>
              <div className="grid gap-2 text-sm leading-6 text-[#333333] sm:grid-cols-3">
                {[
                  `${readingMinutes} min läsning`,
                  "Gratis att jämföra",
                  "Flera svenska uppköpare",
                ].map((fact) => (
                  <div key={fact} className="flex items-baseline gap-2">
                    <Check className="h-3.5 w-3.5 shrink-0 text-[#05B87A]" strokeWidth={2.5} aria-hidden />
                    <span>{fact}</span>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <article
            className="prose prose-neutral max-w-none px-5 py-9 sm:px-10 sm:pb-8
              prose-headings:font-heading prose-headings:text-[#111111]
              prose-h2:mb-3 prose-h2:mt-9 prose-h2:text-[22px] prose-h2:font-bold prose-h2:leading-[1.3]
              prose-h3:mb-3 prose-h3:mt-8 prose-h3:text-xl prose-h3:font-semibold
              prose-p:my-0 prose-p:mb-[22px] prose-p:text-[16px] prose-p:leading-[1.8] prose-p:text-[#444444]
              prose-p:first-of-type:text-lg prose-p:first-of-type:font-medium prose-p:first-of-type:leading-[1.8] prose-p:first-of-type:text-[#222222]
              prose-strong:text-[#111111]
              prose-a:font-semibold prose-a:text-[#05B87A] prose-a:no-underline hover:prose-a:underline
              prose-ul:my-[22px] prose-ul:pl-[22px] prose-li:my-2.5 prose-li:text-[#444444] prose-li:marker:text-[#05B87A]
              prose-ol:my-[22px] prose-li:marker:font-bold prose-li:marker:text-[#05B87A]
              prose-blockquote:my-7 prose-blockquote:rounded-r-lg prose-blockquote:border-l-[3px] prose-blockquote:border-[#ffd23f] prose-blockquote:bg-[#fefcf0] prose-blockquote:px-5 prose-blockquote:py-4 prose-blockquote:font-semibold prose-blockquote:text-[#333333]
              prose-hr:border-[#edeae4]
              prose-table:text-sm prose-th:bg-[#f7f5ef] prose-th:text-[#666666] prose-td:text-[#444444]"
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{article.content}</ReactMarkdown>
          </article>

          <section className="mx-5 mb-9 grid gap-6 rounded-[14px] bg-[#05B87A] p-6 text-white sm:mx-10 sm:grid-cols-[1fr_auto] sm:items-center sm:p-7 lg:px-8">
            <div>
              <h2 className="font-heading text-xl font-bold leading-tight">Sätt ett pris på din telefon</h2>
              <p className="mt-2 text-sm leading-[1.65] text-white/80">
                Jämför vad uppköpare erbjuder just nu. Du väljer själv om du vill gå vidare.
              </p>
            </div>
            <Link
              to="/"
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-white px-5 py-3 text-sm font-bold text-[#044a30] transition hover:bg-[#f7f5ef]"
            >
              Jämför nu
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          </section>

          <footer className="bg-[#111111] px-5 py-[52px] text-center text-white sm:px-10">
            <BookOpen className="mx-auto h-6 w-6 text-[#05B87A]" strokeWidth={2.5} aria-hidden />
            <h2 className="mx-auto mt-4 max-w-[420px] font-heading text-2xl font-extrabold leading-[1.3] sm:text-[26px]">Fler guider innan du säljer</h2>
            <p className="mx-auto mt-3 max-w-[400px] text-sm leading-[1.7] text-white/50">
              Läs mer om värdering, skick och vad som kan påverka budet innan du skickar iväg mobilen.
            </p>
            <Link
              to="/artiklar"
              className="mt-7 inline-flex items-center justify-center gap-2 rounded-md bg-[#05B87A] px-6 py-[13px] text-sm font-bold text-white transition hover:bg-[#009f69]"
            >
              Visa alla artiklar
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          </footer>
        </div>
      </main>
    </div>
  );
};

export default ArticlePage;
