import { Helmet } from "react-helmet-async";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const FAQ_ITEMS = [
  {
    question: "Hur lång tid tar det att sälja min mobil?",
    answer:
      "Från att du skickar in din mobil till att pengarna är på kontot tar det vanligtvis 3–7 arbetsdagar. Värderingen hos uppköparen tar 1–3 dagar och utbetalningen sker oftast samma dag du godkänner erbjudandet.",
  },
  {
    question: "Är det säkert att skicka mobilen med posten?",
    answer:
      "Ja. Du använder den spårbara och försäkrade fraktsedel som uppköparen mejlar dig. Tusentals svenskar säljer mobil via post varje månad utan problem.",
  },
  {
    question: "Måste jag sälja om jag skickar in min mobil?",
    answer:
      "Nej. Alla seriösa uppköpare erbjuder gratis retur om du inte accepterar deras bud. Du förbinder dig aldrig till att sälja förrän du aktivt godkänt erbjudandet.",
  },
  {
    question: "Varför skiljer sig priserna mellan uppköparna?",
    answer:
      "Uppköparna har olika lagerstatus, marginaler och affärsmodeller. Skillnaden för exakt samma modell kan vara flera hundralappar – därför lönar det sig alltid att jämföra först.",
  },
  {
    question: "Vad händer med mina data när jag säljer?",
    answer:
      "Innan du skickar din mobil ska du logga ut från iCloud och göra en fabriksåterställning. Uppköparna gör därefter en egen säkerhetsradering enligt branschstandard innan mobilen säljs vidare.",
  },
];

const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: FAQ_ITEMS.map((item) => ({
    "@type": "Question",
    name: item.question,
    acceptedAnswer: { "@type": "Answer", text: item.answer },
  })),
};

const FAQSection = () => {
  return (
    <section id="faq" className="py-16 md:py-24 px-4 md:px-6 scroll-mt-20 bg-secondary">
      <Helmet>
        <script type="application/ld+json">{JSON.stringify(faqJsonLd)}</script>
      </Helmet>

      <div className="max-w-3xl mx-auto">
        <h2 className="text-2xl md:text-3xl font-heading font-bold text-foreground text-center mb-8">
          Vanliga frågor
        </h2>
        <Accordion type="single" collapsible className="space-y-3">
          {FAQ_ITEMS.map((item, i) => (
            <AccordionItem
              key={i}
              value={`faq-${i}`}
              className="border border-border rounded-xl px-5 data-[state=open]:bg-card"
            >
              <AccordionTrigger className="text-left font-semibold text-foreground hover:no-underline py-5">
                {item.question}
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground leading-relaxed pb-5">
                {item.answer}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
};

export default FAQSection;
