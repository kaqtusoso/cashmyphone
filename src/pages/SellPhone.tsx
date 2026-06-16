import { useParams, Navigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import UnifiedFlow from "@/components/UnifiedFlow";
import { iphoneModels } from "@/data/iphoneCatalog";
import { modelToSlug, slugToModel } from "@/utils/modelSlug";
import { absoluteUrl } from "@/utils/seo";

const SellPhone = () => {
  const { modelSlug, flowStep } = useParams<{ modelSlug: string; flowStep?: string }>();
  const slug = modelSlug?.replace(/^iphone-/, "iphone-");
  const model = iphoneModels.find((m) => modelToSlug(m) === slug) ?? (slug ? slugToModel(slug) : "");
  const canonicalPath = `/salja/${modelSlug}`;

  if (!model) return <Navigate to="/" replace />;

  return (
    <>
      <Helmet>
        <title>{`Sälj ${model} – Jämför priser | Televera`}</title>
        <meta
          name="description"
          content={`Få det bästa priset för din ${model}. Jämför vad svenska uppköpare betalar – snabbt, tryggt och gratis.`}
        />
        <link rel="canonical" href={absoluteUrl(canonicalPath)} />
        {flowStep ? <meta name="robots" content="noindex, follow" /> : <meta name="robots" content="index, follow" />}
      </Helmet>
      <main>
        <UnifiedFlow initialModel={model} initialStepSlug={flowStep} />
      </main>
    </>
  );
};

export default SellPhone;
