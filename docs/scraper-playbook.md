# Scraper-playbook for CashMyPhone

Den här filen är en praktisk checklista för hur vi lägger till en ny återförsäljare.

## Steg for att hitta prismodellen

1. Borja med saljsidan, inte webbshoppen. Testa vanliga URL:er som `/salj-din-mobil`, `/salj-din-iphone`, `/sell`, och sok pa Google med `site:domän sälj iPhone prisuppskattning`.
2. Curla huvudsidan med `curl -L` och spara HTML till `/private/tmp`. Manga sajter redirectar eller cachar olika versioner.
3. Leta efter formularet i HTML: `rg "form|select|data-price|price|condition|model|storage|api|ajax|wp-json|admin-ajax"`.
4. Om sidan ar en SPA/widget, leta efter script, tenant-id, nonce eller API-bas. PhoneHero lag i Livewire-state. reNewed lag i Reusely-widgetens API med `x-tenant-id`.
5. Om sajten visar kategori-steg, prova query-parametrarna som klicklankarna pekar pa. Fixiphone dolde modellkort tills man curlade `?child-cat=iphone&parent-cat=apple#scroll-section`.
6. Nar priserna hittas, identifiera modell, lagring, skicknyckel och avrundning. Halla condition-nycklar korta sa DB-kolumnen inte overflowar.
7. Verifiera med 1-2 manuella kombinationer mot hemsidan innan deploy.

## Vanliga problem och losningar

- **Tomma priser i prod:** Koden kan vara deployad men DB saknar rader. Kor `POST /api/scrape?retailer=...&sync=true` pa Railway och kontrollera `/api/retailers`.
- **Retailer syns i `/api/prices` men inte pa CashMyPhone.se:** Kontrollera `app/pricing/crosswalk.py`. `/api/quote` visar bara handlare vars condition-nyckel matchar frontend-svaren.
- **Fel pris fast scraper fungerar:** Kontrollera displayavrundning. PhoneHero visade avrundade priser, sa vi sparade deras displaypris med ceil till narmaste tiotal.
- **DB-fel `value too long for type character varying(100)`:** Condition-nyckeln ar for lang. Komprimera nycklarna, exempelvis `screen=nyskick` till `s=n`.
- **Bakgrundsscrape visar inget direkt:** Anvand `sync=true` under felsokning sa curl-svaret innehaller felmeddelandet.

## Hur en scraper far synas pa CashMyPhone.se

1. Skapa `app/scrapers/{retailer}.py` som returnerar listor med `model`, `storage_gb`, `condition`, `price_sek`, `url`.
2. Registrera scrapern i `app/scrapers/__init__.py`.
3. Lagg till mapping i `app/pricing/crosswalk.py` sa frontendens formularsvar blir ratt condition-nyckel.
4. Kor `python -m compileall app`.
5. Scrapea lokalt eller i prod. Efter prod-scrape ska `/api/retailers` inkludera handlaren.
6. Testa `/api/quote?model=...&storage_gb=...` med ett riktigt formularpayload, eftersom hemsidan anvander `/api/quote` snarare an bara `/api/prices`.
7. Om frontend har en hardkodad retailer-lista, lagg till namn/metadata dar ocksa. Backend kan fungera aven om Lovable inte visar handlaren snyggt.

## Fixiphone-fynd 2026-05-27

Fixiphone ar WordPress for saljsidan och Magento for webbshop/reparationer. Webbshoppen innehaller reparationspriser och ska inte anvandas som buyback-priser.

Ratt salj-URL for iPhone-priser ar:

```text
https://www.fixiphone.se/salj-din-mobil/?child-cat=iphone&parent-cat=apple#scroll-section
```

Modellkorten ligger i HTML under `.popupInformation .pro-details`. Varje kort har:

- `input[name="product-name"]` for modellnamn.
- `.product-price`-knappar med `data-price` och lagringstext.
- Fragesvar med `data-val`.

Fixiphones egna JS raknar:

```text
ovre pris  = baspris - (baspris / 100) * avdrag
nedre pris = baspris - floor(baspris / 70) * avdrag
```

Avdrag:

- Telefonen fungerar inte normalt: `45`
- Skarmens farg ar inte jamn: `45`
- Repor/bucklor: `0`, `10` eller `20`
- Nagon glasdel trasig: `45`
- Bojd/vattenskadad/Face ID eller Touch ID trasig: `90`

Vi lagrar nedre priset for skadade kombinationer, eftersom Fixiphone visar intervall och CashMyPhone visar ett enda bud. For perfekt skick blir priset exakt baspriset.
