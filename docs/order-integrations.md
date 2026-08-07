# Orderintegreringar

Televera skickar order från frontend till backend-endpointen `POST /api/orders`.
Backend skapar ett ordernummer och kan sedan spara ordern i Google Sheets.
Orderbekräftelser skickas via SMTP när SMTP-miljövariablerna är satta. För
launch använder vi Resend som SMTP-leverantör.

## Databasbackup av order

Innan API:t bekräftar en order sparas hela den mottagna ordern append-only i
tabellen `order_submission_backups` i produktionsdatabasen. Backupen innehåller
alla kund-, betalnings- och skickuppgifter samt de genererade fälten
`order_id` och `created_at`. Google Sheets och e-post körs först efter att
databastransaktionen har lyckats. Om databasen inte kan spara backupen svarar
API:t med `503`, så kunden får inte en falsk orderbekräftelse.

Varje mottaget försök sparas som en separat backuprad, även om samma
`client_order_id` skickas flera gånger. Integrationsresultaten sparas på samma
rad som `pending`, `delivered`, `failed` eller `skipped`.

Backuperna innehåller personuppgifter och kan endast läsas med adminnyckeln:

```bash
# Senaste backuperna
curl "$API_URL/api/orders/backups?limit=100" \
  -H "X-API-Key: $SCRAPE_API_KEY"

# Alla sparade försök för ett ordernummer
curl "$API_URL/api/orders/backups/TLV-ORDERNUMMER" \
  -H "X-API-Key: $SCRAPE_API_KEY"
```

En sparad order kan skickas om till Google Sheets utan att skapa en dubblett:

```bash
curl -X POST \
  "$API_URL/api/orders/backups/BACKUP_ID/retry-google-sheets" \
  -H "X-API-Key: $SCRAPE_API_KEY"
```

## Railway-miljövariabler

```env
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_SHEETS_SPREADSHEET_ID=
GOOGLE_SHEETS_WORKSHEET_NAME=Orders

# Fallback via Apps Script-webhook. Använd scriptet i docs/televera-orders-webhook.gs.
GOOGLE_SHEETS_WEBHOOK_URL=

# Resend för orderbekräftelser. Backend använder Resend API om RESEND_API_KEY
# finns, annars Resend SMTP-fallback via SMTP_PASSWORD.
RESEND_API_KEY=re_xxxxxxxxx
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USERNAME=resend
SMTP_PASSWORD=re_xxxxxxxxx
SMTP_FROM_EMAIL=order@televera.se
SMTP_FROM_NAME=Televera
SMTP_REPLY_TO=televerasverige@gmail.com
SMTP_USE_TLS=true
ORDER_ADMIN_EMAIL=
ORDER_SUBMISSION_TIMEOUT_SECONDS=10

# Trustpilot-feedback 14 dagar efter order. Kräver Google Sheets API.
FEEDBACK_EMAIL_ENABLED=false
FEEDBACK_EMAIL_START_DATE=2026-07-23
FEEDBACK_EMAIL_START_ORDER_ID=TLV-020A6104AB
TRUSTPILOT_REVIEW_URL=https://se.trustpilot.com/evaluate/televera.se
FEEDBACK_EMAIL_DELAY_DAYS=14
FEEDBACK_EMAIL_CRON_HOUR=9
FEEDBACK_EMAIL_CRON_MINUTE=15
FEEDBACK_EMAIL_BATCH_SIZE=50
```

## Resend

1. Skapa konto på Resend.
2. Lägg till och verifiera domänen `televera.se`.
3. Lägg in DNS-posterna som Resend visar, normalt SPF/DKIM/DMARC-relaterade
   poster.
4. Skapa en API key i Resend.
5. Lägg in `RESEND_API_KEY` och avsändarvariablerna ovan i Railway.
6. Skapa en testorder och kontrollera att mailet syns i både kundens inkorg och
   Resends email-logg.

Backend skickar i första hand via Resend API (`https://api.resend.com/emails`),
eftersom det går över HTTPS och undviker att hostingmiljön blockerar utgående
SMTP-portar. SMTP-inställningarna nedan kan användas som fallback.

Resends SMTP-inställningar är:

```text
Host: smtp.resend.com
Port: 587
Username: resend
Password: Resend API key
Security: STARTTLS
```

## Automatiskt Trustpilot-feedbackmail

När `FEEDBACK_EMAIL_ENABLED=true` kör backend ett dagligt jobb som läser
`Orders`-fliken och skickar ett neutralt Trustpilot-mail till kunder vars order
är minst `FEEDBACK_EMAIL_DELAY_DAYS` gammal.

