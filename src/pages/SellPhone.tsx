import { useParams, Navigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import UnifiedFlow from "@/components/UnifiedFlow";
import { iphoneModels } from "@/data/iphoneCatalog";
import { modelToSlug, slugToModel } from "@/utils/modelSlug";
import { DEFAULT_OG_IMAGE, DEFAULT_OG_IMAGE_ALT, SITE_NAME, absoluteUrl } from "@/utils/seo";

const SellPhone = () => {
  const { modelSlug, flowStep } = useParams<{ modelSlug: string; flowStep?: string }>();
  const slug = modelSlug?.replace(/^iphone-/, "iphone-");
  const model = iphoneModels.find((m) => modelToSlug(m) === slug) ?? (slug ? slugToModel(slug) : "");
  const canonicalPath = `/salja/${modelSlug}`;
  const canonicalUrl = absoluteUrl(canonicalPath);
  const title = `Sälj ${model} tryggt – jämför priser | Televera`;
  const description = `Jämför vad svenska uppköpare betalar för din ${model}. Se bästa erbjudandet, slipp privatmarknadsstrul och sälj tryggt online.`;

  if (!model) return <Navigate to="/" replace />;

  return (
    <>
      <Helmet>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={canonicalUrl} />
        {flowStep ? <meta name="robots" content="noindex, follow" /> : <meta name="robots" content="index, follow" />}
        <meta property="og:site_name" content={SITE_NAME} />
        <meta property="og:locale" content="sv_SE" />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={description} />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={canonicalUrl} />
        <meta property="og:image" content={DEFAULT_OG_IMAGE} />
        <meta property="og:image:alt" content={DEFAULT_OG_IMAGE_ALT} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={title} />
        <meta name="twitter:description" content={description} />
        <meta name="twitter:image" content={DEFAULT_OG_IMAGE} />
      </Helmet>
      <main>
        <UnifiedFlow initialModel={model} initialStepSlug={flowStep} />
      </main>
    </>
  );
};

export default SellPhone;
