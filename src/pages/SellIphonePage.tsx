import { Helmet } from "react-helmet-async";

import DesktopHome from "@/components/DesktopHome";
import MobileHome from "@/components/MobileHome";

const SELL_IPHONE_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebPage",
  name: "Sälj iPhone",
  description:
    "Jämför bud från svenska uppköpare innan du säljer din iPhone. Televera samlar flera bud på ett ställe.",
  url: "https://televera.se/salja-iphone",
  isPartOf: {
    "@type": "WebSite",
    name: "Televera",
    url: "https://televera.se",
  },
};

const SellIphonePage = () => {
  return (
    <div className="bg-background">
      <Helmet>
        <title>Sälj iPhone - jämför bud från svenska uppköpare | Televera</title>
        <meta
          name="description"
          content="Sälj din iPhone med bättre koll. Jämför bud från flera svenska uppköpare gratis och välj själv om du vill gå vidare."
        />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href="https://televera.se/salja-iphone" />
        <meta property="og:title" content="Sälj iPhone - jämför bud | Televera" />
        <meta
          property="og:description"
          content="Jämför vad flera svenska uppköpare erbjuder för din iPhone innan du säljer."
        />
        <meta property="og:url" content="https://televera.se/salja-iphone" />
        <script type="application/ld+json">{JSON.stringify(SELL_IPHONE_JSON_LD)}</script>
      </Helmet>

      <main>
        <div className="cmp-desktop-home-only">
          <DesktopHome />
        </div>
        <div className="cmp-mobile-home-only">
          <MobileHome />
        </div>
      </main>
    </div>
  );
};

export default SellIphonePage;
