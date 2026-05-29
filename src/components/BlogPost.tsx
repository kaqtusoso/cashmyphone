import { Calendar } from "lucide-react";

interface BlogPostProps {
  title: string;
  subtitle?: string;
  content: React.ReactNode;
  date: string;
}

const BlogPost = ({ title, subtitle, content, date }: BlogPostProps) => {
  return (
    <article className="bg-white rounded-2xl shadow-lg p-8 md:p-12">
      <header className="mb-8">
        <div className="flex items-center gap-2 text-muted-foreground text-sm mb-4">
          <Calendar className="w-4 h-4" />
          <time>{date}</time>
        </div>
        <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-2">
          {title}
        </h2>
        {subtitle && (
          <p className="text-lg text-muted-foreground italic">{subtitle}</p>
        )}
      </header>
      <div className="prose prose-lg max-w-none text-foreground/90">
        {content}
      </div>
    </article>
  );
};

export default BlogPost;
