#!/usr/bin/env python3
"""Machine-translate the UI strings into lang/<code>.json (run by hand, then commit).

English source = the <script id="en"> block in index.html. Languages = LANGS in index.html.
Uses Google Translate's public web endpoint (machine translation). {placeholders} are kept;
any string whose placeholders get lost falls back to English.
Usage: python3 scripts/translate.py [code ...]
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
page = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
EN = json.loads(re.search(r'<script id="en" type="application/json">(.*?)</script>', page, re.S).group(1).replace("<\\/", "</"))
LANGS = json.loads(re.search(r"const LANGS=(\[.*?\]);", page).group(1))
PH = re.compile(r"\{(\w+)\}")

def enc(s):
    s = html.escape(s, quote=False)
    return PH.sub(lambda m: f'<span class="notranslate">{{{m.group(1)}}}</span>', s)

def dec(s):
    s = re.sub(r'<span class="notranslate">\s*(\{\w+\})\s*</span>', r"\1", s)
    return html.unescape(re.sub(r"</?span[^>]*>", "", s)).strip()

def translate(code, texts):
    data = urllib.parse.urlencode([("q", enc(t)) for t in texts]).encode()
    url = f"https://translate.googleapis.com/translate_a/t?client=gtx&sl=en&tl={code}&format=html"
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data, {"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
                out = json.loads(r.read())
            return [dec(x if isinstance(x, str) else x[0]) for x in out]
        except Exception as e:
            time.sleep(2 + 3 * i); err = e
    raise err

def main():
    keys = list(EN); codes = sys.argv[1:] or [l[0] for l in LANGS if l[0] != "en"]
    os.makedirs(os.path.join(ROOT, "lang"), exist_ok=True)
    for code in codes:
        res = []
        for i in range(0, len(keys), 40):
            res += translate(code, [EN[k] for k in keys[i:i + 40]])
        out, bad = {}, []
        for k, v in zip(keys, res):
            if set(PH.findall(EN[k])) != set(PH.findall(v)) or not v:
                bad.append(k); continue
            out[k] = v
        json.dump(out, open(os.path.join(ROOT, "lang", f"{code}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        print(code, len(out), "ok", ("fallback to English: " + ",".join(bad)) if bad else "")

if __name__ == "__main__":
    main()
