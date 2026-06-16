import { lazy, Suspense, useEffect, useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import Header from "@/components/Header";
import SiteFooter from "@/components/SiteFooter";
import ScrollToTop from "@/components/ScrollToTop";
import { SavedOffersProvider } from "@/contexts/SavedOffersContext";
import { persistCampaignParams, trackEvent } from "@/utils/tracking";
import Index from "./pages/Index";

const NotFound = lazy(() => import("./pages/NotFound"));
const ArticlesListPage = lazy(() => import("./pages/ArticlesListPage"));
const ArticlePage = lazy(() => import("./pages/ArticlePage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const PolicyPage = lazy(() => import("./pages/PolicyPage"));
const SellPhone = lazy(() => import("./pages/SellPhone"));
const Checkout = lazy(() => import("./pages/Checkout"));
const Summary = lazy(() => import("./pages/Summary"));

const queryClient = new QueryClient();

const DeferredOverlays = ({ children }: { children: React.ReactNode }) => {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const idle =
      (window as unknown as { requestIdleCallback?: (cb: () => void) => number })
        .requestIdleCallback || ((cb: () => void) => window.setTimeout(cb, 200));
    idle(() => setReady(true));
  }, []);
  if (!ready) return <>{children}</>;
  return (
    <TooltipProvider>
      <Toaster />
      <Sonner />
      {children}
    </TooltipProvider>
  );
};

const AppRoutes = () => {
  const location = useLocation();
  const useClaudeShell = location.pathname === "/" || location.pathname.startsWith("/salja/");

  useEffect(() => {
    persistCampaignParams(location.search);
    trackEvent("page_view", {
      page_path: `${location.pathname}${location.search}`,
      page_title: document.title,
    });
  }, [location.pathname, location.search]);

  return (
    <div className="flex flex-col min-h-screen">
      {!useClaudeShell && <Header />}
      <div className="flex-1">
        <Suspense fallback={null}>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/artiklar" element={<ArticlesListPage />} />
            <Route path="/artikel/:slug" element={<ArticlePage />} />
            <Route path="/om-oss" element={<AboutPage />} />
            <Route path="/villkor" element={<PolicyPage type="terms" />} />
            <Route path="/integritet" element={<PolicyPage type="privacy" />} />
            <Route path="/cookies" element={<PolicyPage type="cookies" />} />
            <Route path="/salja/:modelSlug" element={<SellPhone />} />
            <Route path="/salja/:modelSlug/:flowStep" element={<SellPhone />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/checkout/:checkoutStep" element={<Checkout />} />
            <Route path="/summary" element={<Summary />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </div>
      {!useClaudeShell && <SiteFooter />}
    </div>
  );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <HelmetProvider>
      <BrowserRouter>
        <ScrollToTop />
        <SavedOffersProvider>
          <DeferredOverlays>
            <AppRoutes />
          </DeferredOverlays>
        </SavedOffersProvider>
      </BrowserRouter>
    </HelmetProvider>
  </QueryClientProvider>
);

export default App;
