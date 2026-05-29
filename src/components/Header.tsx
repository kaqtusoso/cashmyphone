import { Link } from "react-router-dom";
import { Menu } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import ThemeToggle from "@/components/ThemeToggle";
import logoImg from "@/assets/logo-green.png";

const Header = () => {
  return (
    <header className="border-b border-border px-6 py-4 flex items-center justify-between bg-background">
      <Link
        to="/"
        className="flex items-center gap-2 text-xl font-heading font-bold text-foreground"
      >
        <img
          src={logoImg}
          alt="CashMyPhone"
          className="h-8 w-auto"
          height={32}
          fetchPriority="high"
          decoding="async"
        />
      </Link>

      <div className="flex items-center gap-3">
        <nav className="hidden md:flex items-center gap-6 mr-2">
          <Link
            to="/#hur-det-fungerar"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Hur det fungerar
          </Link>
          <Link
            to="/artiklar"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Artiklar
          </Link>
          <Link
            to="/om-oss"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Om oss
          </Link>
        </nav>

        <ThemeToggle />

        <DropdownMenu>
          <DropdownMenuTrigger
            className="md:hidden p-2 -mr-2 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Meny"
          >
            <Menu className="w-5 h-5" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link to="/#hur-det-fungerar">Hur det fungerar</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/artiklar">Artiklar</Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/om-oss">Om oss</Link>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default Header;
