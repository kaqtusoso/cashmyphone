"""Human-written Swedish copy for Televera's social slideshows.

The visual blueprints live in ``topics.py``. Keeping the copy separate makes it
possible to sharpen the voice without accidentally changing image direction.
"""

NATURAL_COPY: dict[str, dict[str, object]] = {
    "tech-drawer": {
        "title": "5 saker som fick mig att rensa mobillådan",
        "caption": (
            "Jag hade en gammal iPhone som bara låg. När jag väl kollade buden "
            "tog hela grejen mycket mindre tid än jag trodde."
        ),
        "cta": "Jämför bud på din iPhone på televera.se – du behöver inte sälja för att kolla.",
        "slides": (
            (
                "1. reservmobilen var mest en ursäkt",
                (
                    "den hade legat avstängd sedan jag köpte min nya mobil",
                    "jag hade inte saknat den en enda gång",
                ),
            ),
            (
                "2. jag trodde den var värd typ ingenting",
                (
                    "så jag kollade innan jag slängde den",
                    "det visade sig faktiskt finnas flera bud",
                ),
            ),
            (
                "3. jag jämförde på Televera",
                (
                    "jag fyllde i modell, lagring och skick",
                    "sedan såg jag flera uppköpares bud på samma ställe",
                ),
            ),
            (
                "4. jag behövde inte bestämma mig direkt",
                (
                    "det var skönt att bara kunna kolla läget",
                    "inget hände förrän jag själv valde att gå vidare",
                ),
            ),
            (
                "5. hela grejen tog kanske tio minuter",
                (
                    "det jobbigaste hade varit att börja",
                    "nu vet jag vad mobilen är värd och lådan är tom",
                ),
            ),
        ),
    },
    "describe-condition": {
        "title": "5 grejer jag kollade innan jag valde skick",
        "caption": (
            "Jag trodde först att skicket bara handlade om repor. Det var några "
            "små tester till som gjorde buden mycket lättare att jämföra."
        ),
        "cta": "Kolla mobilen och jämför bud på televera.se.",
        "slides": (
            (
                "1. repa och spricka är inte samma sak",
                (
                    "jag tände lampan och vinklade skärmen",
                    "det syntes mycket bättre än i vanligt soffljus",
                ),
            ),
            (
                "2. jag testade det jag faktiskt använder",
                (
                    "kamera, face id, högtalare och knappar",
                    "allt tog typ två minuter",
                ),
            ),
            (
                "3. jag satte i laddaren också",
                (
                    "en snygg mobil kan fortfarande ha en trött laddport",
                    "bättre att upptäcka det hemma",
                ),
            ),
            (
                "4. jag kollade batterihälsan",
                (
                    "inte för att försöka gissa ett pris",
                    "utan för att beskriva mobilen rätt från början",
                ),
            ),
            (
                "5. sedan jämförde jag på Televera",
                (
                    "samma modell och skick hos flera uppköpare",
                    "mycket smidigare än att öppna tio olika sajter",
                ),
            ),
        ),
    },
    "one-offer-context": {
        "title": "5 skäl till att jag inte tog första bästa bud",
        "caption": (
            "Det första budet såg helt okej ut. Problemet var bara att jag inte "
            "hade något att jämföra det med."
        ),
        "cta": "Se flera bud för samma iPhone på televera.se.",
        "slides": (
            (
                "1. ett enda bud sa mig nästan ingenting",
                (
                    "det kunde vara bra eller ganska lågt",
                    "jag hade ingen aning när jag bara såg en siffra",
                ),
            ),
            (
                "2. jag kollade samma mobil på Televera",
                (
                    "där såg jag bud från flera uppköpare bredvid varandra",
                    "skillnaden var större än jag hade väntat mig",
                ),
            ),
            (
                "3. jag använde exakt samma skick",
                (
                    "annars jämför man ju inte samma sak",
                    "modell, lagring och skick fick vara identiska",
                ),
            ),
            (
                "4. sedan läste jag villkoren",
                (
                    "frakt, kontroll och retur kunde skilja sig",
                    "det högsta budet var inte automatiskt bäst för mig",
                ),
            ),
            (
                "5. först då valde jag vem jag ville gå vidare med",
                (
                    "jag tog inte första bästa",
                    "jag tog det alternativ som faktiskt passade mig",
                ),
            ),
        ),
    },
    "battery-health": {
        "title": "5 saker jag kollade när batteriet kändes segt",
        "caption": (
            "Batterihälsan var viktig, men den berättade inte allt om mobilen. "
            "Det märkte jag först när jag gick igenom resten också."
        ),
        "cta": "Fyll i skick och batteri och jämför bud på televera.se.",
        "slides": (
            (
                "1. procenten var inte hela svaret",
                (
                    "batterihälsan sa en del",
                    "men modell, lagring och resten av skicket spelade också roll",
                ),
            ),
            (
                "2. jag slutade gå på magkänsla",
                (
                    "att mobilen kändes seg var inte särskilt exakt",
                    "jag öppnade inställningarna och kollade siffran",
                ),
            ),
            (
                "3. laddningen fick ett eget test",
                (
                    "batteriprocenten säger inget om laddporten",
                    "så jag testade både kabel och trådlös laddning",
                ),
            ),
            (
                "4. jag fyllde i allt på Televera",
                (
                    "modell, lagring, batteri och skick",
                    "sedan kunde jag jämföra flera bud på samma uppgifter",
                ),
            ),
            (
                "5. budet var fortfarande preliminärt",
                (
                    "uppköparen behöver kontrollera mobilen först",
                    "det stod tydligt innan jag gick vidare",
                ),
            ),
        ),
    },
    "before-shipping": {
        "title": "5 saker jag gjorde innan jag skickade min iPhone",
        "caption": (
            "Det mesta tog bara några minuter, men jag ville vara helt säker på "
            "att bilder, konton och personliga saker var borta först."
        ),
        "cta": "Jämför bud på televera.se innan du väljer vart mobilen ska skickas.",
        "slides": (
            (
                "1. jag gjorde en sista backup",
                (
                    "bilderna var viktigare än själva mobilen",
                    "jag kollade att allt fanns på min nya telefon",
                ),
            ),
            (
                "2. jag loggade ut från apple-kontot",
                (
                    "sedan stängde jag av hitta min iphone",
                    "den delen ville jag verkligen inte glömma",
                ),
            ),
            (
                "3. först därefter raderade jag allt",
                (
                    "jag återställde mobilen till fabriksinställningarna",
                    "inga bilder, meddelanden eller konton fick följa med",
                ),
            ),
            (
                "4. jag tog bilder på skicket",
                (
                    "fram, bak, kanter och skärm",
                    "det kändes bra att ha kvar innan paketet åkte",
                ),
            ),
            (
                "5. jag jämförde innan jag packade",
                (
                    "på Televera såg jag bud från flera uppköpare",
                    "sedan läste jag villkoren hos den jag valde",
                ),
            ),
        ),
    },
    "preliminary-offer": {
        "title": "5 saker som kan ändra budet på din iPhone",
        "caption": (
            "Budet på skärmen bygger på det du fyller i. Därför dubbelkollade "
            "jag några saker innan jag valde uppköpare."
        ),
        "cta": "Jämför preliminära bud på televera.se och läs villkoren innan du väljer.",
        "slides": (
            (
                "1. ingen hade sett mobilen ännu",
                (
                    "budet byggde helt på mina svar",
                    "så jag försökte vara så exakt som möjligt",
                ),
            ),
            (
                "2. pro, plus och max är inte samma modell",
                (
                    "jag dubbelkollade namnet i inställningarna",
                    "det tog fem sekunder och kunde påverka budet",
                ),
            ),
            (
                "3. lagringen behövde också stämma",
                (
                    "två likadana mobiler kan ha olika mycket minne",
                    "jag kollade siffran i stället för att chansa",
                ),
            ),
            (
                "4. jag testade kamera, face id och laddning",
                (
                    "alla fel syns inte utanpå",
                    "det var bättre att skriva rätt direkt",
                ),
            ),
            (
                "5. på Televera jämförde jag samma uppgifter",
                (
                    "då såg jag flera preliminära bud bredvid varandra",
                    "slutpriset bestäms först efter uppköparens kontroll",
                ),
            ),
        ),
    },
    "compare-without-selling": {
        "title": "5 skäl att kolla värdet även om du inte ska sälja",
        "caption": (
            "Jag var inte redo att sälja. Jag ville bara veta vad mobilen kunde "
            "vara värd innan jag bestämde mig för nästa steg."
        ),
        "cta": "Kolla flera bud på televera.se – du behöver inte sälja för att jämföra.",
        "slides": (
            (
                "1. jag var mest nyfiken",
                (
                    "mobilen låg ändå bara i en låda",
                    "jag ville veta om den var värd att spara",
                ),
            ),
            (
                "2. jag funderade på att uppgradera",
                (
                    "men jag hade inte bestämt modell eller datum",
                    "värdet på den gamla mobilen var ändå bra att känna till",
                ),
            ),
            (
                "3. reservmobil lät bättre än det fungerade",
                (
                    "jag hade redan en annan mobil i reserv",
                    "den här hade inte varit påslagen på månader",
                ),
            ),
            (
                "4. jag kollade buden på Televera",
                (
                    "det gick att jämföra utan att lova bort mobilen",
                    "jag kunde bara stänga sidan och tänka vidare",
                ),
            ),
            (
                "5. beslutet var fortfarande helt mitt",
                (
                    "bud kan ändras och jag kunde kolla igen senare",
                    "men nu hade jag åtminstone en riktig siffra",
                ),
            ),
        ),
    },
    "same-looking-phones": {
        "title": "5 detaljer som gjorde två likadana iPhones olika",
        "caption": (
            "De såg nästan identiska ut på bordet. När jag kollade detaljerna "
            "var det ganska tydligt varför buden skilde sig."
        ),
        "cta": "Fyll i rätt variant på televera.se och jämför bud för just din mobil.",
        "slides": (
            (
                "1. den ena var pro och den andra vanlig",
                (
                    "på håll såg de nästan likadana ut",
                    "modellnamnet i inställningarna gav svaret direkt",
                ),
            ),
            (
                "2. lagringen syntes inte utanpå",
                (
                    "den ena hade dubbelt så mycket utrymme",
                    "det upptäckte jag först när jag kollade siffran",
                ),
            ),
            (
                "3. hel skärm betydde inte felfri mobil",
                (
                    "kamera och laddning behövde fortfarande testas",
                    "några snabba tryck räckte",
                ),
            ),
            (
                "4. batterihälsan skilde sig rejält",
                (
                    "det förklarade varför den ena kändes mycket piggare",
                    "utseendet hade inte avslöjat det",
                ),
            ),
            (
                "5. på Televera fyllde jag i varje mobil för sig",
                (
                    "rätt modell, lagring, batteri och skick",
                    "då blev buden faktiskt jämförbara",
                ),
            ),
        ),
    },
    "upgrade-decision": {
        "title": "5 frågor jag ställde innan jag köpte ny iPhone",
        "caption": (
            "Jag var nära att uppgradera bara för att en ny modell hade kommit. "
            "De här frågorna gjorde beslutet betydligt enklare."
        ),
        "cta": "Kolla vad din gamla iPhone kan vara värd på televera.se.",
        "slides": (
            (
                "1. vad är det som faktiskt stör mig",
                (
                    "batteriet, kameran eller bara känslan av att vilja ha nytt",
                    "svaret var inte lika självklart som jag trodde",
                ),
            ),
            (
                "2. behöver jag köpa den just nu",
                (
                    "min gamla mobil fungerade fortfarande",
                    "jag gav det några dagar innan jag beställde något",
                ),
            ),
            (
                "3. vad ska hända med den gamla",
                (
                    "reservmobil var inget bra svar eftersom jag redan hade en",
                    "jag ville inte skapa ännu en mobil i lådan",
                ),
            ),
            (
                "4. jag kollade värdet på Televera",
                (
                    "där kunde jag jämföra flera uppköpares bud",
                    "det gjorde kostnaden för uppgraderingen lättare att räkna på",
                ),
            ),
            (
                "5. skulle jag fortfarande vilja byta efter det",
                (
                    "ibland var svaret ja och ibland nej",
                    "men nu var det ett genomtänkt beslut",
                ),
            ),
        ),
    },
    "price-is-not-everything": {
        "title": "5 saker jag kollade utöver själva budet",
        "caption": (
            "Två bud låg nästan på samma nivå, men villkoren var inte alls "
            "identiska. Det här avgjorde för mig."
        ),
        "cta": "Jämför bud på televera.se och läs sedan villkoren hos uppköparen.",
        "slides": (
            (
                "1. vem betalade frakten",
                (
                    "gratis frakt var inte självklart överallt",
                    "jag kollade vad som faktiskt ingick",
                ),
            ),
            (
                "2. vad händer om budet ändras",
                (
                    "jag ville veta om mobilen kunde skickas tillbaka",
                    "och vem som i så fall stod för den kostnaden",
                ),
            ),
            (
                "3. hur pengarna betalades ut",
                (
                    "bankkonto eller swish spelade mindre roll för mig",
                    "men jag ville veta hur och när det skulle ske",
                ),
            ),
            (
                "4. hur lång tid allt kunde ta",
                (
                    "det högsta budet var inte min enda prioritet",
                    "en tydlig process var också värd något",
                ),
            ),
            (
                "5. Televera gav mig buden på ett ställe",
                (
                    "sedan öppnade jag uppköparnas villkor",
                    "det gjorde valet mycket enklare",
                ),
            ),
        ),
    },
    "ten-minute-check": {
        "title": "5 snabba kontroller innan jag jämförde bud",
        "caption": (
            "Jag trodde det skulle bli ett projekt. I verkligheten tog det "
            "ungefär tio minuter att få fram allt jag behövde."
        ),
        "cta": "Ha uppgifterna redo och jämför bud på televera.se.",
        "slides": (
            (
                "1. exakt modell",
                (
                    "jag öppnade inställningarna i stället för att gissa",
                    "pro, plus och max är lättare att blanda ihop än man tror",
                ),
            ),
            (
                "2. hur mycket lagring den hade",
                (
                    "det syns inte på utsidan",
                    "men siffran stod på samma ställe som modellnamnet",
                ),
            ),
            (
                "3. batterihälsan",
                (
                    "jag skrev ner procenten som faktiskt stod där",
                    "inte vad batteriet kändes som",
                ),
            ),
            (
                "4. kamera, face id, knappar och laddning",
                (
                    "jag tryckte igenom allt en gång",
                    "små fel var mycket lättare att upptäcka då",
                ),
            ),
            (
                "5. sedan fyllde jag i allt på Televera",
                (
                    "några klick senare såg jag flera bud",
                    "klart enklare än att kolla varje uppköpare separat",
                ),
            ),
        ),
    },
    "old-phone-myths": {
        "title": "5 saker jag hade helt fel om när jag skulle sälja mobilen",
        "caption": (
            "Jag hade tydligen byggt hela min bild på gissningar. Några minuter "
            "senare såg det ganska annorlunda ut."
        ),
        "cta": "Byt gissningen mot flera riktiga bud på televera.se.",
        "slides": (
            (
                "1. att en gammal mobil knappt är värd något",
                (
                    "åldern var bara en del av det",
                    "modell, lagring och skick gjorde större skillnad än jag trodde",
                ),
            ),
            (
                "2. att alla skulle ge ungefär samma bud",
                (
                    "på Televera såg jag flera uppköpare bredvid varandra",
                    "buden var verkligen inte identiska",
                ),
            ),
            (
                "3. att en repa betyder trasig",
                (
                    "kosmetiska märken och funktionsfel är olika saker",
                    "min mobil fungerade trots några små repor",
                ),
            ),
            (
                "4. att jag behövde bestämma mig direkt",
                (
                    "jag kunde jämföra och fundera vidare",
                    "inget skickades någonstans bara för att jag kollade",
                ),
            ),
            (
                "5. att budet på skärmen var slutpriset",
                (
                    "det byggde på uppgifterna jag fyllde i",
                    "uppköparen behövde fortfarande kontrollera mobilen",
                ),
            ),
        ),
    },
    "family-phone-drawer": {
        "title": "5 saker vi hittade i familjens mobillåda",
        "caption": (
            "Vi skulle bara leta efter en laddare och råkade hitta flera års "
            "gamla mobiler. Så här sorterade vi dem."
        ),
        "cta": "Behåll, återvinn eller jämför bud på televera.se.",
        "slides": (
            (
                "1. en mobil ingen kom ihåg koden till",
                (
                    "den hade följt med genom minst två flyttar",
                    "först fick vi lista ut vem som ens hade använt den",
                ),
            ),
            (
                "2. två olika reservmobiler",
                (
                    "ingen av dem hade varit påslagen på länge",
                    "vi behövde kanske inte spara båda",
                ),
            ),
            (
                "3. en mobil som var fin under skalet",
                (
                    "skalet såg ärligt talat ganska trött ut",
                    "men telefonen under var i mycket bättre skick",
                ),
            ),
            (
                "4. laddare till mobiler vi inte längre ägde",
                (
                    "några gick till återvinning direkt",
                    "resten matchade vi med mobilerna som blev kvar",
                ),
            ),
            (
                "5. varje mobil fick ett nästa steg",
                (
                    "behålla, återvinna eller jämföra på Televera",
                    "plötsligt gick lådan faktiskt att stänga",
                ),
            ),
        ),
    },
    "avoid-surprises": {
        "title": "5 saker jag gjorde för att slippa ett ändrat bud",
        "caption": (
            "Jag kunde förstås inte garantera slutpriset, men jag kunde vara "
            "noggrann med uppgifterna innan mobilen skickades."
        ),
        "cta": "Beskriv mobilen rätt och jämför bud på televera.se.",
        "slides": (
            (
                "1. jag dubbelkollade modell och lagring",
                (
                    "det syntes inte på utsidan",
                    "så jag hämtade båda uppgifterna från inställningarna",
                ),
            ),
            (
                "2. jag skilde på repor och sprickor",
                (
                    "bra ljus gjorde det mycket lättare",
                    "jag försökte beskriva det jag faktiskt såg",
                ),
            ),
            (
                "3. jag testade funktionerna",
                (
                    "kamera, knappar, face id och laddning",
                    "utseendet säger inte om allt fungerar",
                ),
            ),
            (
                "4. jag läste vad en kontroll innebär",
                (
                    "budet kunde ändras om uppgifterna inte stämde",
                    "jag kollade också vad som hände då",
                ),
            ),
            (
                "5. först därefter jämförde jag på Televera",
                (
                    "alla bud byggde på samma uppgifter om mobilen",
                    "sedan valde jag vilken uppköpare jag ville läsa mer om",
                ),
            ),
        ),
    },
    "small-decision": {
        "title": "5 små steg som gjorde mobilförsäljningen enklare",
        "caption": (
            "Jag sköt upp det för att allt kändes som ett enda stort projekt. "
            "När jag delade upp det gick det mycket snabbare."
        ),
        "cta": "Börja med modellen och jämför sedan bud på televera.se.",
        "slides": (
            (
                "1. först tog jag reda på modellen",
                (
                    "inte vem jag skulle sälja till",
                    "bara exakt vilken iphone som låg framför mig",
                ),
            ),
            (
                "2. sedan kollade jag lagringen",
                (
                    "en uppgift i taget var mycket enklare",
                    "jag skrev ner siffran direkt",
                ),
            ),
            (
                "3. skärm, ram, batteri och funktion",
                (
                    "jag gav varje del någon minut",
                    "det blev mindre att försöka hålla i huvudet",
                ),
            ),
            (
                "4. sedan jämförde jag bud på Televera",
                (
                    "flera uppköpare dök upp för samma mobil",
                    "jag behövde fortfarande inte välja någon",
                ),
            ),
            (
                "5. beslutet fick komma sist",
                (
                    "först modell, sedan skick, sedan bud",
                    "mycket mindre dramatiskt än jag hade gjort det till",
                ),
            ),
        ),
    },
}
