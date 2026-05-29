import { useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft } from "lucide-react";
import { articleSummaries } from "@/data/article-summaries";

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

  const url = `https://cashmyphone.se/artikel/${article.slug}`;
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: article.title,
    description: article.ingress,
    url,
    publisher: {
      "@type": "Organization",
      name: "CashMyPhone",
      url: "https://cashmyphone.se",
    },
  };

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>{article.title} | CashMyPhone.se</title>
        <meta name="description" content={article.ingress} />
        <meta property="og:title" content={`${article.title} | CashMyPhone.se`} />
        <meta property="og:description" content={article.ingress} />
        <meta property="og:url" content={url} />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href={url} />
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>

      <div className="max-w-[700px] mx-auto px-4 pt-4 pb-10 md:pt-6 md:pb-16">
        <Link
          to="/artiklar"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka
        </Link>

        <h1 className="text-3xl md:text-4xl font-heading font-bold text-foreground leading-tight mb-6">
          {article.title}
        </h1>

        <article
          className="prose prose-neutral dark:prose-invert max-w-none
            prose-headings:font-heading prose-headings:text-foreground
            prose-h2:text-xl prose-h2:md:text-2xl prose-h2:mt-10 prose-h2:mb-4
            prose-h3:text-lg prose-h3:mt-8 prose-h3:mb-3
            prose-p:text-muted-foreground prose-p:leading-relaxed
            prose-strong:text-foreground
            prose-li:text-muted-foreground
            prose-blockquote:border-primary prose-blockquote:text-foreground prose-blockquote:font-medium
            prose-hr:border-border
            prose-a:text-primary"
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{article.content}</ReactMarkdown>
        </article>

        <div className="mt-16 bg-card border border-border rounded-2xl p-8 text-center">
          <h2 className="text-xl md:text-2xl font-heading font-bold text-foreground">
            Redo att värdera din mobil?
          </h2>
          <p className="text-muted-foreground mt-2">
            Använd vår tjänst för att jämföra priser från flera uppköpare på 30 sekunder.
          </p>
          <Link
            to="/"
            className="inline-block mt-5 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-xl hover:opacity-90 transition-all"
          >
            Värdera nu →
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ArticlePage;
