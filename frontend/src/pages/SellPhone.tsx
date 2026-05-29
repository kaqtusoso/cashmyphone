import { useParams, Navigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import UnifiedFlow from "@/components/UnifiedFlow";
import { iphoneModels } from "@/data/mockData";
import { modelToSlug } from "@/utils/modelSlug";

const SellPhone = () => {
  const { modelSlug } = useParams<{ modelSlug: string }>();
  const slug = modelSlug?.replace(/^iphone-/, "iphone-");
  const model = iphoneModels.find((m) => modelToSlug(m) === slug);

  if (!model) return <Navigate to="/" replace />;

  return (
    <>
      <Helmet>
        <title>{`Sälj ${model} – Jämför priser | CashMyPhone`}</title>
        <meta
          name="description"
          content={`Få det bästa priset för din ${model}. Jämför vad svenska uppköpare betalar – snabbt, tryggt och gratis.`}
        />
        <link rel="canonical" href={`https://cashmyphone.se/salja/${modelSlug}`} />
      </Helmet>
      <main className="flex justify-center px-4 md:px-6 pt-6 md:pt-12 pb-8 md:pb-16">
        <div className="w-full max-w-2xl">
          <UnifiedFlow initialModel={model} />
        </div>
      </main>
    </>
  );
};

export default SellPhone;
