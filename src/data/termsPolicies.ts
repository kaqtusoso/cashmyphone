export type TermsSection = {
  heading: string;
  items: string[];
};

export type TermsPolicy = {
  name: string;
  summary: string;
  sourceLabel: string;
  sourceUrl: string;
  updatedLabel: string;
  sections: TermsSection[];
};

const commonSellerResponsibilities = [
  "Du ansvarar för att uppgifterna om modell, lagring, skick, batteri och eventuella skador är korrekta.",
  "Enheten ska vara din att sälja och får inte vara spärrad, stulen, operatörslåst på ett sätt som hindrar försäljning eller belastad av obetalda avtal.",
  "Hitta min iPhone, Apple-ID, Google-konto, skärmlås och annan aktiveringsspärr ska vara borttaget innan enheten skickas eller lämnas in.",
  "Säkerhetskopiera och radera personligt innehåll innan du lämnar ifrån dig enheten. Skicka inte med tillbehör om uppköparen inte uttryckligen ber om det.",
];

export const televeraTermsPolicy: TermsPolicy = {
  name: "Televera",
  summary:
    "Televera är jämförelsetjänsten, inte den slutliga köparen. Vi visar uppskattade bud och skickar orderuppgifter till den uppköpare du väljer, men uppköparens egna villkor styr frakt, kontroll, prisjustering, betalning och eventuell retur.",
  sourceLabel: "Televeras villkor, integritetspolicy och cookiepolicy",
  sourceUrl: "/villkor",
  updatedLabel: "Senast uppdaterad på Televera: 9 juni 2026",
  sections: [
    {
      heading: "Televeras roll",
      items: [
        "Televera samlar uppskattade priser, villkor och praktisk information från externa uppköpare.",
        "Televera köper inte enheten själv och är inte part i det slutliga köpet mellan dig och vald uppköpare.",
        "När du går vidare med ett erbjudande gäller uppköparens egna köpvillkor för själva affären.",
      ],
    },
    {
      heading: "Priser och värdering",
      items: [
        "Priserna på Televera bygger på informationen du anger och på de uppgifter Televera hämtar från uppköpare.",
        "Det slutliga priset fastställs normalt först efter att uppköparen har tagit emot och kontrollerat enheten.",
        "Televera försöker hålla priser och villkor aktuella men kan inte garantera att alla uppgifter alltid är fullständigt uppdaterade.",
      ],
    },
    {
      heading: "Ditt ansvar",
      items: commonSellerResponsibilities,
    },
    {
      heading: "Order och personuppgifter",
      items: [
        "När du fyller i orderuppgifter via Televera delar vi de uppgifter som behövs med uppköparen du valt.",
        "Det kan omfatta kontaktuppgifter, adress, uppgifter om enheten, valt erbjudande och betalningsrelaterad information.",
        "Televera behandlar uppgifter för att visa värderingar, förmedla din förfrågan, kommunicera med dig, felsöka tjänsten och uppfylla rättsliga skyldigheter.",
        "Uppköparen kan vara egen personuppgiftsansvarig för sin hantering av köp, frakt, betalning och support.",
      ],
    },
    {
      heading: "Ansvar och ändringar",
      items: [
        "Televera ansvarar inte för uppköparens handläggning, betalning, frakt, tekniska kontroll, prisjustering, retur eller kundsupport.",
        "Televera kan ändra, pausa eller avsluta delar av tjänsten, exempelvis om en uppköpare ändrar sitt erbjudande eller om tekniska problem uppstår.",
        "Televera kan uppdatera sina villkor och publicerar den senaste versionen på villkorssidan.",
      ],
    },
  ],
};

