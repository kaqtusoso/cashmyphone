import { Suspense, useLayoutEffect, useRef, useState } from "react";
import { Helmet } from "react-helmet-async";

import UnifiedFlow from "@/components/UnifiedFlow";
import LogoCarousel from "@/components/LogoCarousel";
import HowItWorks from "@/components/HowItWorks";
import FAQSection from "@/components/FAQSection";
import ArticlesSection from "@/components/ArticlesSection";

const HOME_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "CashMyPhone",
  description: "Jämför vad svenska uppköpare betalar för din begagnade mobil – snabbt, tryggt och gratis.",
  url: "https://cashmyphone.se",
  applicationCategory: "FinanceApplication",
};

const Index = () => {
  const [flowActive, setFlowActive] = useState(false);
  const hasStartedFlow = useRef(false);

  useLayoutEffect(() => {
    if (!flowActive && hasStartedFlow.current) {
      window.scrollTo({ top: 0, behavior: "auto" });
    }
  }, [flowActive]);

  const handleFlowActiveChange = (active: boolean) => {
    if (active) {
      hasStartedFlow.current = true;
    }

    setFlowActive(active);
  };

  return (
    <div className="bg-background flex flex-col">
      <Helmet>
        <title>CashMyPhone – Jämför priser på din begagnade mobil</title>
        <meta
          name="description"
          content="Jämför vad svenska uppköpare betalar för din iPhone – uppdaterat löpande. Ange modell och skick och se vem som betalar mest."
        />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://cashmyphone.se" />
        <meta property="og:title" content="CashMyPhone – Jämför priser på din begagnade mobil" />
        <meta property="og:description" content="Se vem som betalar mest för din mobil. Flera uppköpare, ett klick." />
        <meta property="og:url" content="https://cashmyphone.se" />
        <script type="application/ld+json">{JSON.stringify(HOME_JSON_LD)}</script>
      </Helmet>

      <main className="flex flex-col">
        <div className="flex justify-center px-4 md:px-6 pt-6 md:pt-12 pb-8 md:pb-16">
          <div
            className={
              flowActive
                ? "w-full max-w-2xl transition-all duration-500"
                : "w-full max-w-5xl grid md:grid-cols-2 gap-8 md:gap-16 items-center transition-all duration-500"
            }
          >
            {!flowActive && (
              <div className="space-y-4 md:space-y-6 text-center md:text-left animate-fade-in">
                <h1 className="text-[2rem] sm:text-5xl lg:text-[3.25rem] font-heading font-bold text-foreground leading-[1.1] tracking-tight">
                  Hitta det bästa priset för din <span className="text-primary">mobil</span>
                  <span className="md:hidden">
                    <span className="text-primary">,</span> gratis!
                  </span>
                  <span className="hidden md:inline">
                    <span className="text-primary">,</span> helt gratis!
                  </span>
                </h1>
                <p className="text-base md:text-lg text-white bg-primary rounded-2xl px-5 py-3 leading-relaxed max-w-md mx-auto md:mx-0">
                  Vi jämför priser från flera återförsäljare och visar dig vem som betalar mest
                </p>
              </div>
            )}

            <div>
              <UnifiedFlow onModelSelected={handleFlowActiveChange} />
            </div>
          </div>
        </div>

        <Suspense fallback={null}>
          {!flowActive && <LogoCarousel />}
          <HowItWorks />
          <FAQSection />
          <ArticlesSection />
        </Suspense>
      </main>
    </div>
  );
};

export default Index;
