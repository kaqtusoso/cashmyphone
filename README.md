# CashMyPhone API

FastAPI-backend som hämtar inköpspriser för begagnade iPhones från svenska återförsäljare.

## Återförsäljare

| Återförsäljare | Metod | Status |
|---|---|---|
| PhoneHero | Livewire snapshot (`?model=slug`) + lokal kombinationsberäkning | ✅ Aktiv – 45 000+ skickskombinationer |
| FixPhonePro | Inline-JS från `/salj/` + lokal formelberäkning | ✅ Aktiv – iPhone-modeller/lagring/skick |
| reNewed | Reusely widget-API (`/v2/widget/catalog/...`) | ✅ Aktiv – iPhone-modeller/lagring/skick |
| HappyPhone | HTML-scraping (`/shop/sell/`) | ✅ Aktiv – 27+ priser |
| Telestore | HTML-scraping (`/salja-mobil/`) | ✅ Aktiv – 29+ priser |
| FixMyPhone | Playwright (`salja.fixmyphone.se`) | ✅ Aktiv – kräver browser |
| Swappie | Playwright + nätverksinterception | ✅ Aktiv – kräver browser |
| Teknikcentralen | – | ⏸ Inaktiv – kontaktformulär, inga publika priser |

## API-endpoints

| Endpoint | Beskrivning |
|---|---|
| `GET /api/prices` | Alla priser (filtrera med `?model=`, `?storage_gb=`, `?condition=`, `?retailer=`) |
| `GET /api/prices/best` | Bästa bud per modell/lagring/skick |
| `GET /api/models` | Lista alla tillgängliga modeller |
| `GET /api/retailers` | Lista aktiva återförsäljare |
| `POST /api/quote` | Returnerar bästa bud för ett formulärsvar |
| `POST /api/scrape` | Trigga manuell scraping (kräver `X-API-Key` header) |
| `POST /api/import-prices/{retailer}` | Importera lokalt hämtade priser (kräver `X-API-Key` header) |
| `GET /health` | Healthcheck |
| `GET /docs` | Swagger UI |

## Lokal utveckling

```bash
# Installera beroenden
pip install -r requirements.txt

# Installera Playwright-browser
playwright install chromium

# Kopiera och konfigurera miljövariabler
cp .env.example .env

# Starta servern
uvicorn app.main:app --reload
```

## Deploy på Railway

1. Skapa nytt Railway-projekt och koppla till detta repo
2. Lägg till miljövariabler från `.env.example`
3. Railway använder `Dockerfile` automatiskt
4. PostgreSQL: Lägg till Railway Postgres-plugin och sätt `DATABASE_URL`

```bash
# Sätt miljövariabler i Railway
SCRAPE_API_KEY=din-hemliga-nyckel
DATABASE_URL=postgresql+asyncpg://...  # från Railway Postgres
SCRAPE_INTERVAL_HOURS=4
PLAYWRIGHT_HEADLESS=true
ALLOWED_ORIGINS=https://cashmyphone.se
```

## Exempelfrågor

```bash
# Alla iPhone 15 Pro-priser
curl https://din-api.railway.app/api/prices?model=iPhone+15+Pro

# Bästa bud per modell
curl https://din-api.railway.app/api/prices/best?model=iPhone+15

# Trigga manuell scraping
curl -X POST https://din-api.railway.app/api/scrape \
  -H "X-API-Key: din-hemliga-nyckel"

# Scrapa bara PhoneHero
curl -X POST "https://din-api.railway.app/api/scrape?retailer=phonehero" \
  -H "X-API-Key: din-hemliga-nyckel"

# Scrapa PhoneHero synkront och få resultat/fel direkt i terminalen
curl -X POST "https://din-api.railway.app/api/scrape?retailer=phonehero&sync=true" \
  -H "X-API-Key: din-hemliga-nyckel"

# Scrapa reNewed synkront
curl -X POST "https://din-api.railway.app/api/scrape?retailer=renewed&sync=true" \
  -H "X-API-Key: din-hemliga-nyckel"

# Scrapa Fixiphone synkront
curl -X POST "https://din-api.railway.app/api/scrape?retailer=fixiphone&sync=true" \
  -H "X-API-Key: din-hemliga-nyckel"

# Scrapa FixPhonePro synkront
curl -X POST "https://din-api.railway.app/api/scrape?retailer=fixphonepro&sync=true" \
  -H "X-API-Key: din-hemliga-nyckel"

# Hämta live-quote från alla aktiva återförsäljare
curl -X POST "https://din-api.railway.app/api/quote" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "iPhone 17",
    "storage_gb": 256,
    "screen_surface": "LIKE_NEW",
    "sides_surface": "LIKE_NEW",
    "back_surface": "LIKE_NEW",
    "is_broken": false,
    "is_screen_broken": false,
    "is_glass_broken": false,
    "is_battery_low": false,
    "is_water_damaged": false
  }'
```

## Prisformat

```json
{
  "id": 1,
  "retailer": "phonehero",
  "model": "iPhone 17",
  "storage_gb": 256,
  "condition": "dev=n|d=no|c=no",
  "price_sek": 7095,
  "currency": "SEK",
  "url": "https://phonehero.se/salj-din-gamla-mobil-till-oss?model=iphone-17",
  "scraped_at": "2026-05-26T10:00:00"
}
```

PhoneHero har två condition-format beroende på modellfamilj:

- Nyare modeller: `dev=n|d=no|c=no`
- Äldre/modeller med fler frågor: `s=n|b=n|d=no|c=no|bt=ok`

reNewed använder Reuselys fyra publika skicknivåer:

- `very_good` – Mycket bra skick
- `used` – Använt skick
- `worn` – Slitet skick
- `broken` – Trasigt skick

FixPhonePro använder kompakta formelnycklar från deras publika JS:

- `s=n|b=n|d=no|f=y|bt=ok` – nyskick, inget fel, batteri minst 85 %
- `s=sp|b=ms|d=yes|f=n|bt=low` – spräckt skärm, sliten baksida/ram, fel/fungerar ej, batteri under 85 %

## Databasschema

- `buyback_prices` – aktuella inköpspriser per återförsäljare/modell/lagring/skick
- `scraper_runs` – logg över scraping-körningar med status och tidsstämplar

## Anteckningar

- Scraping körs schemalagt var 4:e timme (konfigurerbart via `SCRAPE_INTERVAL_HOURS`).
- Nya värderingar via `/api/quote` triggar inte scraping, utan läser bara senast sparade priser från databasen.
- Manuell scraping körs bara via `POST /api/scrape`, till exempel när en ny återförsäljare har lagts till eller priser behöver uppdateras direkt.
- Swappie och FixMyPhone kräver Playwright (ingår i Dockerfile)
- Priser märks som `is_active=false` innan varje ny scraping-körning
- PhoneHero-priser beräknas från publika Livewire-snapshots: baspris per lagring minus avdrag per formulärsvar.
- reNewed-priser hämtas från samma Reusely-widget-API som deras säljsida använder.
