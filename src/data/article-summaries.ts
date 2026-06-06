export type ArticleSummary = {
  slug: string;
  title: string;
  ingress: string;
  /** Markdown body. */
  content: string;
};

export const articleSummaries: ArticleSummary[] = [
  {
    slug: "olika-pris-samma-iphone",
    title: "Varför du får olika betalt för samma iPhone",
    ingress:
      "Sanningen bakom prisskillnaderna när du säljer din iPhone – och varför det nästan alltid lönar sig att jämföra först.",
    content: `Vi har alla varit där. Du ska sälja din gamla iPhone, surfar in på en av de stora sajterna och får ett prisförslag. Det ser okej ut, men du kan inte låta bli att undra: *Är det här verkligen det bästa jag kan få?*

Svaret är nästan alltid **nej**. Eller i alla fall: det beror på vem du frågar.

Det kan låta märkligt att två exakt likadana telefoner – samma modell, samma batterihälsa och samma minne – kan värderas med flera hundralappars skillnad på en och samma dag. Men det finns logiska förklaringar till varför marknaden ser ut som den gör.

## Det handlar inte om mobilen, utan om lagret

När du säljer din iPhone till ett företag köper de inte den för att de gillar modellen; de köper den för att sälja den vidare.

Om ett företag redan har 50 stycken iPhone 13 i lager är de inte särskilt sugna på att köpa in din för toppris. Ett annat företag kanske precis har sålt slut på just den modellen och behöver fylla på direkt – då är de beredda att betala betydligt mer för att säkra din telefon.

## Marginaler vs. volym

- **Stora drakar:** Har ofta enorma marknadsföringskostnader. För att täcka dem behöver de köpa din telefon billigt och sälja den dyrt.
- **Utmanare:** Vill växa snabbt och accepterar mindre vinst per telefon för att få in fler kunder. Här hamnar pengarna oftast i din ficka istället för i deras marknadsföringsbudget.

## Risken kostar pengar

Varje gång ett företag köper en begagnad telefon tar de en risk. Finns det dolda fel? Kommer skärmen sluta svara om en vecka? Vissa företag har strikta marginaler för att täcka upp för dessa risker, vilket drar ner priset du får se på skärmen.

## Varför vi startade CashMyPhone.se

När vi började titta på det här insåg vi hur skevt det var. Att sälja sin telefon är ju tillräckligt med projekt som det är – man ska radera data, hitta originalkartongen och packa ner den. Att man dessutom förväntas surfa runt på tio olika sajter för att manuellt jämföra priser gör att de flesta ger upp och tar första bästa bud.

Det är precis därför vi skapade **CashMyPhone.se**. Vi samlar de största och mest pålitliga uppköparna på ett ställe, så att du direkt ser vem som faktiskt behöver din specifika modell just nu och vem som betalar bäst.

> **Slutsatsen?** Din iPhone har inget fast "listpris". Den är värd exakt så mycket som den mest hungriga köparen är villig att ge för den idag. Och med tanke på hur snabbt priserna svänger är det faktiskt värt de där 30 sekunderna det tar att jämföra.`,
  },
  {
    slug: "miljarderna-i-byraladan",
    title: "Miljarderna som gömmer sig i byrålådan",
    ingress:
      "Hur mycket är svenskarnas gamla mobiler värda – och varför säljer vi inte dem? Vi räknar på guldgruvan.",
    content: `Vi har alla den där lådan. Du vet vilken jag menar. Den där man trycker ner gamla sladdar, trasiga hörlurar och – nästan utan undantag – en eller två gamla mobiltelefoner.

De ligger där som små tekniska fossiler. Kanske sparar du den som en "reservmobil" (som du aldrig använder), eller så har det bara inte blivit av att du gjort dig av med den.

Men har du någonsin funderat på vad de där lådorna faktiskt är värda om man skulle summera hela Sverige?

## Jakten på siffran: vad säger statistiken?

Det är svårt att få fram en exakt krona-för-krona-siffra eftersom värdet på en mobil sjunker snabbare än en sten i vatten. Men om vi tittar på färska rapporter från 2025 börjar en ganska svindlande bild klarna.

- **Antalet:** Det uppskattas finnas omkring 15,6 miljoner gamla mobiltelefoner som ligger och samlar damm i svenska hem. Det är fler telefoner än det finns människor i landet.
- **Potentialen:** Drygt 5 miljoner är i så pass gott skick att de skulle kunna rekonditioneras och säljas vidare direkt.
- **Materialvärdet:** Även de resterande 10 miljonerna har ett värde – guld, silver, kobolt och koppar för flera miljarder kronor bara i de svenska byrålådorna.

## Låt oss räkna på det

Om vi har 5 miljoner fungerande telefoner och sätter ett försiktigt snittvärde på 1 500 kr styck, så pratar vi om **7,5 miljarder kronor**.

Lägger vi till materialvärdet för de 10 miljoner "skrotmobilerna" landar vi snabbt på närmare **10 miljarder kronor**.

10 000 000 000 kronor. Det är pengar som bara ligger och väntar på att bli använda till resor, sparande eller vardagsinköp.

## Varför säljer vi inte?

Det finns två stora hinder. Det första är oro för datasekretess – vi är rädda att våra gamla bilder eller bankuppgifter ska hamna på villovägar. Det andra är ren och skär lathet.

Det är här det blir lite ironiskt. Samtidigt som vi letar efter billigare elavtal eller jagar extrapriser i mataffären låter vi tusenlappar ligga och damma i en hallmöbel.

> Vi på **CashMyPhone.se** skapade vår tjänst just för att det inte ska finnas några ursäkter kvar. Att kolla om din del av de där 10 miljarderna finns i din låda tar ungefär 30 sekunder. Det är en ganska bra timpeng.`,
  },
  {
    slug: "sa-fungerar-cashmyphone",
    title: "Så fungerar CashMyPhone (bakom kulisserna)",
    ingress:
      "Från knapptryck till pengar på kontot – så har vi byggt tjänsten för att vara den enda länken du behöver.",
    content: `Många tror att vi på CashMyPhone bara är en lista med priser. Men sanningen är att vi har byggt tjänsten för att vara den enda länken du behöver mellan din byrålåda och ditt bankkonto.

Vi vet att tröskeln för att sälja sin gamla mobil ofta handlar om tid. Man orkar inte surfa runt, man orkar inte skapa konton på fem olika sajter och man vill inte fylla i sina adressuppgifter om och om igen.

## 1. Jämförelsen – utan att behöva leta själv

Allt börjar med att du väljer din modell och skick. Istället för att besöka varje enskild uppköpare för att se vem som betalar bäst just idag presenterar vi de mest aktuella buden direkt.

## 2. Du gör allt på ett ställe

När du har hittat ett pris du är nöjd med behöver du inte lämna vår sida för att slutföra affären. Vi skickar vidare dina uppgifter till uppköparen du valt och blir din trygga punkt genom hela processen.

## 3. Alltid helt gratis

En fråga vi ofta får är: *"Vad är haken, vad kostar det mig?"*. Svaret är enkelt: **Ingenting**. Vår affärsmodell bygger på samarbeten med uppköparna, inte på att ta betalt av dig.

## 4. Varför vi gör det på det här sättet

Vår filosofi är enkel: ju smidigare det är att sälja sin telefon, desto fler telefoner kommer att återvinnas eller få nytt liv hos en ny ägare.

**Sammanfattningsvis:**

- **Hitta:** Se vem som betalar bäst just nu.
- **Sälj:** Fyll i dina uppgifter direkt hos oss – vi sköter kontakten med köparen.
- **Få betalt:** Skicka in mobilen och se pengarna rulla in.

> Det ska inte vara ett projekt att tömma byrålådan. Det ska vara en snabb affär som både du och miljön tjänar på.`,
  },
];
