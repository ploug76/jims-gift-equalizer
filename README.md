# Jim's Gift Equalizer

Give so each one can buy the same. Free to use and share.

Open it: https://ploug76.github.io/jims-gift-equalizer/

## Rice prices

"Rice, 20 lb bag" uses real market prices stored in `prices.json`
(US: BLS series APU0000701312; Haiti and Malawi: WFP food prices via HDX).
To update them, run by hand: `python3 scripts/refresh_prices.py`, then commit.
There is no automatic job.
