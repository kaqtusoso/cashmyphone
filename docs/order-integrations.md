# Orderintegreringar

CashMyPhone skickar order från frontend till backend-endpointen `POST /api/orders`.
Backend skapar ett ordernummer och kan sedan spara ordern i Google Sheets. Mail är
förberett men avstängt tills vi väljer mailleverantör.

## Railway-miljövariabler

```env
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_SHEETS_SPREADSHEET_ID=
GOOGLE_SHEETS_WORKSHEET_NAME=Orders

# Valfri fallback om vi någon gång vill använda Apps Script i stället.
GOOGLE_SHEETS_WEBHOOK_URL=

# Lämnas tomt tills mailösning är vald.
RESEND_API_KEY=
ORDER_EMAIL_FROM=
ORDER_ADMIN_EMAIL=
ORDER_SUBMISSION_TIMEOUT_SECONDS=10
```

## Google Sheets via service account

1. Skapa eller öppna Google Sheet-filen där ordrar ska sparas.
2. Skapa ett ark/tab som heter `Orders` eller sätt `GOOGLE_SHEETS_WORKSHEET_NAME`
   till det namn du använder.
3. Dela Sheet-filen med service account-mejlen:
   `cashmyphone-orders@cashmyphone-477623.iam.gserviceaccount.com`
4. Ge service account-kontot rollen `Editor`.
5. Kopiera spreadsheet-ID:t från URL:en:
   `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
6. Lägg ID:t i Railway som `GOOGLE_SHEETS_SPREADSHEET_ID`.
7. Lägg hela service account-JSON-filen i Railway som
   `GOOGLE_SERVICE_ACCOUNT_JSON`.
8. Säkerställ att Google Sheets API är aktiverat i Google Cloud-projektet.

Backend använder Google Sheets API och skriver automatiskt header-raden om arket
är tomt. Därefter append:as varje order som en ny rad.

## Kolumner

Orderrader skrivs med dessa kolumner:

```text
order_id
created_at
dealer
model
storage
price_sek
shipping
payment
first_name
last_name
personal_number
email
phone
address
postal_code
city
payment_details
condition_answers
```

`payment_details` och `condition_answers` sparas som JSON-strängar i cellen.
