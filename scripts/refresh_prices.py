#!/usr/bin/env python3
"""Manually refresh prices.json (rice prices for Jim's Gift Equalizer).

Run by hand only:  python3 scripts/refresh_prices.py
There is no scheduled job or GitHub Action. Nothing runs automatically.

Sources
  US     BLS average price, series APU0000701312
         (Rice, white, long grain, uncooked, per lb, U.S. city average)
  Haiti  WFP food prices via HDX, "Rice", KG, Retail, Port-au-Prince market
  Malawi WFP food prices via HDX, "Rice", KG, Retail, Lilongwe markets
         (median of the Lilongwe / Lilongwe City markets in the latest month)

Also writes "wishlist": per-mission item prices (WFP, same markets).
Optional: --hti FILE / --mwi FILE to use already-downloaded WFP CSVs.
Standard library only.
"""
import argparse, csv, datetime, io, json, os, statistics, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "prices.json")
UA = {"User-Agent": "jims-gift-equalizer price refresh (manual)"}
BLS_SERIES = "APU0000701312"
HDX = {"HTI": "wfp-food-prices-for-haiti", "MWI": "wfp-food-prices-for-malawi"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def month_label(y, m):
    return f"{MONTHS[m - 1]} {y}"


def bls():
    d = json.loads(get(f"https://api.bls.gov/publicAPI/v1/timeseries/data/{BLS_SERIES}"))
    if d.get("status") != "REQUEST_SUCCEEDED":
        sys.exit(f"BLS request failed: {d.get('message')}")
    rows = [r for r in d["Results"]["series"][0]["data"] if r["period"].startswith("M") and r["value"] not in ("-", "")]
    r = max(rows, key=lambda r: (int(r["year"]), r["period"]))
    y, m = int(r["year"]), int(r["period"][1:])
    return {"currency": "USD", "price": float(r["value"]), "unit": "lb", "place": "U.S. city average",
            "source": "BLS", "period": f"{y}-{m:02d}", "label": month_label(y, m),
            "series": BLS_SERIES, "url": f"https://data.bls.gov/timeseries/{BLS_SERIES}"}


def wfp_csv(iso, path):
    if path:
        return open(path, newline="", encoding="utf-8").read()
    pkg = json.loads(get(f"https://data.humdata.org/api/3/action/package_show?id={HDX[iso]}"))["result"]
    res = [r for r in pkg["resources"] if r["url"].endswith(f"wfp_food_prices_{iso.lower()}.csv")]
    if not res:
        sys.exit(f"No WFP food price CSV found on HDX for {iso}")
    return get(res[0]["url"]).decode("utf-8")


def wfp(iso, text, match, place):
    rows = [r for r in csv.DictReader(io.StringIO(text))
            if r["commodity"] == "Rice" and r["unit"] == "KG" and r["pricetype"] == "Retail" and match(r)]
    if not rows:
        sys.exit(f"No matching rice rows for {iso}")
    latest = max(r["date"] for r in rows)
    cur = [r for r in rows if r["date"] == latest]
    prices = [float(r["price"]) for r in cur]
    y, m = int(latest[:4]), int(latest[5:7])
    out = {"currency": cur[0]["currency"], "price": round(statistics.median(prices), 2), "unit": "kg",
           "place": place, "source": "WFP", "period": f"{y}-{m:02d}", "label": month_label(y, m),
           "url": f"https://data.humdata.org/dataset/{HDX[iso]}"}
    if len(cur) > 1:
        out["note"] = "median of " + ", ".join(f"{r['market']} {float(r['price']):g}" for r in cur)
    return out


# Wishlist items (mission presets). Each real price is WFP retail, latest month, median of the
# listed markets. Items with no WFP series (school kit, medicine kit) are "price set by mission".
WISH = {
    "HTI": [("rice", "Rice", "KG", 9.0718474), ("beans_black", "Beans (black)", "KG", 4.5359237),
            ("oil_gal", "Oil (vegetable)", "Gallon", 1), ("maize_meal", "Maize meal", "KG", 4.5359237),
            ("sugar", "Sugar", "KG", 1), ("salt", "Salt", "KG", 1), ("eggs30", "Eggs", "30 pcs", 1),
            ("school", None, None, None), ("med", None, None, None)],
    "MWI": [("rice", "Rice", "KG", 9.0718474), ("beans", "Beans", "KG", 4.5359237),
            ("maize50", "Maize", "KG", 50), ("oil_l", "Oil (vegetable)", "L", 1), ("sugar", "Sugar", "KG", 1),
            ("soap", "Bathing soap", "300 G", 1), ("school", None, None, None), ("med", None, None, None)],
}


def wfp_item(iso, text, match, place, key, commodity, unit, qty):
    if not commodity:
        return {"key": key, "price": None}
    rows = [r for r in csv.DictReader(io.StringIO(text))
            if r["commodity"] == commodity and r["unit"] == unit and r["pricetype"] == "Retail" and match(r)]
    if not rows:
        return {"key": key, "price": None}
    latest = max(r["date"] for r in rows)
    cur = [r for r in rows if r["date"] == latest]
    unit_price = statistics.median(float(r["price"]) for r in cur)
    y, m = int(latest[:4]), int(latest[5:7])
    return {"key": key, "currency": cur[0]["currency"], "price": round(unit_price * qty, 2),
            "unit_price": round(unit_price, 2), "unit": unit, "qty": qty, "place": place, "source": "WFP",
            "period": f"{y}-{m:02d}", "label": month_label(y, m), "url": f"https://data.humdata.org/dataset/{HDX[iso]}",
            "markets": ", ".join(f"{r['market']} {float(r['price']):g}" for r in cur)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hti"); ap.add_argument("--mwi")
    a = ap.parse_args()
    hti, mwi = wfp_csv("HTI", a.hti), wfp_csv("MWI", a.mwi)
    m_hti, m_mwi = (lambda r: r["market"] == "Port-au-Prince"), (lambda r: r["admin2"].startswith("Lilongwe"))
    data = {
        "item": "Rice, 20 lb bag", "bag_lb": 20, "bag_kg": 9.0718474,
        "refreshed": datetime.date.today().isoformat(),
        "prices": {
            "USA": bls(),
            "HTI": wfp("HTI", hti, m_hti, "Port-au-Prince"),
            "MWI": wfp("MWI", mwi, m_mwi, "Lilongwe"),
        },
        "wishlist": {
            "HTI": [wfp_item("HTI", hti, m_hti, "Port-au-Prince", *w) for w in WISH["HTI"]],
            "MWI": [wfp_item("MWI", mwi, m_mwi, "Lilongwe", *w) for w in WISH["MWI"]],
        },
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2); f.write("\n")
    for k, v in data["prices"].items():
        print(f"{k}: {v['currency']} {v['price']}/{v['unit']}, {v['place']}, {v['source']}, {v['label']}")
    print("wrote", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
