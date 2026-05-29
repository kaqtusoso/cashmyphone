import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TermsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  type: "cashmyphone" | "vendor";
  vendorName?: string;
}

// ===============================
//  Vendor-specifika villkor
// ===============================
const vendorPolicies: Record<
  string,
  {
    title: string;
    sections: { heading: string; text: string }[];
  }
> = {
  Telestore: {
    title: "Telestores villkor",
    sections: [
      {
        heading: "1. Allmänna villkor",
        text: `Dessa villkor gäller när du säljer din mobiltelefon till Telestore Sverige AB via vår webbplats eller samarbetspartners som CashMyPhone.
Genom att genomföra försäljningen bekräftar du att du är den rättmätige ägaren till enheten och att den inte är stulen, operatörslåst eller föremål för avbetalning.
Telestore förbehåller sig rätten att justera värderingen om den inskickade enheten avviker från den information du angivit.
Du informeras alltid innan en eventuell prisändring görs, och kan välja att acceptera det nya beloppet eller få telefonen returnerad utan kostnad.`,
      },
      {
        heading: "2. Betalningsvillkor",
        text: `Utbetalning sker via Swish eller banköverföring så snart vi mottagit, kontrollerat och godkänt din enhet.
Normalt sker utbetalningen inom samma vardag som bedömningen är slutförd.
Om telefonen inte motsvarar det skick som angivits vid värderingen görs en ny prisbedömning.
Det nya priset meddelas via e-post eller sms och måste godkännas innan utbetalningen genomförs.`,
      },
      {
        heading: "3. Reklamation och justering av pris",
        text: `Om du anser att Telestores bedömning av din enhet är felaktig, kan du kontakta vår kundtjänst inom 7 dagar från att du mottagit bedömningsbeskedet.
Om enheten visar sig vara i ett sämre skick än angivet (t.ex. fuktskadad, sprucken skärm eller olåst iCloud-konto), kan priset komma att justeras.
Om enheten däremot motsvarar beskrivningen gäller det överenskomna priset utan ändring.`,
      },
      {
        heading: "4. Personuppgifter",
        text: `Telestore behandlar dina personuppgifter enligt GDPR.
Vi samlar in namn, adress, e-post, telefonnummer och betalningsinformation för att kunna genomföra försäljningen och betalningen.
Uppgifterna delas endast med betaltjänst- och logistikleverantörer.
Du har rätt att begära utdrag, rättelse eller radering av dina uppgifter genom att kontakta gdpr@telestore.se.`,
      },
    ],
  },

  Swappie: {
    title: "Swappies villkor",
    sections: [
      {
        heading: "1. Allmänna villkor",
        text: `Vi köper din mobiltelefon eller smarttelefon via vår webbplats. Du bekräftar att du är den rättmätige ägaren och att enheten inte är stulen, operatörslåst, eller föremål för obetalda avbetalningar. Vi erbjuder gratis frakt för att skicka enheten till oss. Du får först en prisuppskattning, skickar enheten och sedan genomför vi en fullständig kontroll. Om skickbeskrivningen stämmer med vår bedömning utbetalas beloppet enligt nedan. Om inte – får du ett nytt erbjudande eller möjlighet att få enheten returnerad utan kostnad.`,
      },
      {
        heading: "2. Betalning",
        text: `När vi mottagit och godkänt din enhet sker utbetalning inom 1–3 arbetsdagar via banköverföring eller enligt den betalningsmetod som anges. Ingen avgift tas ut för frakten till oss.`,
      },
      {
        heading: "3. Reklamation och justering av pris",
        text: `Vid mottagandet kontrolleras enhetens skick. Om den avviker från din beskrivning – exempelvis vatten-/fuktskada, funktionsfel, olåst konto, sprucken skärm – skickar vi ett nytt prisförslag. Du kan acceptera det eller begära att få enheten tillbaka utan kostnad. Om skickbeskrivningen stämmer gäller det ursprungliga priset.`,
      },
      {
        heading: "4. Personuppgifter",
        text: `Vi behandlar dina personuppgifter i enlighet med tillämplig lagstiftning (inklusive GDPR). Vi samlar in namn, adress, kontaktuppgifter samt uppgifter om enheten och betalningen för att kunna genomföra köpet. Dina uppgifter används för att genomföra transaktionen, kontakt vid frågor, och för intern administration. Vi delar inte dina personuppgifter med obehöriga tredje parter; endast med tjänsteleverantörer som krävs för genomförandet. Du har rätt att begära tillgång till dina uppgifter, rättelse, radering eller invändning mot behandling enligt gällande lag.

              Vi uppmuntrar dig att läsa vår fullständiga integritetspolicy på vår webbplats för fler detaljer.`,
      },
    ],
  },

  HappyPhone: {
    title: "HappyPhones villkor",
    sections: [
      {
        heading: "1. Allmänna villkor",
        text: `Du bekräftar att du är rättmätig ägare till enheten, att den inte är stulen, operatörslåst eller föremål för obetalda avbetalningar. När du accepterat ett erbjudande från HappyPhone får du instruktioner för att skicka in enheten. Enheten genomgår en noggrann kontroll vid mottagandet.`,
      },
      {
        heading: "2. Betalning",
        text: `Fraktkostnaden för att skicka in enheten täcks av HappyPhone. När enheten mottagits och godkänts sker utbetalning till ditt bankkonto.`,
      },
      {
        heading: "3. Reklamation och justering av pris",
        text: `Om enhetens skick avviker från din beskrivning (t.ex. skärm sprucken, vätskeskada, olåst konto) förbehåller sig HappyPhone rätten att justera priset eller returnera enheten utan kostnad för dig.`,
      },
      {
        heading: "4. Personuppgifter",
        text: `HappyPhone behandlar dina personuppgifter i enlighet med gällande dataskyddslagstiftning (inklusive GDPR). De samlar in namn, adress, kontaktuppgifter samt enhets- och betalningsinformation för att genomföra försäljningen. Uppgifterna används för att hantera affären och delas endast med betaltjänst- och logistikleverantörer vid behov. Du har rätt att begära tillgång till, rättelse eller radering av dina uppgifter enligt lag.`,
      },
    ],
  },

  FixMyPhone: {
    title: "FixMyPhones villkor",
    sections: [
      {
        heading: "1. Allmänna villkor",
        text: `Du bekräftar att du är rättmätig ägare till enheten. Du kan sälja enheten online genom att skicka in via post (frakt betald av FixMyPhone) eller lämna in i fiska butik. Vid inskick online följer du instruktionerna och paketar enligt angiven process.`,
      },
      {
        heading: "2. Betalning",
        text: `Utbetalning sker typiskt inom 1–4 arbetsdagar efter att FixMyPhone mottagit och godkänt din enhet. Frakten vid inskick står företaget för.`,
      },
      {
        heading: "3. Reklamation och justering av pris",
        text: `Efter mottagandet genomförs en kontroll av enhetens skick. Om den inte motsvarar din beskrivning (t.ex. skador, funktionsfel, olåst konto) görs en ny prisbedömning och du får välja att acceptera det nya beloppet eller få enheten tillbaka utan kostnad. Priset du såg som uppskattning på hemsidan kan ändras efter teknisk kontroll.`,
      },
      {
        heading: "4. Personuppgifter",
        text: `FixMyPhone behandlar dina personuppgifter i enlighet med tillämplig lag (inklusive GDPR). De samlar in namn, adress, kontaktuppgifter, enhets­information och betalningsuppgifter i syfte att genomföra transaktionen och utbetalning. Uppgifterna delas endast med nödvändiga tjänste­leverantörer och du har rätt att begära tillgång, rättelse eller radering av dina uppgifter enligt gällande bestämmelser.`,
      },
    ],
  },

  Renewed: {
    title: "Reneweds villkor",
    sections: [
      {
        heading: "1. Allmänna villkor",
        text: `Dessa villkor gäller när du säljer din mobiltelefon, surfplatta eller annan enhet till Renewed AB. Genom att godkänna villkoren bekräftar du att du är den rättmätige ägaren till enheten och har full rätt att sälja den och ta emot betalning. Enheten får inte vara stulen, operatörslåst eller föremål för obetalda avbetalningar. Du ansvarar för att uppgifterna du lämnar vid försäljningen är korrekta och fullständiga. När du anger modell och skick på vår webbplats får du ett prisförslag som gäller i upp till 14 dagar. Efter att vi mottagit din enhet genomförs en teknisk och visuell kontroll. Om enheten motsvarar din beskrivning gäller det angivna priset. Om vi upptäcker avvikelser, till exempel skador, fuktskador, funktionsfel eller olåst konto, gör vi en ny värdering. Du informeras alltid innan eventuella prisändringar görs och kan välja att acceptera det nya beloppet eller få din enhet returnerad utan kostnad.`,
      },
      {
        heading: "2. Betalning",
        text: `Frakten till Renewed är kostnadsfri för dig som säljare. När vi har mottagit, kontrollerat och godkänt enheten sker utbetalning normalt inom två till fyra arbetsdagar via banköverföring. Om enheten kräver ny värdering väntar vi med utbetalningen tills du har godkänt det justerade priset. Om vi inte får nödvändig information för utbetalningen inom 14 dagar efter kontakt kan enheten komma att returneras. Renewed ansvarar inte för eventuella förseningar som beror på felaktigt angivna betalningsuppgifter.`,
      },
      {
        heading: "3. Reklamation och justering av pris",
        text: `Vid mottagandet görs en noggrann inspektion av enhetens skick. Om den visar sig vara i ett sämre skick än vad som uppgavs vid försäljningen har Renwed AB rätt att justera priset. Det kan gälla till exempel funktionsfel, fuktskada, sprickor eller annan skada som inte tidigare uppgetts. Du får alltid möjlighet att godkänna det nya prisförslaget innan vi genomför betalningen. Om du väljer att inte acceptera det justerade priset returnerar vi enheten till dig utan kostnad. Om du anser att vår bedömning är felaktig kan du kontakta vår kundtjänst för en ny genomgång.`,
      },
      {
        heading: "4. Personuppgifter",
        text: `Renewed AB behandlar dina personuppgifter i enlighet med dataskyddsförordningen (GDPR). Vi samlar in uppgifter som namn, adress, e-postadress, telefonnummer, betalningsinformation samt uppgifter om den enhet du säljer. Uppgifterna används för att kunna genomföra försäljningen, hantera frakt, genomföra betalning och uppfylla våra rättsliga skyldigheter. Vi delar inte dina personuppgifter med obehöriga tredje parter, men kan dela dem med betaltjänst- och logistikleverantörer som behandlar uppgifter för vår räkning. Dina uppgifter sparas endast så länge det krävs för dessa syften eller enligt lag. Du har rätt att begära tillgång till, rättelse eller radering av dina personuppgifter, samt att invända mot behandling enligt gällande lag. För mer information om vår hantering av personuppgifter hänvisar vi till vår <a href="https://renewed.se/pages/integritetspolicy" target="_blank" rel="noopener noreferrer" style="text-decoration: underline;"> integritetspolicy på renewed.se </a>`,
      },
    ],
  },
};