export const vendorTermsPolicies: Record<string, TermsPolicy> = {
  swappie: {
    name: "Swappie",
    summary:
      "Swappie ger ett preliminärt pris utifrån dina uppgifter, kontrollerar enheten efter mottagning och kan ge ett nytt erbjudande om skicket inte stämmer. Du behöver ta bort kontolås och radera data innan du skickar in telefonen.",
    sourceLabel: "Swappies säljsida och publika villkor/FAQ",
    sourceUrl: "https://swappie.com/se/salj-din-iphone/",
    updatedLabel: "Källor kontrollerade 19 juni 2026",
    sections: [
      {
        heading: "Pris och kontroll",
        items: [
          "Priset är en uppskattning baserad på modell, lagring och de skickuppgifter du lämnar.",
          "Swappie kontrollerar enheten när den kommer fram och fastställer därefter om det uppskattade priset kan betalas.",
          "Om skick eller funktion avviker kan Swappie föreslå ett nytt pris innan betalning.",
        ],
      },
      {
        heading: "Skicka in enheten",
        items: [
          "Du följer Swappies instruktioner för fraktetikett eller försäljningspaket och packar enheten så att den klarar transporten.",
          "Skicka bara med sådant som efterfrågas. Tillbehör kan hanteras separat eller sakna ersättning.",
          "Enheten bör vara laddad nog för kontroll när den tas emot.",
        ],
      },
      {
        heading: "Ditt ansvar",
        items: commonSellerResponsibilities,
      },
      {
        heading: "Betalning och retur",
        items: [
          "Betalning sker med vald betalningsmetod när enheten har kontrollerats och godkänts.",
          "Om Swappie föreslår ett nytt pris behöver du ta ställning till det innan affären slutförs.",
          "Om du inte accepterar en prisändring kan enheten normalt returneras enligt Swappies returprocess.",
        ],
      },
      {
        heading: "Personuppgifter",
        items: [
          "Swappie behandlar kontakt-, order-, enhets- och betalningsuppgifter för att hantera köpet.",
          "Uppgifter kan delas med nödvändiga logistik-, betalnings- och teknikleverantörer.",
          "Dina rättigheter kring tillgång, rättelse och radering framgår av Swappies integritetspolicy.",
        ],
      },
    ],
  },
  phonehero: {
    name: "PhoneHero",
    summary:
      "PhoneHero låter priset gälla en begränsad tid och kontrollerar enheten mot dina uppgifter. De kan be om kvitto, nekar kontolåsta enheter och erbjuder kostnadsfri retur om du inte accepterar ett justerat pris.",
    sourceLabel: "PhoneHeros säljsida, köpvillkor och integritetspolicy",
    sourceUrl: "https://phonehero.se/salj-din-gamla-mobil-till-oss",
    updatedLabel: "Källor kontrollerade 19 juni 2026",
    sections: [
      {
        heading: "Pris och giltighet",
        items: [
          "PhoneHeros erbjudna pris gäller under en begränsad period från värderingen.",
          "Priset förutsätter att enheten inte har andra defekter än de du angett i formuläret.",
          "Om skicket avviker kan PhoneHero göra prisavdrag och kontakta dig innan affären går vidare.",
        ],
      },
      {
        heading: "Ägarskap och kvitto",
        items: [
          "PhoneHero kan be om inköpskvitto eller annan dokumentation som visar att du får sälja enheten.",
          "Om underlag saknas, till exempel kvitto med namn och IMEI/serienummer för nyare enheter, kan köpet avbrytas.",
          "Enheten får inte vara stulen, spärrad eller knuten till obetalda avtal.",
        ],
      },
      {
        heading: "Kontolås och data",
        items: [
          "PhoneHero köper inte enheter som är låsta till Google-konto eller Apple-ID.",
          "Du ska ta bort aktiveringsspärr och nollställa enheten innan inlämning eller frakt.",
          "PhoneHero anger att de nollställer mjukvaran på enheter de köper in, men du bör ändå radera personligt innehåll själv först.",
        ],
      },
      {
        heading: "Frakt, retur och tillbehör",
        items: [
          "Om du skickar enheten ansvarar du för den tills PhoneHero har tagit emot den oskadd.",
          "Om PhoneHero returnerar enheten står de för transportansvar enligt sin returprocess.",
          "PhoneHero ansvarar inte för tillbehör som skickas eller lämnas in med enheten.",
        ],
      },
      {
        heading: "Personuppgifter",
        items: [
          "PhoneHero sparar kunduppgifter för att kunna hantera köp, garantiåtaganden, kundkommunikation och uppföljning.",
          "Uppgifter kan behandlas enligt deras integritetspolicy och delas med nödvändiga tjänsteleverantörer.",
        ],
      },
    ],
  },
  renewed: {
    name: "reNewed",
    summary:
      "reNeweds publika villkor är främst skrivna för köp av produkter, men anger tydligt ansvar kring kunduppgifter, betalningar, leverans, returer, garanti och att aktiveringslås måste tas bort. För säljordrar bör du räkna med teknisk kontroll innan slutligt pris.",
    sourceLabel: "reNeweds allmänna villkor, säljsida och integritetspolicy",
    sourceUrl: "https://renewed.se/pages/allmanna-villkor",
    updatedLabel: "Källor kontrollerade 19 juni 2026",
    sections: [
      {
        heading: "Avtal och kunduppgifter",
        items: [
          "reNewed ingår inte avtal med minderåriga och kräver korrekta kontaktuppgifter för beställningar.",
          "Kunduppgifter kan lagras och användas för att fullfölja tjänsten, ge service och hantera kundkontakt.",
          "Villkoren kan ändras av reNewed och tvingande konsumentskydd gäller där lagen kräver det.",
        ],
      },
      {
        heading: "Pris, produktinformation och kontroll",
        items: [
          "reNewed reserverar sig för fel i pris- och produktinformation, tekniska problem och skrivfel på webbplatsen.",
          "Vid försäljning av en enhet bör priset ses som preliminärt tills enheten har kontrollerats.",
          "Om skicket inte motsvarar uppgifterna kan priset behöva justeras innan affären slutförs.",
        ],
      },
      {
        heading: "Kontolås och återställning",
        items: [
          "reNeweds villkor anger att PIN-kod, Hitta min iPhone och Google-konto ska tas bort inför retur eller hantering av en enhet.",
          "Om lås inte är borttagna kan reNewed inte hantera enheten på vanligt sätt och kan ta ut hanteringsavgift.",
          "Du bör säkerhetskopiera och fabriksåterställa enheten innan den lämnas ifrån dig.",
        ],
      },
      {
        heading: "Retur, reklamation och garanti",
        items: [
          "reNewed har särskilda regler för ångerrätt, retur, reklamation och garanti när de säljer produkter.",
          "Skador som beror på kundens hantering, fukt, stötar, obehörig reparation eller kontoproblem kan falla utanför garanti.",
          "Returer ska normalt godkännas och hanteras enligt reNeweds instruktioner.",
        ],
      },
      {
        heading: "Personuppgifter",
        items: [
          "reNewed behandlar personuppgifter enligt sin integritetspolicy och kan använda uppgifter för order, betalning, service och kundkontakt.",
          "Du kan kontakta reNewed för utdrag, rättelse eller borttagning av uppgifter enligt dataskyddsreglerna.",
        ],
      },
    ],
  },
  happyphone: {
    name: "HappyPhone",
    summary:
      "HappyPhone beskriver en trade-in-process där värdering görs via experter, betalning sker efter undersökning och teknisk hantering sker i samarbete med Fix My Phone. Butiksinlämning kan ge betalning samma dag.",
    sourceLabel: "HappyPhones säljsida, e-handelsvillkor och privacy policy",
    sourceUrl: "https://happyphone.se/",
    updatedLabel: "Källor kontrollerade 19 juni 2026",
    sections: [
      {
        heading: "Värdering och process",
        items: [
          "HappyPhone erbjuder prisuppskattning via experter, antingen på plats eller via meddelande.",
          "Du kan sälja, byta upp dig eller kombinera inbyte med köp av rekonditionerad enhet.",
          "HappyPhone anger att teknisk service och hantering sker i samarbete med Fix My Phone.",
        ],
      },
      {
        heading: "Frakt och inlämning",
        items: [
          "Du kan besöka Fix My Phone-butiker eller skicka in enheten enligt instruktion.",
          "HappyPhone beskriver kostnadsfri frakt för inskick av enhet.",
          "Vid butikshantering kan värdering och utbetalning ske snabbare än vid inskick.",
        ],
      },
      {
        heading: "Betalning",
        items: [
          "Banköverföring görs efter att enheten har undersökts.",
          "I butik anger HappyPhone att betalning kan ske samma dag när undersökningen är klar.",
          "Om enheten avviker från uppgifterna kan priset påverkas innan utbetalning.",
        ],
      },
      {
        heading: "Ditt ansvar",
        items: commonSellerResponsibilities,
      },
      {
        heading: "Personuppgifter",
        items: [
          "HappyPhone behandlar kontakt-, order- och betalningsuppgifter för att kunna hantera köp, försäljning, service och support.",
          "Deras privacy policy styr hur uppgifter sparas, används och delas med nödvändiga leverantörer.",
        ],
      },
    ],
  },
  fixmyphone: {
    name: "FixMyPhone",
    summary:
      "FixMyPhone hanterar försäljning via egna butiker och inskick. Enheten undersöks innan betalning, och priset kan ändras om skicket inte stämmer med uppgifterna.",
    sourceLabel: "FixMyPhones säljsida och publika villkor",
    sourceUrl: "https://salja.fixmyphone.se/salja/",
    updatedLabel: "Källor kontrollerade 19 juni 2026",
    sections: [
      {
        heading: "Sälja online eller i butik",
        items: [
          "Du kan sälja genom att lämna in enheten i butik eller skicka in den enligt FixMyPhones instruktioner.",
          "FixMyPhone använder butiksnätet för service, kontroll och inlämning.",
          "Vid inskick ansvarar du för att följa pack- och fraktinstruktionerna.",
        ],
      },
      {
        heading: "Pris och kontroll",
        items: [
          "Priset bygger på den modell och det skick du anger när du värderar enheten.",
          "FixMyPhone kontrollerar enhetens skick innan slutlig betalning.",
          "Om skador, funktionsfel, fukt, spärrar eller andra avvikelser upptäcks kan priset justeras.",
        ],
      },
      {
        heading: "Betalning och retur",
        items: [
          "Utbetalning sker efter att enheten har mottagits och godkänts.",
          "Om du inte accepterar ett justerat pris hanteras retur enligt FixMyPhones instruktioner.",
          "Eventuella villkor för retur, frakt och hantering styrs av FixMyPhone.",
        ],
      },
      {
        heading: "Ditt ansvar",
        items: commonSellerResponsibilities,
      },
      {
        heading: "Personuppgifter",
        items: [
          "FixMyPhone behandlar kontakt-, enhets- och betalningsuppgifter för att hantera försäljning, kontroll, utbetalning och support.",
          "Uppgifter kan delas med nödvändiga betalnings-, logistik- och driftleverantörer.",
        ],
      },
    ],
  },
  telestore: {
    name: "Telestore",
    summary:
      "Telestore ger prisförslag online, skickar QR-kod för spårbar frakt och betalar när mobilen har tagits emot och kontrollerats. Om värderingen skiljer sig från dina uppgifter kontaktar de dig först.",
    sourceLabel: "Telestores säljsida, villkor och personuppgiftspolicy",
    sourceUrl: "https://telestore.se/",
    updatedLabel: "Källor kontrollerade 19 juni 2026",
    sections: [
      {
        heading: "Värdering",
        items: [
          "Du anger modell, skick och svarar på frågor för att få ett prisförslag online.",
          "Priset är beroende av att enheten motsvarar de uppgifter du lämnat.",
          "Telestore kontaktar dig först om kontrollen leder till en annan värdering.",
        ],
      },
      {
        heading: "Frakt och inlämning",
        items: [
          "Telestore skickar QR-kod för PostNord-frakt via SMS eller e-post.",
          "Du kan också lämna in enheten i butik där det alternativet erbjuds.",
          "Televeras checkout kan visa fraktavgift om Telestores aktuella erbjudande innebär att avgiften dras från priset.",
        ],
      },
      {
        heading: "Betalning",
        items: [
          "Telestore beskriver snabba Swish-betalningar efter mottagning och kontroll.",
          "Betalning sker först när enheten är kontrollerad och affären kan godkännas.",
          "Om priset ändras behöver du ta ställning innan utbetalning genomförs.",
        ],
      },
      {
        heading: "Ditt ansvar",
        items: commonSellerResponsibilities,
      },
      {
        heading: "Personuppgifter",
        items: [
          "Telestore behandlar kontakt-, order-, enhets- och betalningsuppgifter enligt sin personuppgiftspolicy.",
          "Uppgifter används för värdering, orderhantering, betalning, support och nödvändig kommunikation.",
        ],
      },
    ],
  },
  fixiphone: {
    name: "FixiPhone",
    summary:
      "FixiPhone erbjuder försäljning med snabb betalning och gratis frakt enligt säljsidan. Priset är beroende av att den inskickade enheten matchar dina uppgifter och att kontolås är borttaget.",
    sourceLabel: "FixiPhones säljsida och publika webbplatsvillkor",
    sourceUrl: "https://www.fixiphone.se/salj-din-mobil/",
    updatedLabel: "Källor kontrollerade 19 juni 2026",
    sections: [
      {
        heading: "Värdering",
        items: [
          "FixiPhone värderar enheten utifrån modell, lagring och skickuppgifter.",
          "Det preliminära priset förutsätter att enheten motsvarar beskrivningen när den kontrolleras.",
          "Skador, fukt, funktionsfel eller lås som inte angetts kan leda till omvärdering.",
        ],
      },
      {
        heading: "Frakt och butik",
        items: [
          "FixiPhone beskriver gratis frakt för att skicka in mobil, surfplatta eller annan enhet.",
          "Televeras checkout kan även visa butikslämning där FixiPhone erbjuder det.",
          "Du ansvarar för att följa pack- och fraktinstruktioner och spara inlämningskvitto.",
        ],
      },
      {
        heading: "Betalning och retur",
        items: [
          "FixiPhone anger snabb betalning när enheten har kontrollerats och godkänts.",
          "Om priset ändras efter kontroll ska du kunna ta ställning till det nya erbjudandet.",
          "Retur och eventuell returavgift styrs av FixiPhones aktuella villkor och det fraktalternativ som används.",
        ],
      },
      {
        heading: "Ditt ansvar",
        items: commonSellerResponsibilities,
      },
      {
        heading: "Personuppgifter",
        items: [
          "FixiPhone behandlar kontakt-, order-, enhets- och betalningsuppgifter för att hantera försäljningen.",
          "Cookie- och integritetsinformation på webbplatsen styr teknisk spårning och personuppgiftshantering.",
        ],
      },
    ],
  },
  fixphonepro: {
    name: "FixTech",
    summary:
      "FixTech/FixPhonePro erbjuder försäljning via frakt eller butik och betalar efter kontroll. Som hos övriga uppköpare är priset preliminärt tills enheten matchats mot dina uppgifter.",
    sourceLabel: "FixPhonePros säljsida och publika villkor",
    sourceUrl: "https://fixphonepro.net/salj/",
    updatedLabel: "Källor kontrollerade 19 juni 2026",
    sections: [
      {
        heading: "Pris och kontroll",
        items: [
          "Det pris som visas bygger på din beskrivning av enhetens modell, lagring och skick.",
          "FixTech/FixPhonePro kontrollerar enheten när den lämnas in eller tas emot.",
          "Om uppgifterna inte stämmer kan priset justeras innan betalning.",
        ],
      },
      {
        heading: "Frakt och butik",
        items: [
          "Du kan använda digital fraktetikett eller lämna in via butik där alternativet erbjuds.",
          "Vid frakt ansvarar du för att packa enheten enligt instruktion och spara kvitto från ombud.",
          "Butiksinlämning kan ge snabbare handläggning eftersom enheten kan kontrolleras på plats.",
        ],
      },
      {
        heading: "Betalning",
        items: [
          "Utbetalning sker med vald betalningsmetod när enheten är kontrollerad och godkänd.",
          "Swish kan kräva personnummer i Televeras checkout eftersom uppköparen behöver matcha mottagaren.",
          "Banköverföring kräver korrekta kontouppgifter från dig.",
        ],
      },
      {
        heading: "Ditt ansvar",
        items: commonSellerResponsibilities,
      },
      {
        heading: "Personuppgifter",
        items: [
          "FixTech/FixPhonePro behandlar person- och orderuppgifter för att kunna hantera försäljning, frakt, kontroll, betalning och support.",
          "Uppgifter kan delas med nödvändiga betalnings- och logistikleverantörer.",
        ],
      },
    ],
  },
};

export const getVendorTermsPolicy = (dealerIdOrName: string): TermsPolicy | undefined => {
  const name = dealerIdOrName.toLowerCase();
  if (name.includes("swappie")) return vendorTermsPolicies.swappie;
  if (name.includes("phonehero") || name.includes("phone hero")) return vendorTermsPolicies.phonehero;
  if (name.includes("renewed")) return vendorTermsPolicies.renewed;
  if (name.includes("happyphone") || name.includes("happy phone")) return vendorTermsPolicies.happyphone;
  if (name.includes("fixmyphone") || name.includes("fix my phone")) return vendorTermsPolicies.fixmyphone;
  if (name.includes("telestore")) return vendorTermsPolicies.telestore;
  if (name.includes("fixiphone") || name.includes("fix iphone")) return vendorTermsPolicies.fixiphone;
  if (name.includes("fixtech") || name.includes("fix tech") || name.includes("fixphonepro")) {
    return vendorTermsPolicies.fixphonepro;
  }
  return undefined;
};
