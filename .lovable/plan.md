## Mål

Ge erbjudande-sidan (resultatlistan i `UnifiedFlow.tsx` + `ComparisonTable.tsx`) ett tydligare, mer kontrastrikt utseende inspirerat av Guldkollen, och ersätta navigationen till `/checkout` med en formulär-modal som dyker upp direkt på samma sida när användaren klickar "Sälj".

---

## 1. Ny header för resultatet (ersätter "Här är vad du kan få…")

Inspirerat av Guldkollens "Värdering för 10g 21K guld":

- Rubrik: **"Värdering för {model} {storage}"** där modell+storage färgas i CMP-grönt (`text-primary`) som accent.
- Underrad (mindre, muted): **"{antal} köpare har värderat din telefon"**.
- Tredje rad ännu mindre: **"Priser hämtade: {datum tid}"**.
- Tas bort: "Sorterat från högsta till lägsta bud · uppdaterat just nu".

## 2. "Bästa erbjudandet"-hero-kort (nytt)

Direkt under rubriken, ett brett kort som lyfter fram det högsta budet — Guldkollens orange-hero översatt till CMP-grönt:

- Bakgrund: ljus grön tint (`bg-primary/5`), grön border (`border-2 border-primary/40`), rundade hörn (`rounded-2xl`).
- Innehåll centrerat: liten label "💰 Bästa erbjudandet", stort pris i `text-primary` (4xl/5xl bold), och en rad "Skillnad mot lägsta pris: **{diff} kr**" där diff är klickbar/understruken i grönt.

## 3. Lista över alla bud (ersätter nuvarande 4-kolumns-grid)

Idag är `ComparisonTable.tsx` ett kortgrid. Byts till en **vertikal lista** (samma stil som Guldkollens rad-layout):

```
[#1]  Företagsnamn                          11 120 kr     [ Sälj ]
      kr/telefon-metadata                   +diff kr
```

Detaljer:

- Varje rad: vit `bg-card`, border `border-border`, `rounded-xl`, `p-4`/`p-5`.
- Topplaceringen (#1): grön border (`border-2 border-primary`) + grön rankningscirkel.
- Övriga rader: neutral border, grå rankningscirkel (`bg-muted text-muted-foreground`).
- Vänster: cirkel med rangnummer + företagsnamn (bold) + liten metadata-rad (leverans/utbetalning, muted).
- Höger: pris i bold + grön "+diff kr" under + grön "Sälj"-knapp (CMP-grön, samma som idag).
- Hover: lätt skugga och translate-y för feedback (samma minimalistiska animationsstil som memo:n säger).

## 4. "Köper ej din telefon"-block

Behålls men flyttas under listan och får en tydligare separation (extra `mt-8`, egen rubrik utanför `bg-muted/30`-boxen). Ingen funktionell ändring.

## 5. Mobil-layout

- Hero-kortet och raderna är redan vertikala, så de fungerar i mobilvy.
- På `< sm`: minska rubrikstorlek (`text-xl`), behåll cirkelrang + företagsnamn på rad 1, pris + Sälj på rad 2 om plats saknas (`flex-col sm:flex-row`).
- "Skillnad mot lägsta pris"-raden bryts på två rader vid behov.

## 6. Sälj-formulär som modal istället för `/checkout`-navigering

Idag navigerar "Välj erbjudande" till `/checkout?dealer=...` (se `ComparisonTable.tsx`). Det ersätts med en **Dialog** som öppnas på samma sida.

- Ny komponent: `src/components/SellOfferDialog.tsx`.
- Triggas från Sälj-knappen i den nya rad-listan — istället för `navigate(...)` sätts state `{ open: true, offer }` i resultat-vyn.
- Innehåll i dialogen: samma formulär-fält som finns på `Checkout.tsx` idag (förnamn, efternamn, adress, postnummer, stad, telefon, e-post, betalmetod m.m.) — formulärlogiken, Zod-schemat och submit-flödet flyttas/extraheras från `Checkout.tsx` så att samma kod återanvänds av både dialog och route.
- Visuell stil: matchar "Sälj"-formuläret från Guldkollen / nuvarande UnifiedFlow-steg — `bg-card`, grön accent, sektionsrubriker i fetstil ovanför grupperade fält (samma mönster som vi nyligen införde i Funktionskoll-steget).
- Vid submit: samma `OrderTransition` → success-flöde som idag.
- `/checkout`-routen behålls bakåtkompatibel (renderar samma formulär-komponent) men är inte längre primärt entry-point från resultaten.

## 7. Färg- & kontrast-uppgradering

För att lösa "för lite kontrast – allt är vitt":

- Yttre sidbakgrund: byt från ren vit till `bg-muted/40` (mycket ljus grön-grå) bakom resultatkortet, så att vita kort poppar.
- Behåll kort som vita med tydlig border.
- Använd grön accent (`--primary`) konsekvent för: rubrikens modellnamn, hero-pris, rang-#1, diff-belopp, Sälj-knappar.

Alla färger via semantiska tokens i `index.css` — inga hårdkodade färger i komponenter (`#00B87A` byts ut mot `bg-primary` där det förekommer i `ComparisonTable.tsx`).

---

## Filer som ändras

- `src/components/UnifiedFlow.tsx` — ny resultatheader + hero-kort, byt grid-grafik till lista, hantera dialog-state.
- `src/components/ComparisonTable.tsx` — skrivs om till rad-lista, eller ersätts av nya komponenter `OffersList.tsx` + `BestOfferHero.tsx`.
- `src/components/SellOfferDialog.tsx` — ny dialog som wrappar formuläret.
- `src/pages/Checkout.tsx` — extrahera formulär + schema till delad komponent (t.ex. `CheckoutForm.tsx`) som dialogen och routen båda använder.

## Öppna frågor

1. Ska "Köper ej din telefon"-blocket visas som en collapsed accordion (Guldkollen-känsla, mindre brus) eller alltid öppet?
2. När formuläret submittas i dialogen — ska vi fortfarande navigera till `/order/success`-flödet efteråt, eller stänga dialogen och visa success inline ovanpå resultatlistan?
