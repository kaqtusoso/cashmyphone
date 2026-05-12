# CashMyPhone API

FastAPI-backend som hämtar inköpspriser för begagnade iPhones från svenska återförsäljare.

## Återförsäljare

| Återförsäljare | Metod | Status |
|---|---|---|
| PhoneHero | Livewire snapshot (`?model=slug`) | ✅ Aktiv – 80+ priser |
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
| `POST /api/scrape` | Trigga manuell scraping (kräver `X-API-Key` header) |
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
SCRAPE_INTERVAL_HOURS=6
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
```

## Prisformat

```json
{
  "id": 1,
  "retailer": "phonehero",
  "model": "iPhone 15 Pro",
  "storage_gb": 256,
  "condition": "nyskick",
  "price_sek": 6159,
  "currency": "SEK",
  "url": "https://phonehero.se/salj-din-gamla-mobil-till-oss?model=iphone-15-pro",
  "scraped_at": "2026-05-12T10:00:00"
}
```

## Databasschema

- `buyback_prices` – aktuella inköpspriser per återförsäljare/modell/lagring/skick
- `scraper_runs` – logg över scraping-körningar med status och tidsstämplar

## Anteckningar

- Scraping körs var 6:e timme (konfigurerbart via `SCRAPE_INTERVAL_HOURS`)
- Swappie och FixMyPhone kräver Playwright (ingår i Dockerfile)
- Priser märks som `is_active=false` innan varje ny scraping-körning
- `condition: "nyskick"` = bästa möjliga skick (ingen rabatt)
