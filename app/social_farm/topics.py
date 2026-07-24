from dataclasses import dataclass

from .copybook import NATURAL_COPY


@dataclass(frozen=True)
class SlideBlueprint:
    heading: str
    body: tuple[str, str]
    scene: str
    visual_type: str = "object"


@dataclass(frozen=True)
class TopicBlueprint:
    key: str
    category: str
    title: str
    caption: str
    cta: str
    slides: tuple[SlideBlueprint, ...]


TOPICS: tuple[TopicBlueprint, ...] = (
    TopicBlueprint(
        key="tech-drawer",
        category="vardagsberattelse",
        title="5 saker som fick mig att sluta spara gamla iPhones",
        caption="Reservmobil eller bara ännu en sak i lådan? Börja med att kolla modell, skick och vilka bud som finns. Du behöver inte sälja bara för att du jämför.",
        cta="kolla värdet först. bestäm dig sen.",
        slides=(
            SlideBlueprint(
                "1. jag slutade kalla den reservmobil",
                ("den hade legat orörd i lådan i över ett år", "det jag egentligen sparade var ett beslut"),
                "en öppen hallbyrå med en äldre telefon, laddkabel och nycklar",
            ),
            SlideBlueprint(
                "2. jag kollade vad den faktiskt var värd",
                ("jag hade fått för mig att en äldre mobil knappt var värd något", "men jag hade aldrig jämfört buden"),
                "äldre smartphone på ett lugnt skandinaviskt skrivbord bredvid en kopp",
            ),
            SlideBlueprint(
                "3. jag jämförde mer än en siffra",
                ("olika uppköpare kan värdera samma telefon olika", "först då fick siffran ett sammanhang"),
                "laptop på ett köksbord med diskret jämförelsevy, ingen läsbar skärmtext",
                "interface",
            ),
            SlideBlueprint(
                "4. jag slutade vänta på rätt tillfälle",
                ("jag tänkte alltid att jag skulle ta tag i det senare", "värdet blev inte tydligare av att mobilen låg kvar"),
                "person sedd bakifrån som rensar en liten låda i en svensk lägenhet",
                "person_far",
            ),
            SlideBlueprint(
                "5. jag gjorde det till en tiominutersgrej",
                ("jag kollade modell, lagring och skick", "sedan kunde jag bestämma mig utan stress"),
                "äldre mobil, anteckningsbok och en enkel timer på ett ljust bord",
            ),
        ),
    ),
    TopicBlueprint(
        key="describe-condition",
        category="skick",
        title="5 saker jag kollade innan jag beskrev skicket",
        caption="Kosmetiska märken och funktionsfel är inte samma sak. Kontrollera mobilen i lugn och ro innan du jämför bud.",
        cta="beskriv ärligt. jämför tydligare.",
        slides=(
            SlideBlueprint(
                "1. jag började med skärmen",
                ("en liten repa är inte samma sak som en spricka", "jag tittade i bra ljus innan jag valde skick"),
                "smartphone på ett bord nära ett nordiskt fönster, mjukt sidoljus",
            ),
            SlideBlueprint(
                "2. jag testade face id och kameran",
                ("utseendet berättar inte om allt fungerar", "några snabba tester gav en bättre bild"),
                "telefon bredvid glasögon och en enkel checklista, inga händer",
            ),
            SlideBlueprint(
                "3. jag kontrollerade laddningen",
                ("porten och kabeln behöver fungera som de ska", "det tog mindre än en minut att dubbelkolla"),
                "telefon och laddkabel på ett nattduksbord i en svensk lägenhet",
            ),
            SlideBlueprint(
                "4. jag tittade på batterihälsan",
                ("batteriet kan påverka hur mobilen bedöms", "jag skrev ner procenten i stället för att gissa"),
                "mobilskärm sedd på avstånd i en lugn hemmiljö, ingen läsbar text",
                "interface",
            ),
            SlideBlueprint(
                "5. jag valde hellre rätt än optimistiskt",
                ("ett preliminärt bud bygger på uppgifterna jag lämnar", "en ärlig beskrivning minskar överraskningar senare"),
                "telefon på en vikt handduk bredvid en penna och anteckningsbok",
            ),
        ),
    ),
    TopicBlueprint(
        key="one-offer-context",
        category="jamforelse",
        title="5 skäl till att ett enda bud inte gav mig hela bilden",
        caption="Ett bud visar vad en uppköpare erbjuder. Flera bud ger ett bättre beslutsunderlag innan du väljer.",
        cta="jämför först. välj sedan.",
        slides=(
            SlideBlueprint(
                "1. en siffra saknade sammanhang",
                ("jag kunde inte se om budet låg högt eller lågt", "det blev tydligare först när jag såg alternativen"),
                "ett ensamt neutralt priskort på en laptop i ett dämpat hem",
                "interface",
            ),
            SlideBlueprint(
                "2. uppköpare kan värdera olika",
                ("lager och efterfrågan behöver inte se likadana ut", "samma mobil kan därför få olika bud"),
                "tre neutrala kort på ett bord, abstrakt och utan läsbar text",
            ),
            SlideBlueprint(
                "3. skicket måste vara jämförbart",
                ("modell och lagring räcker inte alltid", "jag använde samma skickbeskrivning för varje alternativ"),
                "äldre telefon fotograferad rakt ovanifrån på linnetyg",
            ),
            SlideBlueprint(
                "4. villkoren var också en del av valet",
                ("frakt, kontroll och utbetalning kan skilja sig", "priset var början på jämförelsen, inte slutet"),
                "kuvert, telefon och enkel utskriven checklista på ett köksbord",
            ),
            SlideBlueprint(
                "5. jag behövde inte välja direkt",
                ("jämförelsen gav mig överblick", "sedan kunde jag läsa vidare hos den uppköpare jag övervägde"),
                "person sedd bakifrån med kaffe vid ett fönster, telefon på bordet",
                "person_far",
            ),
        ),
    ),
    TopicBlueprint(
        key="battery-health",
        category="skick",
        title="5 saker batterihälsan berättade om min gamla iPhone",
        caption="Batterihälsan är en del av helheten. Modell, lagring, skick och funktion påverkar också hur mobilen bedöms.",
        cta="kolla helheten innan du jämför.",
        slides=(
            SlideBlueprint(
                "1. procenten var bara en del",
                ("batteriet spelade roll men avgjorde inte allt", "modell, lagring och övrigt skick behövde också stämma"),
                "telefon och batterisymbol formad av vardagsföremål, diskret stilleben",
            ),
            SlideBlueprint(
                "2. känslan räckte inte som kontroll",
                ("att mobilen kändes trött var inte särskilt exakt", "jag öppnade inställningarna och kollade"),
                "telefon på ett nattduksbord i mjukt morgonljus",
            ),
            SlideBlueprint(
                "3. laddningen behövde också fungera",
                ("ett batterivärde säger inget om porten", "jag testade både kabel och trådlös laddning"),
                "telefon bredvid laddkabel och laddplatta, inga händer",
            ),
            SlideBlueprint(
                "4. jag slutade gissa på skicket",
                ("en konkret kontroll gjorde frågorna enklare", "det blev lättare att jämföra likvärdiga bud"),
                "checklista och telefon på ett skrivbord, nordisk eftermiddagsbelysning",
            ),
            SlideBlueprint(
                "5. slutpriset krävde fortfarande kontroll",
                ("mitt svar gav ett preliminärt bud", "uppköparen behövde fortfarande undersöka mobilen"),
                "telefon bredvid en stängd återanvändbar fraktkartong",
            ),
        ),
    ),
    TopicBlueprint(
        key="before-shipping",
        category="trygghet",
        title="5 saker jag gjorde innan min gamla iPhone lämnade hemmet",
        caption="Säkerhetskopiera, logga ut och kontrollera villkoren innan du skickar mobilen till en uppköpare.",
        cta="förbered mobilen i lugn och ro.",
        slides=(
            SlideBlueprint(
                "1. jag gjorde en sista säkerhetskopia",
                ("bilder och anteckningar var viktigare än själva telefonen", "jag kontrollerade att allt fanns kvar på den nya enheten"),
                "två telefoner sida vid sida på ett ljust skrivbord, inga händer",
            ),
            SlideBlueprint(
                "2. jag loggade ut från mina konton",
                ("jag tog bort kopplingen till mitt apple-konto", "sedan stängde jag av hitta min iphone"),
                "telefon och nyckelknippa på en lugn hallbyrå",
            ),
            SlideBlueprint(
                "3. jag raderade innehållet",
                ("först efter säkerhetskopian återställde jag mobilen", "då kunde nästa person börja från början"),
                "nollställd telefon på ett vikt tyg, skärmen utan läsbar text",
            ),
            SlideBlueprint(
                "4. jag dokumenterade skicket",
                ("några enkla bilder visade hur mobilen såg ut", "det gav mig bättre koll före frakten"),
                "telefon fotograferad på ett rent bord bredvid en liten kamera",
            ),
            SlideBlueprint(
                "5. jag läste fraktvillkoren",
                ("jag kontrollerade emballage, retur och vad som händer efter kontroll", "sedan packade jag utan brådska"),
                "telefon bredvid bubbelkuvert och tejp, inga händer",
            ),
        ),
    ),
    TopicBlueprint(
        key="preliminary-offer",
        category="trygghet",
        title="5 skäl till att det första budet fortfarande är preliminärt",
        caption="Det första budet bygger på dina uppgifter. Uppköparen fastställer slutpriset efter kontroll av modell, lagring, skick och funktion.",
        cta="jämför bud och läs slutvillkoren.",
        slides=(
            SlideBlueprint(
                "1. budet byggde på mina svar",
                ("ingen hade sett mobilen ännu", "därför var beskrivningen viktig redan från början"),
                "telefon bredvid ett enkelt formulär på laptop, ingen läsbar text",
                "interface",
            ),
            SlideBlueprint(
                "2. modellen behövde stämma",
                ("pro, plus och max är olika varianter", "jag dubbelkollade namnet i inställningarna"),
                "tre olika neutrala smartphone-silhuetter på ett bord",
            ),
            SlideBlueprint(
                "3. lagringen kunde ändra värdet",
                ("telefoner som ser likadana ut kan ha olika lagring", "jag kontrollerade siffran i stället för att minnas"),
                "telefon bredvid liten handskriven notering med endast abstrakta linjer",
            ),
            SlideBlueprint(
                "4. funktionsfel syns inte alltid",
                ("kamera, face id och laddning måste testas", "utseendet berättade inte hela historien"),
                "telefon bredvid kameraikon, laddkabel och hörlurar som stilleben",
            ),
            SlideBlueprint(
                "5. uppköparen gjorde slutkontrollen",
                ("först då kunde det slutliga priset fastställas", "jag läste villkoren innan jag valde"),
                "stängd fraktlåda på en enkel svensk hallbänk",
            ),
        ),
    ),
    TopicBlueprint(
        key="compare-without-selling",
        category="beslut",
        title="5 skäl att jämföra även om du inte vill sälja idag",
        caption="Du behöver inte vara redo att sälja för att vara redo att jämföra. Buden kan ändras över tid, men en jämförelse kan ge en första överblick.",
        cta="kolla läget utan att bestämma dig.",
        slides=(
            SlideBlueprint(
                "1. jag ville bara förstå läget",
                ("ett värde var lättare att förhålla sig till än en gissning", "jag behövde inte fatta beslut samma dag"),
                "äldre telefon på ett sidobord bredvid en bok och kaffe",
            ),
            SlideBlueprint(
                "2. uppgraderingen låg längre fram",
                ("jag funderade på en ny telefon men hade inte bestämt mig", "en jämförelse gav mig ett ungefärligt underlag"),
                "två telefoner på en neutral säng, vardaglig svensk miljö",
            ),
            SlideBlueprint(
                "3. reservmobilen hade ett alternativ",
                ("den kunde ligga kvar eller få ett nytt liv", "jag ville veta vad valet faktiskt innebar"),
                "telefon i en öppen låda bredvid vardagsföremål",
            ),
            SlideBlueprint(
                "4. buden kunde förändras",
                ("jämförelsen var en ögonblicksbild, inte ett löfte", "jag visste att jag behövde kontrollera igen senare"),
                "kalender, telefon och penna på ett träbord",
            ),
            SlideBlueprint(
                "5. jag behöll kontrollen över beslutet",
                ("ingen jämförelse tvingade mig att sälja", "jag kunde välja att gå vidare eller vänta"),
                "person sedd på avstånd vid ett köksbord, telefon liggande bredvid",
                "person_far",
            ),
        ),
    ),
    TopicBlueprint(
        key="same-looking-phones",
        category="modell",
        title="5 detaljer som gjorde två likadana iPhones helt olika",
        caption="Modellnamnet är bara början. Variant, lagring, batteri, skick och funktion kan påverka jämförelsen.",
        cta="kontrollera detaljerna först.",
        slides=(
            SlideBlueprint(
                "1. modellvarianten skilde sig",
                ("pro, plus och max kan vara lätta att blanda ihop", "jag kollade det exakta namnet i inställningarna"),
                "två smartphones i olika storlek på ett linnetyg",
            ),
            SlideBlueprint(
                "2. lagringen syntes inte utanpå",
                ("utseendet sa inget om hur mycket plats mobilen hade", "jag behövde kontrollera siffran"),
                "telefon bredvid diskreta minneskortsliknande former, inga märken",
            ),
            SlideBlueprint(
                "3. skicket handlade om mer än repor",
                ("en hel skärm kunde fortfarande dölja funktionsfel", "jag testade knappar, kamera och laddning"),
                "telefon med laddkabel, hörlurar och kamera som ordnat stilleben",
            ),
            SlideBlueprint(
                "4. batteriet gav mer sammanhang",
                ("två annars lika mobiler kunde ha olika batterihälsa", "det blev en del av helhetsbedömningen"),
                "två telefoner bredvid varsin enkel batteriform, abstrakt",
            ),
            SlideBlueprint(
                "5. samma modellnamn räckte inte",
                ("först med rätt uppgifter blev buden jämförbara", "det gjorde beslutet betydligt lugnare"),
                "anteckningsbok med fem enkla bockar bredvid en telefon",
            ),
        ),
    ),
    TopicBlueprint(
        key="upgrade-decision",
        category="timing",
        title="5 frågor jag ställde innan jag uppgraderade min iPhone",
        caption="En ny telefon är ett större beslut än bara modell och färg. Kolla behov, kostnad och vad den gamla mobilen kan vara värd.",
        cta="skaffa överblick före uppgraderingen.",
        slides=(
            SlideBlueprint(
                "1. vad fungerade faktiskt dåligt",
                ("jag försökte skilja behov från nyhetskänsla", "batteri, kamera och lagring fick varsin ärlig kontroll"),
                "äldre telefon på ett vardagligt köksbord, mjukt kvällsljus",
            ),
            SlideBlueprint(
                "2. behövde jag köpa just nu",
                ("en ny modell betydde inte automatiskt att min gamla var obrukbar", "jag gav beslutet några dagar"),
                "telefon bredvid en enkel kalender och kaffe",
            ),
            SlideBlueprint(
                "3. vad skulle den gamla mobilen göra",
                ("reservmobil lät bra men jag hade redan en", "jag funderade på om någon annan kunde använda den"),
                "två äldre telefoner i en prydlig tekniklåda",
            ),
            SlideBlueprint(
                "4. vad kunde den vara värd",
                ("jag ville förstå alternativen före köpet", "flera bud gav mer sammanhang än en ensam siffra"),
                "laptop och telefon i ett hemmakontor, ingen läsbar skärmtext",
                "interface",
            ),
            SlideBlueprint(
                "5. vilket beslut kändes lugnast",
                ("jag behövde inte maximera varje detalj", "jag behövde bara ha tillräckligt bra koll"),
                "person sedd bakifrån vid ett fönster i en vanlig svensk lägenhet",
                "person_far",
            ),
        ),
    ),
    TopicBlueprint(
        key="price-is-not-everything",
        category="jamforelse",
        title="5 saker jag jämförde utöver själva budet",
        caption="Två bud kan ligga nära varandra men ha olika villkor. Kontrollera hela erbjudandet hos uppköparen innan du väljer.",
        cta="jämför pris och villkor.",
        slides=(
            SlideBlueprint(
                "1. hur mobilen skulle skickas",
                ("gratis frakt och betald frakt gav olika slutresultat", "jag kontrollerade vad som faktiskt ingick"),
                "mobil bredvid två olika neutrala fraktkuvert",
            ),
            SlideBlueprint(
                "2. vad som hände efter kontrollen",
                ("jag ville veta hur ett ändrat bud hanterades", "returvillkoren var en del av beslutet"),
                "telefon, förstoringsglas och enkel checklista som stilleben",
            ),
            SlideBlueprint(
                "3. hur utbetalningen fungerade",
                ("bank, swish och andra alternativ kunde skilja sig", "jag valde inte förrän jag förstått stegen"),
                "telefon bredvid plånbok och bankkort utan synliga märken",
            ),
            SlideBlueprint(
                "4. hur lång tid processen tog",
                ("det högsta budet var inte min enda prioritet", "jag behövde också förstå när allt blev klart"),
                "enkel klocka, telefon och fraktkartong på ett bord",
            ),
            SlideBlueprint(
                "5. vem jag faktiskt ville gå vidare med",
                ("priset öppnade jämförelsen", "villkoren hjälpte mig att avsluta den"),
                "person sedd på avstånd som läser vid ett köksbord, telefon bredvid",
                "person_far",
            ),
        ),
    ),
    TopicBlueprint(
        key="ten-minute-check",
        category="praktiskt",
        title="5 kontroller som tog mindre än tio minuter",
        caption="En snabb kontroll av modell, lagring, batteri och funktion gör det lättare att beskriva mobilen rättvist.",
        cta="kontrollera. jämför. välj.",
        slides=(
            SlideBlueprint(
                "1. exakt modell",
                ("jag öppnade inställningarna i stället för att gissa", "där stod vilket modellnamn jag faktiskt hade"),
                "telefon bredvid en enkel etikett och anteckningsbok",
            ),
            SlideBlueprint(
                "2. lagring",
                ("telefoner med samma utsida kan ha olika lagring", "siffran tog några sekunder att kontrollera"),
                "telefon och abstrakta lagringsblock på ett skrivbord",
            ),
            SlideBlueprint(
                "3. batterihälsa",
                ("jag skrev ner procenten som visades", "det gav en tydligare bild än magkänslan"),
                "telefon på nattduksbord med laddare, ingen läsbar text",
            ),
            SlideBlueprint(
                "4. kamera, face id och knappar",
                ("jag testade det jag använder varje dag", "små fel var lättare att upptäcka när jag letade efter dem"),
                "telefon bredvid kamera och hörlurar som lugnt stilleben",
            ),
            SlideBlueprint(
                "5. repor, sprickor och ram",
                ("jag tittade i bra ljus från flera håll", "sedan kunde jag beskriva skicket mer rättvist"),
                "telefon på ljust tyg nära ett stort nordiskt fönster",
            ),
        ),
    ),
    TopicBlueprint(
        key="old-phone-myths",
        category="myter",
        title="5 saker jag hade fel om när jag skulle sälja min gamla iPhone",
        caption="Det är lätt att gissa om värde, skick och process. Några kontroller och flera bud ger en bättre överblick.",
        cta="byt gissningar mot överblick.",
        slides=(
            SlideBlueprint(
                "1. att gamla mobiler saknade värde",
                ("åldern var viktig men inte det enda", "modell, lagring och skick behövde också vägas in"),
                "äldre telefon på en hylla bland böcker och vardagsföremål",
            ),
            SlideBlueprint(
                "2. att alla bud skulle vara lika",
                ("olika uppköpare kunde göra olika bedömningar", "en jämförelse gav mig sammanhanget"),
                "flera neutrala kortformer bredvid en telefon",
            ),
            SlideBlueprint(
                "3. att en repa betydde trasig",
                ("kosmetiska märken och funktionsfel var olika saker", "jag kontrollerade vad som faktiskt fungerade"),
                "telefon i sidoljus där små vardagliga märken kan anas",
            ),
            SlideBlueprint(
                "4. att jag behövde bestämma mig direkt",
                ("jag kunde jämföra utan att sälja samma dag", "det gjorde processen mindre stressig"),
                "person sedd bakifrån med telefon liggande på ett bord",
                "person_far",
            ),
            SlideBlueprint(
                "5. att första budet var slutpriset",
                ("budet byggde på mina uppgifter", "uppköparens kontroll återstod fortfarande"),
                "telefon bredvid en enkel kontrollista och fraktkuvert",
            ),
        ),
    ),
    TopicBlueprint(
        key="family-phone-drawer",
        category="vardagsberattelse",
        title="5 fynd från familjens låda med gamla mobiler",
        caption="Gamla telefoner samlas lätt på hög. Sortera modell, ägare, skick och vilka som faktiskt behöver sparas.",
        cta="börja med en telefon i taget.",
        slides=(
            SlideBlueprint(
                "1. en mobil ingen mindes lösenkoden till",
                ("den hade följt med genom flera flyttar", "först behövde vi ta reda på vem som använt den"),
                "flera äldre telefoner i en vardaglig svensk kökslåda",
            ),
            SlideBlueprint(
                "2. två så kallade reservmobiler",
                ("ingen av dem hade varit påslagen på länge", "vi behövde inte spara båda för säkerhets skull"),
                "två äldre telefoner bredvid laddkablar på ett bord",
            ),
            SlideBlueprint(
                "3. en telefon med bättre skick än väntat",
                ("skalet såg slitet ut men mobilen under var hel", "vi tog av det och kontrollerade ordentligt"),
                "äldre telefon och avtaget neutralt mobilskal på linnetyg",
            ),
            SlideBlueprint(
                "4. laddare till modeller vi inte längre hade",
                ("lådan var full av gamla beslut", "vi sorterade tillbehören efter det vi faktiskt använder"),
                "ordnade laddkablar och adaptrar i små lådor",
            ),
            SlideBlueprint(
                "5. en enkel ordning för resten",
                ("behåll, återvinn eller jämför bud", "varje telefon fick ett tydligt nästa steg"),
                "tre neutrala sorteringshögar på ett matbord",
            ),
        ),
    ),
    TopicBlueprint(
        key="avoid-surprises",
        category="trygghet",
        title="5 sätt jag minskade risken för överraskningar efter budet",
        caption="Rätt modell, ärligt skick och tydliga villkor gör det preliminära budet lättare att förstå.",
        cta="gör kontrollen före valet.",
        slides=(
            SlideBlueprint(
                "1. jag dubbelkollade modell och lagring",
                ("de uppgifterna syntes inte alltid på utsidan", "jag hämtade dem direkt från inställningarna"),
                "telefon bredvid anteckningsbok med två enkla kontrollrader",
            ),
            SlideBlueprint(
                "2. jag skilde repor från sprickor",
                ("ett kosmetiskt märke var inte samma sak som en skadad skärm", "bra ljus gjorde skillnaden tydligare"),
                "telefon fotograferad i mjukt sidoljus på ett rent bord",
            ),
            SlideBlueprint(
                "3. jag testade funktionerna",
                ("kamera, knappar och laddning behövde fungera", "jag litade inte bara på hur mobilen såg ut"),
                "telefon bredvid kamera, kabel och hörlurar som stilleben",
            ),
            SlideBlueprint(
                "4. jag läste vad kontrollen innebar",
                ("uppköparen behövde fortfarande undersöka mobilen", "jag tog reda på vad som hände om budet ändrades"),
                "enkel villkorssida på laptop, texten oläslig, telefon bredvid",
                "interface",
            ),
            SlideBlueprint(
                "5. jag sparade dokumentationen",
                ("några bilder och anteckningar gav mig bättre koll", "sedan kunde jag gå vidare lugnare"),
                "telefon, kamera och liten anteckningsbok på träbord",
            ),
        ),
    ),
    TopicBlueprint(
        key="small-decision",
        category="beslut",
        title="5 sätt jag gjorde mobilförsäljningen till ett mindre beslut",
        caption="Dela upp processen: kontrollera mobilen, jämför bud och välj först när du förstår alternativen.",
        cta="ett steg i taget räcker.",
        slides=(
            SlideBlueprint(
                "1. jag började med modellnamnet",
                ("inte med vilken uppköpare jag skulle välja", "en konkret detalj gjorde starten enklare"),
                "telefon och ett litet anteckningskort på ett sidobord",
            ),
            SlideBlueprint(
                "2. sedan tog jag lagringen",
                ("nästa fråga hade bara ett tydligt svar", "jag behövde inte lösa allt på en gång"),
                "telefon bredvid abstrakta kuber i olika storlekar",
            ),
            SlideBlueprint(
                "3. jag kontrollerade skicket lugnt",
                ("skärm, ram, batteri och funktion fick varsin minut", "det blev mindre att hålla i huvudet"),
                "telefon på tyg bredvid en enkel fempunktslista",
            ),
            SlideBlueprint(
                "4. först därefter jämförde jag bud",
                ("flera alternativ gav mig överblick", "jag behövde fortfarande inte välja direkt"),
                "laptop med neutrala kort och telefon bredvid, ingen läsbar text",
                "interface",
            ),
            SlideBlueprint(
                "5. beslutet fick komma sist",
                ("kontrollera, jämför, välj", "tre små steg kändes lättare än ett stort"),
                "tre enkla objekt i rad på ett lugnt skrivbord",
            ),
        ),
    ),
)


def _apply_natural_copy(topic: TopicBlueprint) -> TopicBlueprint:
    copy = NATURAL_COPY.get(topic.key)
    if not copy:
        raise RuntimeError(f"Natural copy saknas för ämnet {topic.key}")

    slide_copy = copy["slides"]
    if not isinstance(slide_copy, tuple) or len(slide_copy) != len(topic.slides):
        raise RuntimeError(f"Fel antal copy-slides för ämnet {topic.key}")

    slides = tuple(
        SlideBlueprint(
            heading=heading,
            body=body,
            scene=visual.scene,
            visual_type=visual.visual_type,
        )
        for visual, (heading, body) in zip(topic.slides, slide_copy)
    )
    return TopicBlueprint(
        key=topic.key,
        category=topic.category,
        title=str(copy["title"]),
        caption=str(copy["caption"]),
        cta=str(copy["cta"]),
        slides=slides,
    )


TOPICS = tuple(_apply_natural_copy(topic) for topic in TOPICS)