// ===============================
//  Komponent
// ===============================
const TermsDialog = ({ open, onOpenChange, type, vendorName }: TermsDialogProps) => {
  const isVendor = type === "vendor";
  const policy = vendorName ? vendorPolicies[vendorName] : undefined;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">
            {isVendor
              ? policy
                ? policy.title
                : `${vendorName || "Återförsäljarens"} villkor`
              : "CashMyPhones villkor"}
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-4 text-sm text-foreground">
            {isVendor ? (
              policy ? (
                policy.sections.map((section, i) => (
                  <section key={i}>
                    <h3 className="font-semibold text-lg mb-2">{section.heading}</h3>
                    <p
                      className="text-muted-foreground leading-relaxed whitespace-pre-line"
                      dangerouslySetInnerHTML={{ __html: section.text }}
                    />
                  </section>
                ))
              ) : (
                <p className="text-muted-foreground">Inga specifika villkor tillgängliga för {vendorName}.</p>
              )
            ) : (
              <>
                <section>
                  <h3 className="font-semibold text-lg mb-2">1. Om CashMyPhone</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    CashMyPhone är en prisjämförelsetjänst som hjälper dig att hitta det bästa priset när du vill sälja
                    din begagnade iPhone. Vi samarbetar med noggrant utvalda partnerföretag som köper in begagnade
                    enheter. Vårt mål är att göra processen enkel, trygg och transparent – från värdering till
                    försäljning. CashMyPhone genomför ingen egen inlösen av enheter utan fungerar som en mellanhand
                    mellan dig och den återförsäljare du själv väljer via vår plattform.
                  </p>
                </section>

                <section>
                  <h3 className="font-semibold text-lg mb-2">2. Ansvar och garantier</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    CashMyPhone ansvarar inte för själva försäljningen eller transaktionen mellan dig och
                    återförsäljaren. När du väljer att sälja din enhet vidare sker avtalet direkt mellan dig och det
                    företag du valt. Varje återförsäljare har sina egna villkor gällande betalning, leverans,
                    reklamation och justering av pris. Du måste läsa igenom och godkänna dessa innan du slutför din
                    försäljning. CashMyPhone kan inte hållas ansvarigt för eventuella fel, förseningar, prisskillnader
                    eller andra omständigheter som uppstår i samband med den faktiska försäljningen.
                  </p>
                </section>

                <section>
                  <h3 className="font-semibold text-lg mb-2">3. Prisgaranti</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    De priser som visas på CashMyPhone är uppskattningar baserade på din beskrivning av enhetens modell,
                    lagringskapacitet, skick och batterihälsa. Det slutgiltiga priset fastställs först efter att
                    återförsäljaren mottagit och bedömt enheten. Om enheten avviker från den beskrivning du angett kan
                    priset komma att justeras enligt återförsäljarens villkor. CashMyPhone garanterar inte att det
                    visade priset alltid motsvarar det slutgiltiga erbjudandet, men vi strävar efter att informationen
                    ska vara så korrekt och uppdaterad som möjligt.
                  </p>
                </section>

                <section>
                  <h3 className="font-semibold text-lg mb-2">4. Personuppgifter</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    CashMyPhone behandlar dina personuppgifter i enlighet med gällande dataskyddslagstiftning (GDPR). Vi
                    delar endast den information som är nödvändig för att genomföra din försäljning – exempelvis
                    kontaktuppgifter, modellinformation och försäljningsdetaljer – med den återförsäljare du väljer.
                  </p>
                </section>

                <section>
                  <h3 className="font-semibold text-lg mb-2">5. Ändringar av villkor</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    CashMyPhone förbehåller sig rätten att när som helst uppdatera eller ändra dessa villkor. Eventuella
                    förändringar träder i kraft så snart de publicerats på vår webbplats. Vi rekommenderar att du
                    regelbundet läser igenom villkoren för att hålla dig uppdaterad kring hur vi hanterar information
                    och samarbeten.
                  </p>
                </section>
              </>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default TermsDialog;
