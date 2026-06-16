import { useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft, ArrowRight, BookOpen, Clock3, Sparkles } from "lucide-react";
import { articleSummaries } from "@/data/article-summaries";

const estimateReadingMinutes = (content: string) => {
  const words = content.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(2, Math.ceil(words / 180));
};

const ArticlePage = () => {
  const { slug } = useParams<{ slug: string }>();
  const article = articleSummaries.find((a) => a.slug === slug);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  if (!article) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-heading font-bold text-foreground">Artikeln hittades inte.</h1>
          <Link to="/artiklar" className="text-primary mt-4 inline-block">
            ← Tillbaka till artiklar
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
    publisher: {
      "@type": "Organization",
      name: "Televera",
      url: "https://televera.se",
    },
  };
  const readingMinutes = estimateReadingMinutes(article.content);

  return (
    <div className="min-h-screen bg-[#fbfdfb] text-foreground">
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

      <div className="mx-auto max-w-5xl px-4 pb-12 pt-4 md:px-6 md:pb-20 md:pt-6">
        <Link
          to="/artiklar"
          className="mb-8 inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka till artiklar
        </Link>

        <header className="grid gap-7 border-b border-[#dfe9e3] pb-9 lg:grid-cols-[minmax(0,1fr)_280px] lg:items-end">
          <div>
            <div className="mb-4 flex flex-wrap items-center gap-2 text-sm">
              <span className="inline-flex items-center gap-2 rounded-full border border-[#bfe8d6] bg-white px-3 py-1.5 font-bold text-[#007f5d] shadow-sm">
                <BookOpen className="h-4 w-4" aria-hidden />
                Guide
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border border-[#dfe9e3] bg-white px-3 py-1.5 font-semibold text-[#62706b]">
                <Clock3 className="h-4 w-4 text-primary" aria-hidden />
                {readingMinutes} min läsning
              </span>
            </div>
            <h1 className="max-w-3xl text-4xl font-extrabold leading-[1.06] tracking-normal text-[#11181f] md:text-6xl">
              {article.title}
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-[#52605b] md:text-xl">{article.ingress}</p>
          </div>

          <aside className="rounded-lg border border-[#d9e7df] bg-white p-5 shadow-sm">
            <div className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-[#e7f7ef] text-primary">
              <Sparkles className="h-4 w-4" aria-hidden />
            </div>
            <h2 className="mt-4 text-base font-extrabold text-[#11181f]">I korthet</h2>
            <p className="mt-2 text-sm leading-6 text-[#52605b]">{article.ingress}</p>
          </aside>
        </header>

        <div className="mx-auto mt-10 grid max-w-4xl gap-8 lg:grid-cols-[minmax(0,700px)_1fr]">
          <article
            className="prose prose-neutral dark:prose-invert max-w-none
              rounded-lg border border-[#d9e7df] bg-white px-5 py-7 shadow-sm md:px-9 md:py-10
              prose-headings:font-heading prose-headings:text-[#11181f]
              prose-h2:border-t prose-h2:border-[#e7eee9] prose-h2:pt-8
              prose-h2:text-2xl prose-h2:font-extrabold prose-h2:leading-tight prose-h2:mt-10 prose-h2:mb-4
              prose-h3:text-lg prose-h3:font-extrabold prose-h3:mt-8 prose-h3:mb-3
              prose-p:text-[#3d4642] prose-p:text-[1.03rem] prose-p:leading-8
              prose-strong:text-[#11181f]
              prose-ul:my-6 prose-li:my-2 prose-li:text-[#3d4642] prose-li:marker:text-primary
              prose-blockquote:rounded-lg prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:bg-[#e7f7ef] prose-blockquote:px-5 prose-blockquote:py-3 prose-blockquote:text-[#11181f] prose-blockquote:font-semibold
              prose-hr:border-[#dfe9e3]
              prose-a:font-semibold prose-a:text-primary"
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{article.content}</ReactMarkdown>
          </article>

          <aside className="hidden lg:block">
            <div className="sticky top-24 rounded-lg border border-[#d9e7df] bg-[#101820] p-5 text-white shadow-sm">
              <p className="text-sm font-bold text-white/70">Nästa steg</p>
              <h2 className="mt-2 text-xl font-extrabold leading-tight">Se vad din iPhone är värd just nu.</h2>
              <p className="mt-3 text-sm leading-6 text-white/72">
                Jämför flera bud på samma ställe och välj i lugn och ro.
              </p>
              <Link
                to="/"
                className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-primary-foreground transition hover:bg-[#00a06b]"
              >
                Starta värdering
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </div>
          </aside>
        </div>

        <section className="mx-auto mt-10 grid max-w-4xl gap-5 rounded-lg border border-[#d9e7df] bg-[#101820] p-6 text-white md:grid-cols-[1fr_auto] md:items-center md:p-8 lg:hidden">
          <div>
            <h2 className="text-2xl font-extrabold leading-tight">Vill du jämföra bud på din mobil?</h2>
            <p className="mt-3 text-sm leading-6 text-white/72">
              Televera samlar flera uppköpare så du kan se vad din iPhone är värd utan att hoppa mellan sajter.
            </p>
          </div>
          <Link
            to="/"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-primary-foreground transition hover:bg-[#00a06b]"
          >
            Starta värdering
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </section>
      </div>
    </div>
  );
};

export default ArticlePage;
