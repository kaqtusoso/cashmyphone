import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

const STORAGE_KEY = "cashmyphone-theme";

const getInitialTheme = (): "light" | "dark" => {
  if (typeof window === "undefined") return "light";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return "light";
};

const ThemeToggle = () => {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const initial = getInitialTheme();
    setTheme(initial);
    document.documentElement.classList.toggle("dark", initial === "dark");
  }, []);

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.classList.toggle("dark", next === "dark");
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? "Byt till ljust tema" : "Byt till mörkt tema"}
      title={theme === "dark" ? "Ljust tema" : "Mörkt tema"}
      className="inline-flex items-center justify-center h-9 w-9 rounded-full border border-border bg-secondary text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
    >
      {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
    </button>
  );
};

export default ThemeToggle;
