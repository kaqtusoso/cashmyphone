import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { ArrowLeft } from "lucide-react";
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
      url: `https://cashmyphone.se/artikel/${a.slug}`,
      name: a.title,
    })),
  };

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>Guider om att sälja mobil | CashMyPhone.se</title>
        <meta
          name="description"
          content="Läs våra guider om att sälja begagnade mobiler – allt från värdering och prisskillnader till praktiska tips innan du säljer."
        />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://cashmyphone.se/artiklar" />
        <script type="application/ld+json">{JSON.stringify(itemListJsonLd)}</script>
      </Helmet>

      <div className="max-w-5xl mx-auto px-4 pt-4 pb-10 md:pt-6 md:pb-16">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Tillbaka
        </Link>

        <h1 className="text-3xl md:text-4xl font-heading font-bold text-foreground leading-tight mb-6">
          Guider om att sälja mobil
        </h1>

        <div className="grid md:grid-cols-2 gap-6">
          {articleSummaries.map((article) => (
            <Link
              key={article.slug}
              to={`/artikel/${article.slug}`}
              className="bg-card border border-border rounded-2xl p-6 hover:border-primary/40 transition-all duration-150 group"
            >
              <h2 className="text-lg font-heading font-semibold text-foreground group-hover:text-primary transition-colors">
                {article.title}
              </h2>
              <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{article.ingress}</p>
              <span className="inline-block mt-4 text-sm font-medium text-primary">Läs mer →</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ArticlesListPage;
