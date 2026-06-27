import { ExternalLink, Sparkles } from "lucide-react";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getVendorTermsPolicy, televeraTermsPolicy, TermsPolicy } from "@/data/termsPolicies";

interface TermsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  type: "televera" | "vendor";
  vendorName?: string;
}

const fallbackPolicy = (vendorName?: string): TermsPolicy => ({
  name: vendorName || "Återförsäljaren",
  summary:
    "Vi saknar en fullständig villkorsöversikt för den här uppköparen i Televera just nu. Läs uppköparens egna villkor innan du skickar in enheten.",
  sourceLabel: "Återförsäljarens egna villkor",
  sourceUrl: "#",
  updatedLabel: "Ingen källöversikt tillgänglig",
  sections: [
    {
      heading: "Kontrollera innan du godkänner",
      items: [
        "Säkerställ att pris, frakt, kontroll, betalning, prisjustering och retur framgår hos uppköparen.",
        "Ta bort Hitta min iPhone, Apple-ID, Google-konto och skärmlås innan enheten skickas eller lämnas in.",
        "Kontakta uppköparen direkt om något i deras villkor är oklart.",
      ],
    },
  ],
});

const TermsDialog = ({ open, onOpenChange, type, vendorName }: TermsDialogProps) => {
  const policy =
    type === "televera"
      ? televeraTermsPolicy
      : getVendorTermsPolicy(vendorName || "") ?? fallbackPolicy(vendorName);
  const isExternal = policy.sourceUrl.startsWith("http");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[86vh] max-w-2xl gap-0 overflow-hidden p-0">
        <DialogHeader className="border-b border-border px-5 pb-4 pt-5 text-left">
          <DialogTitle className="pr-8 text-xl font-bold">{policy.name} - köpvillkor</DialogTitle>
          <DialogDescription>{policy.updatedLabel}</DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[68vh]">
          <div className="space-y-5 px-5 py-5 text-sm">
            <section className="rounded-lg border border-[#cdeadd] bg-[#f2fbf6] p-4 text-[#18362b]">
              <div className="mb-2 flex items-center gap-2 font-semibold">
                <Sparkles className="h-4 w-4 text-[#00a873]" aria-hidden />
                AI-sammanfattning
              </div>
              <p className="leading-6">{policy.summary}</p>
            </section>

            {policy.sections.map((section) => (
              <section key={section.heading} className="space-y-2">
                <h3 className="text-base font-semibold text-foreground">{section.heading}</h3>
                <ul className="space-y-2 leading-6 text-muted-foreground">
                  {section.items.map((item) => (
                    <li key={item} className="flex gap-2">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[#00b87a]" aria-hidden />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ))}

            <footer className="border-t border-border pt-4 text-xs leading-5 text-muted-foreground">
              <p>
                Källöversikt:{" "}
                <a
                  href={policy.sourceUrl}
                  target={isExternal ? "_blank" : undefined}
                  rel={isExternal ? "noopener noreferrer" : undefined}
                  className="inline-flex items-center gap-1 font-semibold text-primary hover:underline"
                >
                  {policy.sourceLabel}
                  {isExternal ? <ExternalLink className="h-3 w-3" aria-hidden /> : null}
                </a>
              </p>
              <p className="mt-2">
                Sammanfattningen är gjord för att göra villkoren lättare att förstå. Vid skillnad mellan denna
                översikt och uppköparens egna villkor gäller uppköparens publicerade villkor.
              </p>
            </footer>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default TermsDialog;
