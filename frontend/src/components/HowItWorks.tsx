import iphoneMockup from "@/assets/mockup-iphone-new.png";

const steps = [
  {
    number: 1,
    title: "Välj modell & skick",
    description: "Berätta vilken iPhone du har och hur den mår – det tar ca 30 sekunder.",
  },
  {
    number: 2,
    title: "Få värdering direkt",
    description: "Vi jämför priser från flera uppköpare och visar vem som betalar mest.",
  },
  {
    number: 3,
    title: "Skicka in & få betalt",
    description: "Välj bästa erbjudandet, posta din mobil och få pengarna på kontot.",
  },
];

const HowItWorks = () => {
  return (
    <section
      id="hur-det-fungerar"
      className="bg-background pt-8 md:pt-12 px-4 md:px-6 pb-0 overflow-hidden scroll-mt-20"
    >
      <div className="max-w-5xl mx-auto">
        <div className="grid md:grid-cols-2 gap-6 md:gap-10 items-stretch">
          <div className="order-2 md:order-1 flex justify-center items-end">
            <div className="w-64 md:w-80 drop-shadow-2xl">
              <img
                src={iphoneMockup}
                alt="iPhone-värdering på cashmyphone.se"
                className="w-full h-auto object-contain object-bottom block"
                loading="lazy"
                decoding="async"
              />
            </div>
          </div>

          <div className="order-1 md:order-2 space-y-8 self-center">
            {steps.map((step) => (
              <div key={step.number} className="flex gap-4 items-start">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-heading font-bold text-lg">
                  {step.number}
                </div>
                <div>
                  <h3 className="font-heading font-semibold text-lg text-foreground mb-1">
                    {step.title}
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
