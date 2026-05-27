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

- **Cloudflare blockerar API-anrop:** Prova curl-cffi med Chrome-impersonering innan Playwright. Swappie blev stabilare när primärvägen blev direkta API-anrop med `AsyncSession(impersonate="chrome136")` och Playwright bara används som fallback.
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

## FixPhonePro-fynd 2026-05-27

FixPhonePro ar WordPress/WooCommerce. Sjalva saljsidan ar inte Livewire som PhoneHero, utan en Elementor-sida dar hela prislistan och formeln ligger i inline-JS:

```text
https://fixphonepro.net/salj/
```

Leta efter `const MODELLER = [` och `function calculatePrice()`.

Datat innehaller `brand`, `name`, `storage` och `basePrice`. Endast `brand: "Apple"` anvands for CashMyPhone.

Deras formel:

```text
pris = basePrice
lagring: 16GB 0.8, 32GB 0.85, 64GB 0.9, 128GB 1.0, 256GB 1.1, 512GB 1.2, 1TB 1.3
skarm: Nyskick 1.0, Normalt sliten 0.9, Mycket sliten 0.7, Sprackt 0.4
baksida/ram: Nyskick 1.0, Normalt sliten 0.95, Mycket sliten 0.8, Sprackt 0.6
fel: Inget fel 1.0, valfritt fel 0.7
fungerar allt: Ja 1.0, Nej 0.5
batteri: minst 85% 1.0, lagre an 85% 0.9
visat pris = Math.round(max(100, pris))
```

Condition-nyckeln halls kort:

```text
s=n|b=n|d=no|f=y|bt=ok
```

Där `s` = screen, `b` = body, `d` = defect, `f` = functional och `bt` = battery.
