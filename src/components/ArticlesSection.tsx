import { Link } from "react-router-dom";
import { articleSummaries as articles } from "@/data/article-summaries";

const PREVIEW_COUNT = 4;

const ArticlesSection = () => (
  <section className="py-16 px-4 md:px-6 bg-background">
    <div className="max-w-5xl mx-auto">
      <h2 className="text-2xl md:text-3xl font-heading font-bold text-foreground text-center mb-8">
        Tips & insikter om begagnade mobiler
      </h2>
      <div className="grid md:grid-cols-2 gap-6">
        {articles.slice(0, PREVIEW_COUNT).map((article) => (
          <Link
            key={article.slug}
            to={`/artikel/${article.slug}`}
            className="bg-card border border-border rounded-2xl p-6 hover:border-primary/40 transition-all duration-150 group"
          >
            <h3 className="text-lg font-heading font-semibold text-foreground group-hover:text-primary transition-colors">
              {article.title}
            </h3>
            <p
              className="text-sm text-muted-foreground mt-2 leading-relaxed line-clamp-3"
              style={{
                WebkitMaskImage:
                  "linear-gradient(to bottom, hsl(var(--foreground)) 40%, transparent 100%)",
                maskImage:
                  "linear-gradient(to bottom, hsl(var(--foreground)) 40%, transparent 100%)",
              }}
            >
              {article.ingress}
            </p>
            <span className="inline-block mt-4 text-sm font-medium text-primary">Läs mer →</span>
          </Link>
        ))}
      </div>
      <div className="flex justify-center mt-8">
        <Link
          to="/artiklar"
          className="inline-block px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-xl hover:opacity-90 transition-all"
        >
          Visa alla guider →
        </Link>
      </div>
    </div>
  </section>
);

export default ArticlesSection;
