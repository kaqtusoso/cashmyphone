import { useState } from "react";
import { ArrowRight, Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface AISummaryProps {
  fullSummary: string[];
  onCtaClick: () => void;
}

const AISummary = ({ fullSummary, onCtaClick }: AISummaryProps) => {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="bg-violet-50 border border-violet-200 rounded-xl p-3">
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="w-4 h-4 text-violet-600" />
        <span className="text-sm font-semibold text-violet-700">AI-sammanfattning</span>
      </div>
      
      <div 
        className={`relative overflow-hidden transition-all duration-300 ease-out ${
          isExpanded ? 'max-h-[1000px]' : 'max-h-24'
        }`}
      >
        <ul className="text-sm text-violet-900/80 mb-3 space-y-1.5 list-disc list-inside">
          {fullSummary.map((point, index) => (
            <li key={index}>{point}</li>
          ))}
        </ul>
        <div 
          className={`absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-violet-50 to-transparent pointer-events-none transition-opacity duration-300 ${
            isExpanded ? 'opacity-0' : 'opacity-100'
          }`} 
        />
      </div>
      
      <div className={`transition-all duration-300 ease-out ${isExpanded ? 'opacity-100' : 'opacity-100'}`}>
        {!isExpanded ? (
          <button
            onClick={() => setIsExpanded(true)}
            className="text-sm text-violet-600 hover:text-violet-800 font-medium flex items-center gap-1 transition-colors"
          >
            Visa hela sammanfattningen
            <ChevronDown className="w-4 h-4 transition-transform duration-300" />
          </button>
        ) : (
          <button
            onClick={onCtaClick}
            className="bg-violet-600 hover:bg-violet-700 text-white font-semibold py-2 px-5 rounded-lg inline-flex items-center gap-2 border-2 border-violet-700 shadow-[3px_3px_0px_rgba(109,40,217,0.4)] hover:shadow-[1px_1px_0px_rgba(109,40,217,0.4)] hover:translate-x-[2px] hover:translate-y-[2px] transition-all duration-200 text-sm"
          >
            Gör en gratis värdering
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

interface BlogCardProps {
  title: string;
  subtitle?: string;
  excerpt: string;
  content: (onCtaClick: () => void) => React.ReactNode;
  icon?: string;
  fullSummary: string[];
}

const BlogCard = ({ title, subtitle, excerpt, content, icon = "📱", fullSummary }: BlogCardProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleCtaClick = () => {
    setIsOpen(false);
    setTimeout(() => {
      const valuationSection = document.getElementById('valuation');
      if (valuationSection) {
        valuationSection.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);
  };

  return (
    <>
      <article className="bg-white rounded-2xl border-2 border-[#00B87A] shadow-[4px_4px_0px_rgba(0,184,122,1)] p-6 pb-4 flex flex-col h-full hover:shadow-[2px_2px_0px_rgba(0,184,122,1)] hover:translate-x-[2px] hover:translate-y-[2px] transition-all duration-200 relative overflow-hidden">
        <h3 className="text-lg font-bold text-foreground mb-3 line-clamp-2">
          {icon} {title}
        </h3>
        
        <div className="relative flex-grow mb-8">
          <p className="text-muted-foreground text-sm line-clamp-3">
            {excerpt}
          </p>
          <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-white to-transparent pointer-events-none" />
        </div>
        
        <button
          onClick={() => setIsOpen(true)}
          className="absolute bottom-0 right-0 w-1/2 bg-[#00B87A] hover:bg-[#00a06b] text-white font-semibold py-2.5 px-4 rounded-tl-xl flex items-center justify-center gap-2 transition-colors duration-200"
        >
          Läs mer
          <ArrowRight className="w-4 h-4" />
        </button>
      </article>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl md:text-3xl font-bold text-foreground">
              {icon} {title}
            </DialogTitle>
            {subtitle && (
              <p className="text-lg text-muted-foreground italic">{subtitle}</p>
            )}
          </DialogHeader>
          
          <AISummary 
            fullSummary={fullSummary} 
            onCtaClick={handleCtaClick} 
          />
          
          <div className="prose prose-lg max-w-none text-foreground/90">
            {content(handleCtaClick)}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default BlogCard;
