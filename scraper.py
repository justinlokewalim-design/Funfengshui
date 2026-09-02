#!/usr/bin/env python3
"""
Singapore Lottery Scraper — source: check4d.org
"""

import json, re, os, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

SOURCE_URL = "https://www.check4d.org/singapore-4d-results/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = []
        self._in = False
        self._buf = ""
    def handle_starttag(self, tag, attrs):
        if tag in ("td","th"): self._in = True; self._buf = ""
    def handle_endtag(self, tag):
        if tag in ("td","th"):
            self._in = False
            t = self._buf.strip()
            if t: self.cells.append(t)
    def handle_data(self, data):
        if self._in: self._buf += data

def parse_page(html):
    p = TableParser()
    p.feed(html)
    cells = p.cells
    fourd_draws = []
    toto_draws  = []
    mode = None
    i = 0
    n = len(cells)

    while i < n:
        t = cells[i]
        if re.search(r"Singapore 4D", t, re.I):
            mode = "4d"; i += 1; continue
        if re.search(r"Singapore Toto", t, re.I):
            mode = "toto"; i += 1; continue

        date_m = re.match(r"Date:\s*(\d{2}-\d{2}-\d{4})", t)
        if date_m and i+1 < n:
            draw_m = re.match(r"Draw No:\s*(\d+)", cells[i+1])
            if draw_m:
                date_str = date_m.group(1)
                draw_no  = draw_m.group(1)
                i += 2

                if mode == "4d":
                    entry = {"draw":draw_no,"date":date_str,"first":[],"second":[],"third":[],"starter":[],"consolation":[]}
                    while i < n:
                        c = cells[i]
                        if re.search(r"1st Prize|首獎", c, re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                            entry["first"]=[cells[i+1]]; i+=2; continue
                        elif re.search(r"2nd Prize|二獎", c, re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                            entry["second"]=[cells[i+1]]; i+=2; continue
                        elif re.search(r"3rd Prize|三獎", c, re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                            entry["third"]=[cells[i+1]]; i+=2; continue
                        elif re.match(r"^\d{4}$", c):
                            if len(entry["starter"])<10: entry["starter"].append(c)
                            elif len(entry["consolation"])<10: entry["consolation"].append(c)
                            i+=1; continue
                        elif re.match(r"Date:|Singapore", c, re.I): break
                        i+=1
                    if entry["first"]: fourd_draws.append(entry)

                elif mode == "toto":
                    nums=[]; additional=None; found_plus=False
                    while i < n:
                        c = cells[i]
                        if c == "+": found_plus=True; i+=1; continue
                        if re.match(r"^\d{1,2}$", c):
                            if found_plus: additional=int(c); i+=1; break
                            else: nums.append(int(c)); i+=1
                        elif re.match(r"Prize Group|Group \d|Date:|Singapore", c, re.I): break
                        else: i+=1; continue
                    if len(nums)>=6:
                        toto_draws.append({"draw":draw_no,"date":date_str,"numbers":sorted(nums[:6]),"additional":additional})
                continue
        i += 1

    return toto_draws, fourd_draws

def is_real_draw(draw):
    """Filter out fake/sample data — real draws have proper date format DD-MM-YYYY"""
    return bool(re.match(r"^\d{2}-\d{2}-\d{4}$", draw.get("date", "")))

def merge(new_list, old_list, keep=30):
    """Merge new draws into history, keeping only real data"""
    # Only keep real data from old list (filter out 2025 fake sample data)
    old_real = [d for d in old_list if is_real_draw(d)]
    new_draws = {d["draw"] for d in new_list}
    combined  = new_list + [d for d in old_real if d["draw"] not in new_draws]
    return combined[:keep]

def main():
    print(f"Fetching {SOURCE_URL} ...")
    toto_draws = []
    fourd_draws = []

    try:
        html = fetch_html(SOURCE_URL)
        toto_draws, fourd_draws = parse_page(html)
        print(f"  Parsed: {len(toto_draws)} TOTO, {len(fourd_draws)} 4D")
        if toto_draws:
            t = toto_draws[0]
            print(f"  Latest TOTO → Draw {t['draw']} | {t['date']} | {t['numbers']} + {t['additional']}")
        if fourd_draws:
            f = fourd_draws[0]
            print(f"  Latest 4D   → Draw {f['draw']} | {f['date']} | 1st={f['first']}")
    except Exception as e:
        print(f"  Error: {e}")

    # Load existing history
    existing = {"toto": [], "four_d": []}
    if os.path.exists("data/results.json"):
        try:
            with open("data/results.json") as f:
                existing = json.load(f)
        except Exception:
            pass

    merged_toto  = merge(toto_draws,  existing.get("toto",   []))
    merged_fourd = merge(fourd_draws, existing.get("four_d", []))

    data = {
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": "check4d.org",
        "toto":   merged_toto,
        "four_d": merged_fourd
    }

    os.makedirs("data", exist_ok=True)
    with open("data/results.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved → {len(merged_toto)} TOTO + {len(merged_fourd)} 4D draws")

if __name__ == "__main__":
    main()
