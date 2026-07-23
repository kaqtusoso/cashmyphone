# Televera Social Farm

Social Farm skapar ett svenskt TikTok-/Reels-utkast med sex vertikala slides:
en cover och fem innehållsslides. Text och bakgrunder hålls separata. Det gör
typografin konsekvent och låter redaktören byta text eller bild utan att generera
om hela inlägget.

## Lokalt arbetsflöde

1. Starta backend och frontend som vanligt.
2. Öppna `/admin/social-farm`.
3. Ange samma nyckel som `SCRAPE_API_KEY`.
4. Välj ämne eller låt farmen rotera automatiskt.
5. Skapa ett utkast, granska alla sex slides och redigera vid behov.
6. Godkänn och ladda ned ZIP-paketet med PNG-filer, caption och manifest.

Adminytan publicerar ingenting till TikTok eller Instagram. Ett godkännande
markerar bara materialet som färdigt för manuell publicering.

## Schemaläggning varannan dag

Farmen är avstängd som standard. Aktivera den med:

```env
SOCIAL_FARM_ENABLED=true
SOCIAL_FARM_INTERVAL_HOURS=48
SOCIAL_FARM_CRON_HOUR=8
SOCIAL_FARM_TOPIC_COOLDOWN_DAYS=45
```

Den befintliga backend-schedulern kontrollerar farmen varje dag klockan 08:00
Europe/Stockholm. Tjänsten skapar bara ett utkast när minst 48 timmar har gått
sedan det senaste. Varje körfönster har en unik nyckel, så en omstart skapar inte
dubbletter.

## AI-leverantörer

Kuraterad svensk copy och ett lokalt bibliotek med fullbleed lifestyle-foton är
säkra standardvärden:

```env
SOCIAL_FARM_COPY_PROVIDER=curated
SOCIAL_FARM_IMAGE_PROVIDER=local
```

För AI-varianter:

```env
OPENAI_API_KEY=...
SOCIAL_FARM_COPY_PROVIDER=openai
SOCIAL_FARM_IMAGE_PROVIDER=openai
SOCIAL_FARM_TEXT_MODEL=gpt-5.6-luna
SOCIAL_FARM_IMAGE_MODEL=gpt-image-2
SOCIAL_FARM_GENERATED_IMAGES_PER_POST=2
```

Endast de första två bakgrunderna AI-genereras som standard. Övriga slides väljs
ur ett lokalt, deterministiskt fotobibliotek med sovrum, frukostbord, picknick,
café, kustmiljö och kvällsstilleben. Bildprompten tillåter människor på högst två
slides och undviker händer som interagerar med föremål.

## API

Alla endpoints kräver `X-API-Key`.

- `GET /api/social-farm/topics`
- `GET /api/social-farm/posts`
- `POST /api/social-farm/generate`
- `POST /api/social-farm/schedule/run`
- `POST /api/social-farm/posts/{id}/approve`
- `POST /api/social-farm/posts/{id}/slides/{slide_id}`
- `POST /api/social-farm/posts/{id}/slides/{slide_id}/regenerate`
- `GET /api/social-farm/posts/{id}/export`

Genererade filer sparas under `data/social_farm/`, som inte ska versionshanteras.
