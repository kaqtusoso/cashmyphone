import { Helmet } from "react-helmet-async";

import DesktopHome from "@/components/DesktopHome";
import MobileHome from "@/components/MobileHome";
import { DEFAULT_OG_IMAGE, DEFAULT_OG_IMAGE_ALT, SITE_NAME, SITE_URL } from "@/utils/seo";

const HOME_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Televera",
  description: "Jämför vad svenska uppköpare betalar för din iPhone och sälj enkelt och tryggt.",
  url: SITE_URL,
  applicationCategory: "FinanceApplication",
};

const Index = () => {
  return (
    <div className="bg-background">
      <Helmet>
        <title>Televera – Jämför priser och sälj din iPhone tryggt</title>
        <meta
          name="description"
          content="Jämför erbjudanden från svenska uppköpare och sälj din iPhone enkelt och tryggt. Se vem som betalar bäst på ett ställe."
        />
        <meta name="robots" content="index, follow" />
        <link rel="canonical" href={SITE_URL} />
        <meta property="og:site_name" content={SITE_NAME} />
        <meta property="og:locale" content="sv_SE" />
        <meta property="og:title" content="Televera – Jämför priser och sälj din iPhone tryggt" />
        <meta
          property="og:description"
          content="Se vem som betalar bäst för din iPhone utan att själv lägga upp annonser och boka möten."
        />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={SITE_URL} />
        <meta property="og:image" content={DEFAULT_OG_IMAGE} />
        <meta property="og:image:alt" content={DEFAULT_OG_IMAGE_ALT} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Televera – Jämför priser och sälj din iPhone tryggt" />
        <meta
          name="twitter:description"
          content="Jämför svenska uppköpare på ett ställe och välj bästa erbjudandet för din iPhone."
        />
        <meta name="twitter:image" content={DEFAULT_OG_IMAGE} />
        <meta name="twitter:image:alt" content={DEFAULT_OG_IMAGE_ALT} />
        <script type="application/ld+json">{JSON.stringify(HOME_JSON_LD)}</script>
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

export default Index;
