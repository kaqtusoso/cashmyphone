import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

const FAQ = () => {
  const faqs = [
    {
      question: "Hur exakta är priserna?",
      answer:
        "Vi ser till att priserna alltid är uppdaterade. Det exakta värdet kan dock skilja sig lite beroende på din telefons skick vid inspektion.",
    },
    {
      question: "Kostar det något att använda tjänsten?",
      answer: "Nope! Att jämföra priser här är (och kommer alltid vara) 100% gratis - precis som det ska vara.",
    },
    {
      question: "Hur snabbt får jag betalt?",
      answer:
        "Utbetalningstiden varierar mellan återförsäljarna, men vanligtvis tar det 1-3 dagar efter att de mottagit, inspekterat och bekräftat priset på din telefon.",
    },
    {
      question: "Kan jag sälja en trasig iPhone?",
      answer:
        "Självklart! Även en trasig iPhone kan glänsa i rätt händer. Våra partners tar emot den med öppna armar (och öppen plånbok)!",
    },
    {
      question: "Vad händer med min data på telefonen?",
      answer:
        "Du bör alltid radera all data från din iPhone innan du skickar den. Använd Apples återställningsfunktion för att säkerställa att all data tas bort säkert.",
    },
    {
      question: "Måste jag skicka med laddare och tillbehör?",
      answer:
        "Nej, du behöver inte skicka med några tillbehör. Det enda som krävs är själva telefonen. Vissa återförsäljare kan dock ge ett lite högre pris om originalkartongen finns med.",
    },
  ];

  return (
    <div id="faq" className="scroll-mt-20">
      <Accordion type="single" collapsible className="space-y-4">
        {faqs.map((faq, index) => (
          <AccordionItem
            key={index}
            value={`item-${index}`}
            className="bg-[#F5FFF7] rounded-xl px-6 border-none shadow-card"
          >
            <AccordionTrigger className="text-left font-semibold hover:no-underline">{faq.question}</AccordionTrigger>
            <AccordionContent className="text-foreground">{faq.answer}</AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
};

export default FAQ;
