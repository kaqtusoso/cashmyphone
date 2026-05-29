import { ArrowRight } from "lucide-react";
import BlogCard from "./BlogCard";

interface CtaButtonProps {
  onClick: () => void;
}

const CtaButton = ({ onClick }: CtaButtonProps) => (
  <div className="text-center my-8">
    <button
      onClick={onClick}
      className="bg-[#00B87A] hover:bg-[#00a06b] text-white font-semibold py-3 px-8 rounded-xl inline-flex items-center gap-2 shadow-[4px_4px_0px_rgba(0,184,122,0.3)] hover:shadow-[2px_2px_0px_rgba(0,184,122,0.3)] hover:translate-x-[2px] hover:translate-y-[2px] transition-all duration-200"
    >
      Gör en gratis värdering
      <ArrowRight className="w-5 h-5" />
    </button>
  </div>
);

const blogPosts = [
  {
    title: "Varför du får olika betalt för samma iPhone",
    subtitle: "Sanningen bakom prisskillnaderna",
    icon: "💰",
    excerpt:
      "Vi har alla varit där. Du ska sälja din gamla iPhone och undrar om du verkligen får det bästa priset. Svaret är nästan alltid nej – det beror på vem du frågar.",
    fullSummary: [
      "Samma iPhone kan värderas med hundralappars skillnad beroende på köparens lagerstatus och affärsmodell",
      "Återförsäljare med fullt lager betalar mindre, medan de som behöver påfyllning betalar toppris",
      "CashMyPhone samlar alla stora återförsäljare på ett ställe så du ser direkt vem som betalar bäst",
    ],
    content: (onCtaClick: () => void) => (
      <>
        <p>
          Vi har alla varit där. Du ska sälja din gamla iPhone, surfar in på en av de stora sajterna och får ett
          prisförslag. Det ser okej ut, men du kan inte låta bli att undra:{" "}
          <em>Är det här verkligen det bästa jag kan få?</em>
        </p>
        <p>
          Svaret är nästan alltid <strong>nej</strong>. Eller i alla fall: det beror på vem du frågar.
        </p>
        <p>
          Det kan låta märkligt att två exakt likadana telefoner – samma modell, samma batterihälsa och samma minne –
          kan värderas med flera hundralappars skillnad på en och samma dag. Men det finns logiska förklaringar till
          varför marknaden ser ut som den gör.
        </p>

        <h3 className="text-xl font-semibold mt-8 mb-4">Det handlar inte om mobilen, utan om lagret</h3>
        <p>
          När du säljer din iPhone till ett företag köper de inte den för att de gillar modellen; de köper den för att
          sälja den vidare.
        </p>
        <p>
          Om ett företag redan har 50 stycken iPhone 13 i lager, är de inte särskilt sugna på att köpa in din för
          toppris. De kommer ge dig ett lägre bud för att de vet att din telefon kommer ligga på hyllan ett tag. Ett
          annat företag kanske precis har sålt slut på just den modellen och behöver fylla på direkt – då är de beredda
          att betala betydligt mer för att säkra din telefon.
        </p>

        <h3 className="text-xl font-semibold mt-8 mb-4">Marginaler vs. Volym</h3>
        <p>Företag jobbar på olika sätt:</p>
        <ul className="list-disc pl-6 space-y-2">
          <li>
            <strong>Stora drakar:</strong> Har ofta enorma marknadsföringskostnader. För att täcka dem behöver de köpa
            din telefon billigt och sälja den dyrt.
          </li>
          <li>
            <strong>Utmanare:</strong> Vill växa snabbt och accepterar mindre vinst per telefon för att få in fler
            kunder. Här hamnar pengarna oftast i din ficka istället för i deras marknadsföringsbudget.
          </li>
        </ul>

        <h3 className="text-xl font-semibold mt-8 mb-4">Risken kostar pengar</h3>
        <p>
          Varje gång ett företag köper en begagnad telefon tar de en risk. Finns det dolda fel? Kommer skärmen sluta
          svara om en vecka? Vissa företag har väldigt strikta marginaler för att täcka upp för dessa risker, vilket
          drar ner priset du får se på skärmen.
        </p>

        <h3 className="text-xl font-semibold mt-8 mb-4">Varför vi startade CashMyPhone.se</h3>
        <p>
          När vi började titta på det här insåg vi hur skevt det var. Att sälja sin telefon är ju tillräckligt med
          projekt som det är – man ska radera data, hitta originalkartongen och packa ner den. Att man dessutom
          förväntas surfa runt på tio olika sajter för att manuellt jämföra priser gör att de flesta ger upp och tar
          första bästa bud.
        </p>
        <p>
          Det är precis därför vi skapade <strong>CashMyPhone.se</strong>.
        </p>
        <p>
          Vi tycker inte att det ska krävas en timmes research för att få rättvist betalt. Genom att samla de största
          och mest pålitliga aktörerna på ett ställe, gör vi jobbet åt dig. Du ser direkt vem som faktiskt behöver din
          specifika modell just nu och vem som betalar bäst.
        </p>

        <CtaButton onClick={onCtaClick} />

        <div className="bg-[#F1F8F4] rounded-xl p-6 mt-8 border-l-4 border-primary">
          <p className="font-medium text-foreground mb-0">
            <strong>Slutsatsen?</strong> Din iPhone har inget fast &quot;listpris&quot;. Den är värd exakt så mycket som
            den mest hungriga köparen är villig att ge för den idag. Och med tanke på hur snabbt priserna svänger, är
            det faktiskt värt de där 30 sekunderna det tar att jämföra.
          </p>
        </div>
      </>
    ),
  },
  {
    title: "Miljarderna som gömmer sig i byrålådan",
    subtitle: "Hur mycket är våra gamla mobiler värda?",
    icon: "🤫",
    excerpt:
      "Vi har alla den där lådan med gamla telefoner. Men visste du att svenskarna har miljardbelopp liggande och samlar damm? Uppskattningsvis...",
    fullSummary: [
      "15,6 miljoner gamla mobiltelefoner samlar damm i svenska hem – fler telefoner än människor i landet",
      "Cirka 5 miljoner är i tillräckligt gott skick för att säljas vidare direkt",
      "Med ett snittvärde på 1 500 kr per telefon landar totalsumman på närmare 10 miljarder kronor",
      "CashMyPhone gör det enkelt att se vad just din telefon är värd på under 30 sekunder",
    ],
    content: (onCtaClick: () => void) => (
      <>
        <p>
          Vi har alla den där lådan. Du vet vilken jag menar. Den där man trycker ner gamla sladdar, trasiga hörlurar
          och – nästan utan undantag – en eller två gamla mobiltelefoner.
        </p>
        <p>
          De ligger där som små tekniska fossiler. Kanske sparar du den som en &quot;reservmobil&quot; (som du aldrig
          använder), eller så har det bara inte blivit av att du gjort dig av med den för att det känns krångligt med
          batterier och radering av bilder.
        </p>
        <p>Men har du någonsin funderat på vad de där lådorna faktiskt är värda om man skulle summera hela Sverige?</p>

        <h3 className="text-xl font-semibold mt-8 mb-4">Jakten på siffran: Vad säger statistiken?</h3>
        <p>
          Det är svårt att få fram en exakt krona-för-krona-siffra eftersom värdet på en mobil sjunker snabbare än en
          sten i vatten. Men om vi tittar på färska rapporter från 2025, bland annat från aktörer som Refurbed och
          Fraunhofer Austria, börjar en ganska svindlande bild klarna.
        </p>
        <p>
          <strong>Här är vad vi vet:</strong>
        </p>
        <ul className="list-disc pl-6 space-y-2">
          <li>
            <strong>Antalet:</strong> Det uppskattas finnas omkring 15,6 miljoner gamla mobiltelefoner som ligger och
            samlar damm i svenska hem. Det är alltså fler telefoner än det finns människor i landet.
          </li>
          <li>
            <strong>Potentialen:</strong> Av dessa räknar man med att drygt 5 miljoner är i så pass gott skick att de
            skulle kunna rekonditioneras och säljas vidare direkt.
          </li>
          <li>
            <strong>Materialvärdet:</strong> Även de resterande 10 miljonerna, de som kanske är krossade eller helt
            stendöda, har ett värde. De innehåller guld, silver, kobolt och koppar. Enligt vissa beräkningar ligger det
            metaller för flera miljarder kronor bara i de svenska byrålådorna.
          </li>
        </ul>

        <h3 className="text-xl font-semibold mt-8 mb-4">Låt oss räkna på det (mellan tummen och pekfingret)</h3>
        <p>
          Om vi ska försöka oss på ett konkret räkneexempel – med förbehållet att detta är kvalificerade gissningar – så
          blir matematiken rätt intressant:
        </p>
        <p>
          Om vi har 5 miljoner fungerande telefoner och vi sätter ett väldigt försiktigt snittvärde på 1 500 kr styck
          (vissa iPhones är värda 4 000 kr, gamla Androids kanske 500 kr), så pratar vi om{" "}
          <strong>7,5 miljarder kronor</strong>.
        </p>
        <p>
          Om vi lägger till materialvärdet för de 10 miljoner &quot;skrotmobilerna&quot;, som ofta uppskattas till
          betydande belopp i återvinningsvärde, landar vi snabbt på en total summa som närmar sig{" "}
          <strong>10 miljarder kronor</strong>.
        </p>
        <p className="text-lg font-semibold text-primary">
          10 000 000 000 kronor. Det är alltså pengar som just nu bara ligger och väntar på att bli använda till resor,
          sparande eller vardagsinköp.
        </p>

        <h3 className="text-xl font-semibold mt-8 mb-4">Varför säljer vi inte?</h3>
        <p>
          Det finns två stora hinder som dyker upp i nästan alla undersökningar. Det första är oro för datasekretess –
          vi är rädda att våra gamla semesterbilder eller bankuppgifter ska hamna på villovägar. Det andra är ren och
          skär lathet (eller tidsbrist, om man ska vara snäll). Det känns helt enkelt för jobbigt att jämföra priser och
          skicka iväg paketet.
        </p>
        <p>
          Det är här det blir lite ironiskt. Samtidigt som vi letar efter billigare elavtal eller jagar extrapriser i
          mataffären, låter vi tusenlappar ligga och damma i en hallmöbel.
        </p>

        <CtaButton onClick={onCtaClick} />

        <h3 className="text-xl font-semibold mt-8 mb-4">Sammanfattningsvis: En outnyttjad guldgruva</h3>
        <p>
          Även om ingen kan säga på öret exakt hur mycket pengar det rör sig om, är alla experter överens: det handlar
          om miljardbelopp. Att låta en fungerande smartphone ligga i två år till gör den inte bara mindre värd för dig,
          utan det är också ett enormt slöseri med resurser som någon annan hade kunnat använda.
        </p>
        <p>
          Så, nästa gång du går förbi den där lådan – stanna upp. Det är inte bara elektronikskrot där i. Det är
          sannolikt en obetald middag, ett par nya skor eller ett välkommet tillskott till sparkontot.
        </p>

        <div className="bg-[#F1F8F4] rounded-xl p-6 mt-8 border-l-4 border-primary">
          <p className="font-medium text-foreground mb-0">
            Vi på <strong>CashMyPhone.se</strong> skapade vår tjänst just för att det inte ska finnas några ursäkter
            kvar. Att kolla om din del av de där 10 miljarderna finns i din låda tar ungefär 30 sekunder. Det är en
            ganska bra timpeng.
          </p>
        </div>
      </>
    ),
  },
  {
    title: "Så fungerar CashMyPhone (bakom kulisserna)",
    subtitle: "Från knapptryck till pengar på kontot",
    icon: "⚙️",
    excerpt:
      "Många tror att vi bara är en lista med priser. Men vi har byggt tjänsten för att vara din enda länk mellan byrålådan och ditt bankkonto...",
    fullSummary: [
      "Istället för att besöka flera sajter ser du alla aktuella bud på ett ställe",
      "Fyll i dina uppgifter direkt hos oss – vi sköter kontakten med återförsäljaren",
      "Tjänsten är helt gratis för dig som konsument, utan avgifter eller provision",
      "Det pris du ser är det pris du får",
    ],
    content: (onCtaClick: () => void) => (
      <>
        <p>
          Många tror att vi på CashMyPhone bara är en lista med priser. Men sanningen är att vi har byggt tjänsten för
          att vara den enda länken du behöver mellan din byrålåda och ditt bankkonto.
        </p>
        <p>
          Vi vet att tröskeln för att sälja sin gamla mobil ofta handlar om tid. Man orkar inte surfa runt, man orkar
          inte skapa konton på fem olika sajter och man vill inte behöva fylla i sina adressuppgifter om och om igen.
        </p>
        <p>Här är en genomgång av hur det faktiskt går till när du använder oss.</p>

        <h3 className="text-xl font-semibold mt-8 mb-4">1. Jämförelsen (utan att behöva leta själv)</h3>
        <p>
          Allt börjar med att du väljer din modell och skick. Istället för att du ska behöva besöka varje enskild
          återförsäljare för att se vem som betalar bäst just idag, så presenterar vi de mest aktuella buden direkt.
        </p>
        <p>
          Vi har valt ut pålitliga samarbetspartners så att du kan känna dig trygg oavsett vem i listan du väljer. Du
          ser svart på vitt vem som är mest sugen på just din modell för tillfället.
        </p>

        <h3 className="text-xl font-semibold mt-8 mb-4">2. Du gör allt på ett ställe</h3>
        <p>
          Det här är den största fördelen med CashMyPhone. När du har hittat ett pris du är nöjd med behöver du inte
          lämna vår sida för att slutföra affären.
        </p>
        <p>
          Du fyller i dina betalningsuppgifter och fraktinformation direkt hos oss. Sedan sköter vi resten. Vi skickar
          vidare dina uppgifter till den återförsäljare du valt, vilket gör att du slipper navigera genom nya gränssnitt
          eller krångliga formulär hos någon annan. Vi blir din trygga punkt genom hela processen.
        </p>

        <h3 className="text-xl font-semibold mt-8 mb-4">3. Alltid helt gratis (på riktigt)</h3>
        <p>
          En fråga vi ofta får är: <em>&quot;Vad är haken, vad kostar det mig?&quot;</em>. Svaret är enkelt:{" "}
          <strong>Ingenting</strong>.
        </p>
        <p>
          Tjänsten är, och kommer alltid att vara, helt gratis för dig som konsument. Vi tar inte ut någon administrativ
          avgift eller klipper en del av ditt försäljningspris. Det priset du ser i vår lista är det priset du får. Vår
          affärsmodell bygger på samarbeten med återförsäljarna, inte på att ta betalt av dig som vill göra ett
          miljömedvetet val.
        </p>

        <h3 className="text-xl font-semibold mt-8 mb-4">4. Varför vi gör det på det här sättet</h3>
        <p>
          Vår filosofi är enkel: Ju smidigare det är att sälja sin telefon, desto fler telefoner kommer att återvinnas
          eller få nytt liv hos en ny ägare. Genom att vi tar hand om &quot;pappersarbetet&quot; och förmedlar din order
          direkt till återförsäljaren, sparar du både tid och huvudvärk.
        </p>

        <h3 className="text-xl font-semibold mt-8 mb-4">Sammanfattningsvis:</h3>
        <ul className="list-disc pl-6 space-y-2">
          <li>
            <strong>Hitta:</strong> Se vem som betalar bäst just nu.
          </li>
          <li>
            <strong>Sälj:</strong> Fyll i dina uppgifter direkt hos oss – vi sköter kontakten med köparen.
          </li>
          <li>
            <strong>Få betalt:</strong> Skicka in mobilen och se pengarna rulla in.
          </li>
        </ul>

        <CtaButton onClick={onCtaClick} />

        <div className="bg-[#F1F8F4] rounded-xl p-6 mt-8 border-l-4 border-primary">
          <p className="font-medium text-foreground mb-0">
            Det ska inte vara ett projekt att tömma byrålådan. Det ska vara en snabb affär som både du och miljön tjänar
            på.
          </p>
        </div>
      </>
    ),
  },
];

const BlogSection = () => {
  return (
    <section id="blogg" className="py-20 px-4 bg-background scroll-mt-20">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-3">Tips & insikter om begagnade mobiler</h2>
          <span className="inline-block text-sm font-semibold text-primary bg-primary/10 px-4 py-1.5 rounded-full">
            Lär dig mer genom att läsa vår blogg
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {blogPosts.map((post, index) => (
            <BlogCard
              key={index}
              title={post.title}
              excerpt={post.excerpt}
              icon={post.icon}
              content={post.content}
              fullSummary={post.fullSummary}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default BlogSection;