Sätt `FEEDBACK_EMAIL_START_ORDER_ID` för att börja exakt vid en viss orderrad
och inkludera alla efterföljande rader i `Orders`. När variabeln är satt har den
företräde framför `FEEDBACK_EMAIL_START_DATE`. Om startordern inte hittas stoppas
jobbet utan utskick. Startdatumet finns kvar som fallback när inget order-ID är
konfigurerat.

Jobbet markerar varje orderrad med:

- `Feedbackmail skickat`
- `Resend mejl-ID`
- `Feedbackmail status`

Innan utskicket markeras raden som `Skickar`, och ett lyckat utskick markeras
som `Skickat`. Resend-anropet använder dessutom
en stabil idempotency-nyckel per order. Det förhindrar dubbla utskick om Resend
tar emot mailet men en efterföljande uppdatering av kalkylarket misslyckas.

`Feedback`-fliken är den auktoritativa utskickslistan. Borttagna rader
återskapas inte från `Orders`; endast helt nya ordernummer läggs till när en ny
order sparas.

En säker produktionskontroll som inte skickar mail kan köras med:

```bash
curl -X POST "$API_URL/api/orders/feedback-emails/run?dry_run=true" \
  -H "X-API-Key: $SCRAPE_API_KEY"
```

Trustpilots företagsriktlinjer kräver rättvisa, neutrala inbjudningar utan
incitament. Mallen ber därför kunden dela sin upplevelse, inte lämna ett
positivt betyg.

## Google Sheets via service account

1. Skapa eller öppna Google Sheet-filen där ordrar ska sparas.
2. Skapa ett ark/tab som heter `Orders` eller sätt `GOOGLE_SHEETS_WORKSHEET_NAME`
   till det namn du använder.
3. Dela Sheet-filen med service account-mejlen:
   `televera-orders@televera-477623.iam.gserviceaccount.com`
4. Ge service account-kontot rollen `Editor`.
5. Kopiera spreadsheet-ID:t från URL:en:
   `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
6. Lägg ID:t i Railway som `GOOGLE_SHEETS_SPREADSHEET_ID`.
7. Lägg hela service account-JSON-filen i Railway som
   `GOOGLE_SERVICE_ACCOUNT_JSON`.
8. Säkerställ att Google Sheets API är aktiverat i Google Cloud-projektet.

Backend använder Google Sheets API och skriver automatiskt header-raden om arket
är tomt eller har gamla tekniska rubriker. Därefter append:as varje order som en
ny rad.

## Google Sheets via Apps Script-webhook

Om `GOOGLE_SERVICE_ACCOUNT_JSON` eller `GOOGLE_SHEETS_SPREADSHEET_ID` saknas
faller backend tillbaka till `GOOGLE_SHEETS_WEBHOOK_URL`.

Webhooken ska använda scriptet i `docs/televera-orders-webhook.gs`. Det
scriptet:

- tar emot backendens orderpayload med tekniska nycklar
- skriver svenska rubriker i rätt ordning
- formaterar header, kolumnbredder, filter, fryst rad och radbrytning
- gör om befintlig header-rad nästa gång en order kommer in

## Engångsformattera befintligt orderark

För att skriva om hela `Orders`-fliken på samma sätt som Kostschemat gör, kör:

```bash
python scripts/rebuild_orders_sheet.py \
  --credentials /path/to/credentials.json \
  --spreadsheet-id SPREADSHEET_ID
```

Scriptet kan också använda `GOOGLE_SERVICE_ACCOUNT_JSON` och
`GOOGLE_SHEETS_SPREADSHEET_ID`, vilket passar bättre i Railway eller annan
produktionsmiljö. Google Sheet-filen måste vara delad med service accounten som
`Editor`.

## Kolumner

Orderrader skrivs med dessa kolumner:

```text
Ordernummer
Datum
Köpare
Modell
Lagring
Pris (SEK)
Differens (SEK)
Frakt
Betalning
Förnamn
Efternamn
Personnummer
E-post
Telefon
Adress
Postnummer
Ort
Betalningsuppgifter
Skick / frågesvar
```

`Feedback`-fliken använder endast:

```text
Ordernummer
Feedbackmail skickat
Resend mejl-ID
Feedbackmail status
```

`Betalningsuppgifter` och `Skick / frågesvar` sparas som läsbar flerradig text i cellen.
