import { lazy, Suspense, useEffect, useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import ScrollToTop from "@/components/ScrollToTop";
import { SavedOffersProvider } from "@/contexts/SavedOffersContext";
import Index from "./pages/Index";

const NotFound = lazy(() => import("./pages/NotFound"));
const ArticlesListPage = lazy(() => import("./pages/ArticlesListPage"));
const ArticlePage = lazy(() => import("./pages/ArticlePage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const SellPhone = lazy(() => import("./pages/SellPhone"));

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

const App = () => (
  <QueryClientProvider client={queryClient}>
    <HelmetProvider>
      <BrowserRouter>
        <ScrollToTop />
        <SavedOffersProvider>
          <DeferredOverlays>
            <div className="flex flex-col min-h-screen">
              <Header />
              <div className="flex-1">
                <Suspense fallback={null}>
                  <Routes>
                    <Route path="/" element={<Index />} />
                    <Route path="/artiklar" element={<ArticlesListPage />} />
                    <Route path="/artikel/:slug" element={<ArticlePage />} />
                    <Route path="/om-oss" element={<AboutPage />} />
                    <Route path="/salja/:modelSlug" element={<SellPhone />} />
                    {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </Suspense>
              </div>
              <Footer />
            </div>
          </DeferredOverlays>
        </SavedOffersProvider>
      </BrowserRouter>
    </HelmetProvider>
  </QueryClientProvider>
);

export default App;
