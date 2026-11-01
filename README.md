# Jim's Gift Equalizer

Give so each one can buy the same. Free to use and share.

Open it: https://ploug76.github.io/jims-gift-equalizer/

## Rice prices

"Rice, 20 lb bag" uses real market prices stored in `prices.json`
(US: BLS series APU0000701312; Haiti and Malawi: WFP food prices via HDX).
To update them, run by hand: `python3 scripts/refresh_prices.py`, then commit.
There is no automatic job.

## Mission wishlists

Each mission preset has a wishlist of things it buys at its own local market.
Prices are WFP retail market prices (via HDX) for the mission's area, with the market
and month on every item; `scripts/refresh_prices.py` also refreshes them (the
`wishlist` part of `prices.json`). Items with no market price (school kit, medicine
kit) say "price set by mission". The donor picks items, copies the note
("For: 2 × Rice, 20 lb bag; ...") and gives through the mission's own page.
The app never sends or holds money.

Share links: `#m=branch&q=rice.2,oil_gal.1` opens a preset with quantities.
A mission can build its own list in "Make a wishlist for your mission", which
copies a `#wish=...` link (name, https giving link, currency, items).

## Languages

100 languages, auto-picked from the phone's language, remembered, searchable.
Language names come from the browser (`Intl.DisplayNames`). UI translations in
`lang/<code>.json` are machine-translated (Google Translate) from the English
strings in `index.html`; English is the original. Re-run by hand:
`python3 scripts/translate.py` (or a list of codes), then commit.
