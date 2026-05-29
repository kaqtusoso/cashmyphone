import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const ScrollToTop = () => {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (hash) {
      const id = hash.slice(1);
      let attempts = 0;
      const tryScroll = () => {
        const el = document.getElementById(id);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
          return;
        }
        if (attempts++ < 20) setTimeout(tryScroll, 100);
      };
      tryScroll();
    } else {
      window.scrollTo(0, 0);
    }
  }, [pathname, hash]);

  return null;
};

export default ScrollToTop;
