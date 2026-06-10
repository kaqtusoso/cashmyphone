# Orderintegreringar

Televera skickar order från frontend till backend-endpointen `POST /api/orders`.
Backend skapar ett ordernummer och kan sedan spara ordern i Google Sheets.
Orderbekräftelser skickas via SMTP när SMTP-miljövariablerna är satta. För
launch använder vi Resend som SMTP-leverantör.

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

`Betalningsuppgifter` och `Skick / frågesvar` sparas som läsbar flerradig text i cellen.
