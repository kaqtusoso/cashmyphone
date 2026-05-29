# Orderintegreringar

CashMyPhone skickar order från frontend till backend-endpointen `POST /api/orders`.
Backend skapar ett ordernummer och kan sedan skicka ordern vidare till Google Sheets
och Resend om miljövariablerna är satta.

## Miljövariabler

```env
GOOGLE_SHEETS_WEBHOOK_URL=
RESEND_API_KEY=
ORDER_EMAIL_FROM=CashMyPhone <orders@cashmyphone.se>
ORDER_ADMIN_EMAIL=
ORDER_SUBMISSION_TIMEOUT_SECONDS=10
```

Om `GOOGLE_SHEETS_WEBHOOK_URL` saknas hoppar backend över Sheets men returnerar
fortfarande en giltig orderbekräftelse.

Om `RESEND_API_KEY` eller `ORDER_EMAIL_FROM` saknas hoppar backend över mailutskick
men returnerar fortfarande en giltig orderbekräftelse.

## Google Sheets via Apps Script

1. Skapa ett Google Sheet med ett ark som heter `Orders`.
2. Öppna `Extensions > Apps Script`.
3. Klistra in scriptet nedan.
4. Deploya som Web App.
5. Välj att web appen körs som dig och att åtkomst tillåts för den som har länken.
6. Lägg Web App-URL:en i `GOOGLE_SHEETS_WEBHOOK_URL`.

```js
const SHEET_NAME = "Orders";

const HEADERS = [
  "order_id",
  "created_at",
  "dealer",
  "model",
  "storage",
  "price_sek",
  "shipping",
  "payment",
  "first_name",
  "last_name",
  "personal_number",
  "email",
  "phone",
  "address",
  "postal_code",
  "city",
  "payment_details",
  "condition_answers",
];

function doPost(e) {
  const payload = JSON.parse(e.postData.contents);
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);

  if (!sheet) {
    throw new Error(`Sheet "${SHEET_NAME}" saknas`);
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
  }

  sheet.appendRow(
    HEADERS.map((key) => {
      const value = payload[key];
      return typeof value === "object" && value !== null ? JSON.stringify(value) : value || "";
    })
  );

  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
```

## Resend

För mailutskick krävs:

- Verifierad domän i Resend.
- `RESEND_API_KEY` från Resend.
- `ORDER_EMAIL_FROM` med en avsändare på den verifierade domänen.

Backend skickar orderbekräftelsen via `https://api.resend.com/emails`.
