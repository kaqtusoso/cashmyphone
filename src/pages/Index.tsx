import { Helmet } from "react-helmet-async";

import DesktopHome from "@/components/DesktopHome";
import MobileHome from "@/components/MobileHome";

const HOME_JSON_LD = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "CashMyPhone",
  description: "Jämför vad svenska uppköpare betalar för din begagnade mobil – snabbt, tryggt och gratis.",
  url: "https://cashmyphone.se",
  applicationCategory: "FinanceApplication",
};

const Index = () => {
  return (
    <div className="bg-background">
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
