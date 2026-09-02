#!/usr/bin/env python3
"""
Singapore Lottery Scraper
- Latest results from check4d.org (no blocking)
- Historical 4D data from Singapore Pools static files (1 year)
- Merges and deduplicates, keeps up to 1 year of history
"""

import json, re, os, urllib.request, time
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser

LATEST_URL  = "https://www.check4d.org/singapore-4d-results/"
HISTORY_4D  = "https://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_top_draws_en.html"
HISTORY_TOTO= "https://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/toto_result_top_draws_en.html"
MAX_DRAWS   = 150   # ~1 year of draws

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

def fetch(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            print(f"  Attempt {i+1} failed: {e}")
            if i < retries-1: time.sleep(2)
    return None

class TDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells=[]; self._in=False; self._buf=""
    def handle_starttag(self,tag,attrs):
        if tag in("td","th"): self._in=True; self._buf=""
    def handle_endtag(self,tag):
        if tag in("td","th"):
            self._in=False
            t=self._buf.strip()
            if t: self.cells.append(t)
    def handle_data(self,data):
        if self._in: self._buf+=data

def is_real(draw):
    return bool(re.match(r"^\d{2}-\d{2}-\d{4}$", draw.get("date","")))

# ── Parse check4d.org (latest results) ─────────
def parse_check4d(html):
    p=TDParser(); p.feed(html)
    cells=p.cells; fourd=[]; toto=[]; mode=None; i=0; n=len(cells)
    while i<n:
        t=cells[i]
        if re.search(r"Singapore 4D",t,re.I): mode="4d"; i+=1; continue
        if re.search(r"Singapore Toto",t,re.I): mode="toto"; i+=1; continue
        dm=re.match(r"Date:\s*(\d{2}-\d{2}-\d{4})",t)
        if dm and i+1<n:
            drm=re.match(r"Draw No:\s*(\d+)",cells[i+1])
            if drm:
                ds=dm.group(1); dn=drm.group(1); i+=2
                if mode=="4d":
                    e={"draw":dn,"date":ds,"first":[],"second":[],"third":[],"starter":[],"consolation":[]}
                    while i<n:
                        c=cells[i]
                        if re.search(r"1st Prize|首獎",c,re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                            e["first"]=[cells[i+1]]; i+=2; continue
                        elif re.search(r"2nd Prize|二獎",c,re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                            e["second"]=[cells[i+1]]; i+=2; continue
                        elif re.search(r"3rd Prize|三獎",c,re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                            e["third"]=[cells[i+1]]; i+=2; continue
                        elif re.match(r"^\d{4}$",c):
                            if len(e["starter"])<10: e["starter"].append(c)
                            elif len(e["consolation"])<10: e["consolation"].append(c)
                            i+=1; continue
                        elif re.match(r"Date:|Singapore",c,re.I): break
                        i+=1
                    if e["first"]: fourd.append(e)
                elif mode=="toto":
                    nums=[]; additional=None; fp=False
                    while i<n:
                        c=cells[i]
                        if c=="+": fp=True; i+=1; continue
                        if re.match(r"^\d{1,2}$",c):
                            if fp: additional=int(c); i+=1; break
                            else: nums.append(int(c)); i+=1
                        elif re.match(r"Prize Group|Group \d|Date:|Singapore",c,re.I): break
                        else: i+=1; continue
                    if len(nums)>=6:
                        toto.append({"draw":dn,"date":ds,"numbers":sorted(nums[:6]),"additional":additional})
                continue
        i+=1
    return toto, fourd

# ── Parse Singapore Pools static 4D file ───────
def parse_sp_4d(html):
    p=TDParser(); p.feed(html)
    cells=p.cells; draws=[]; i=0; n=len(cells)
    while i<n:
        # Header: "Sun, 30 Aug 2026" and "Draw No. 5529"
        dm=re.match(r"(\w+),\s+(\d+)\s+(\w+)\s+(\d{4})",cells[i])
        if dm and i+1<n and re.match(r"Draw No\.\s*\d+",cells[i+1]):
            raw_date=cells[i]   # "Sun, 30 Aug 2026"
            draw_no=re.search(r"\d+",cells[i+1]).group()
            # Convert to DD-MM-YYYY
            try:
                dt=datetime.strptime(raw_date,"%a, %d %b %Y")
                date_str=dt.strftime("%d-%m-%Y")
            except:
                date_str=raw_date
            i+=2
            e={"draw":draw_no,"date":date_str,"first":[],"second":[],"third":[],"starter":[],"consolation":[]}
            while i<n:
                c=cells[i]
                if re.match(r"1st Prize",c,re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                    e["first"]=[cells[i+1]]; i+=2; continue
                elif re.match(r"2nd Prize",c,re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                    e["second"]=[cells[i+1]]; i+=2; continue
                elif re.match(r"3rd Prize",c,re.I) and i+1<n and re.match(r"^\d{4}$",cells[i+1]):
                    e["third"]=[cells[i+1]]; i+=2; continue
                elif re.match(r"^\d{4}$",c):
                    if len(e["starter"])<10: e["starter"].append(c)
                    elif len(e["consolation"])<10: e["consolation"].append(c)
                    i+=1; continue
                elif re.match(r"\w+,\s+\d+\s+\w+\s+\d{4}",c): break
                i+=1
            if e["first"]: draws.append(e)
            continue
        i+=1
    return draws

# ── Parse Singapore Pools static TOTO file ─────
def parse_sp_toto(html):
    p=TDParser(); p.feed(html)
    cells=p.cells; draws=[]; i=0; n=len(cells)
    while i<n:
        dm=re.match(r"(\w+),\s+(\d+)\s+(\w+)\s+(\d{4})",cells[i])
        if dm and i+1<n and re.match(r"Draw No\.\s*\d+",cells[i+1]):
            raw_date=cells[i]; draw_no=re.search(r"\d+",cells[i+1]).group()
            try:
                dt=datetime.strptime(raw_date,"%a, %d %b %Y")
                date_str=dt.strftime("%d-%m-%Y")
            except:
                date_str=raw_date
            i+=2
            nums=[]; additional=None
            # Skip "Winning Numbers" header cells
            while i<n:
                c=cells[i]
                if re.match(r"^\d{1,2}$",c) and 1<=int(c)<=49:
                    nums.append(int(c)); i+=1
                elif re.match(r"Additional Number",c,re.I): i+=1; continue
                elif re.match(r"Group \d|Winning|Prize|\$",c,re.I): break
                elif re.match(r"\w+,\s+\d+\s+\w+\s+\d{4}",c): break
                else: i+=1
            # Additional number comes after main 6
            if len(nums)>=7:
                additional=nums[6]; nums=nums[:6]
            if len(nums)>=6:
                draws.append({"draw":draw_no,"date":date_str,"numbers":sorted(nums[:6]),"additional":additional})
            continue
        i+=1
    return draws

def merge(new_list, old_list, keep=MAX_DRAWS):
    old_real = [d for d in old_list if is_real(d)]
    new_ids  = {d["draw"] for d in new_list}
    combined = new_list + [d for d in old_real if d["draw"] not in new_ids]
    return combined[:keep]

def main():
    print("="*50)
    print("Singapore Lottery Scraper")
    print("="*50)

    # 1. Fetch latest from check4d.org
    print("\n[1] Fetching latest from check4d.org...")
    toto_new=[]; fourd_new=[]
    html=fetch(LATEST_URL)
    if html:
        toto_new, fourd_new = parse_check4d(html)
        print(f"    check4d → {len(toto_new)} TOTO, {len(fourd_new)} 4D")
        if toto_new: print(f"    Latest TOTO: Draw {toto_new[0]['draw']} | {toto_new[0]['date']} | {toto_new[0]['numbers']} +{toto_new[0]['additional']}")
        if fourd_new: print(f"    Latest 4D:   Draw {fourd_new[0]['draw']} | {fourd_new[0]['date']} | 1st={fourd_new[0]['first']}")
    else:
        print("    check4d.org failed")

    # 2. Try Singapore Pools static files for more history
    print("\n[2] Fetching history from Singapore Pools static files...")
    sp_fourd=[]; sp_toto=[]

    html4d=fetch(HISTORY_4D)
    if html4d:
        sp_fourd=parse_sp_4d(html4d)
        print(f"    SP 4D history → {len(sp_fourd)} draws")
    else:
        print("    SP 4D static file: blocked/unavailable")

    html_toto=fetch(HISTORY_TOTO)
    if html_toto:
        sp_toto=parse_sp_toto(html_toto)
        print(f"    SP TOTO history → {len(sp_toto)} draws")
    else:
        print("    SP TOTO static file: blocked/unavailable")

    # 3. Load existing history
    existing={"toto":[],"four_d":[]}
    if os.path.exists("data/results.json"):
        try:
            with open("data/results.json") as f:
                existing=json.load(f)
            # Filter out old fake data
            existing["toto"]   = [d for d in existing.get("toto",[])   if is_real(d)]
            existing["four_d"] = [d for d in existing.get("four_d",[]) if is_real(d)]
            print(f"\n[3] Existing history: {len(existing['toto'])} TOTO, {len(existing['four_d'])} 4D")
        except Exception as e:
            print(f"    Could not load existing: {e}")

    # 4. Merge: priority = check4d latest > SP history > existing
    merged_toto  = merge(toto_new,  merge(sp_toto,  existing.get("toto",[])))
    merged_fourd = merge(fourd_new, merge(sp_fourd, existing.get("four_d",[])))

    print(f"\n[4] Final: {len(merged_toto)} TOTO draws, {len(merged_fourd)} 4D draws")

    data={
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": "check4d.org + Singapore Pools",
        "toto":   merged_toto,
        "four_d": merged_fourd
    }

    os.makedirs("data",exist_ok=True)
    with open("data/results.json","w") as f:
        json.dump(data,f,indent=2,ensure_ascii=False)
    print(f"\n✅ Saved to data/results.json")

if __name__=="__main__":
    main()
