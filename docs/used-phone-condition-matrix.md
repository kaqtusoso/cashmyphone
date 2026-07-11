# Used Phone Condition Matrix

Televera normalizes each retailer's own storefront condition labels into one
comparison scale for buy-side listings.

## Televera classes

| Class | Label | Meaning |
|---|---|---|
| `new_in_box` | Ny i kartong | Explicitly new, sealed, boxed, or "helt ny". |
| `class_a` | Klass A | Best used condition from that retailer. Minimal wear. |
| `class_b` | Klass B | Strong used condition. Visible but moderate wear. |
| `class_c` | Klass C | Lower accepted used condition. Clearer wear but sold as working. |
| `unknown` | Ej klassat | Missing or unmapped condition. Should be reviewed. |

## Retailer mappings

| Retailer | Raw condition | Televera class | Confidence | Note |
|---|---|---|---|---|
| PhoneHero | Ny i kartong | Ny i kartong | High | Explicit boxed/new label. |
| PhoneHero | Klass A | Klass A | High | Retailer grade. |
| PhoneHero | Klass B | Klass B | High | Retailer grade. |
| PhoneHero | Klass C | Klass C | High | Retailer grade. |
| Swappie | A | Klass A | High | Retailer grade. |
| Swappie | B | Klass B | High | Retailer grade. |
| Swappie | C | Klass C | High | Retailer grade. |
| Swappie | D | Klass C | Medium | Below C in Swappie's model; kept in the lowest visible Televera class for now. |
| Telestore | Helt ny | Ny i kartong | High | Explicit new label. |
| Telestore | Premium | Klass A | High | Best used/premium tier. |
| Telestore | Klass A | Klass A | High | Retailer grade. |
| Telestore | Klass B | Klass B | High | Retailer grade. |
| Telestore | Klass C | Klass C | High | Retailer grade. |
| FixMyPhone | Like new | Klass A | High | Best used condition. |
| FixMyPhone | Very good | Klass B | High | Strong used condition. |
| FixMyPhone | Good | Klass C | High | Lowest normal mapped tier. |
| FixMyPhone | Acceptable | Klass C | Medium | Below Good; kept in the lowest visible Televera class for now. |
| HappyPhone | Som ny | Klass A | High | Best used condition. |
| HappyPhone | Premium | Klass A | High | Best/premium condition. |
| HappyPhone | Klass A | Klass A | High | Retailer grade. |
| HappyPhone | Klass B | Klass B | High | Retailer grade. |
| ReNewed | Nyskick | Klass A | High | Best used condition. |
| ReNewed | Premium | Klass A | High | Premium/best condition. |
| ReNewed | Utmärkt skick | Klass B | High | Strong used condition. |
| ReNewed | Bra skick | Klass C | High | Lower accepted used condition. |
| ReNewed | Okej skick | Klass C | Medium | Below Bra; kept in the lowest visible Televera class for now. |
| FixTech | NYHET | Ny i kartong | Medium | Appears to signal newness but should be verified against product pages. |
| FixTech | som ny | Klass A | High | Best used condition. |
| Fixiphone | Grade/Klass A/B/C | Klass A/B/C | Medium | Current scraper often misses condition; parsing needs follow-up. |

Run `python scripts/build_used_phone_catalog.py` after changing mappings. It prints
all unknown or medium-confidence mappings that need review.
