#!/usr/bin/env python3
"""
Singapore Pools Lottery Scraper
Uses official static HTML files from Singapore Pools - no login, no block.

URLs:
  TOTO: https://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/toto_result_top_draws_en.html
  4D:   https://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_top_draws_en.html
"""

import json
import re
import os
from datetime import datetime
import urllib.request

TOTO_URL = "https://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/toto_result_top_draws_en.html"
FOURD_URL = "https://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_top_draws_en.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def parse_toto(html):
    """
    Each draw block looks like:
      <td>Mon, 31 Aug 2026</td>  <td>Draw No. 4213</td>
      numbers in a row of <td> cells
      Additional Number in next row
    """
    from html.parser import HTMLParser

    class TotoParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.draws = []
            self.current = {}
            self.td_texts = []
            self.in_td = False
            self.capture = False

        def handle_starttag(self, tag, attrs):
            if tag == "td":
                self.in_td = True
                self.buf = ""

        def handle_endtag(self, tag):
            if tag == "td":
                self.in_td = False
                text = self.buf.strip()
                if text:
                    self.td_texts.append(text)

        def handle_data(self, data):
            if self.in_td:
                self.buf += data

    p = TotoParser()
    p.feed(html)
    texts = p.td_texts

    draws = []
    i = 0
    while i < len(texts):
        # Look for date pattern like "Mon, 31 Aug 2026"
        date_match = re.match(r"\w+,\s+\d+ \w+ \d{4}", texts[i])
        draw_match = re.match(r"Draw No\.\s+(\d+)", texts[i]) if i + 1 < len(texts) else None

        if date_match and i + 1 < len(texts) and re.match(r"Draw No\.\s+\d+", texts[i + 1]):
            draw_date = texts[i]
            draw_num = re.search(r"\d+", texts[i + 1]).group()
            i += 2

            # Collect numbers: up to 6 main + 1 additional
            nums = []
            while i < len(texts) and re.match(r"^\d{1,2}$", texts[i]) and len(nums) < 7:
                nums.append(int(texts[i]))
                i += 1

            if len(nums) >= 6:
                draws.append({
                    "draw": draw_num,
                    "date": draw_date,
                    "numbers": sorted(nums[:6]),
                    "additional": nums[6] if len(nums) >= 7 else None
                })
        else:
            i += 1

    return draws


def parse_4d(html):
    """
    Each draw block:
      <td>Sun, 30 Aug 2026</td>  Draw No. 5529
      1st Prize  9238
      2nd Prize  8594
      3rd Prize  0379
      Starter Prizes: 10 numbers
      Consolation Prizes: 10 numbers
    """
    from html.parser import HTMLParser

    class FourDParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.td_texts = []
            self.in_td = False
            self.buf = ""

        def handle_starttag(self, tag, attrs):
            if tag == "td":
                self.in_td = True
                self.buf = ""

        def handle_endtag(self, tag):
            if tag == "td":
                self.in_td = False
                text = self.buf.strip()
                if text:
                    self.td_texts.append(text)

        def handle_data(self, data):
            if self.in_td:
                self.buf += data

    p = FourDParser()
    p.feed(html)
    texts = p.td_texts

    draws = []
    i = 0
    while i < len(texts):
        date_match = re.match(r"\w+,\s+\d+ \w+ \d{4}", texts[i])
        if date_match and i + 1 < len(texts) and re.match(r"Draw No\.\s+\d+", texts[i + 1]):
            draw_date = texts[i]
            draw_num = re.search(r"\d+", texts[i + 1]).group()
            i += 2

            entry = {
                "draw": draw_num,
                "date": draw_date,
                "first": [],
                "second": [],
                "third": [],
                "starter": [],
                "consolation": []
            }

            # Parse prizes
            j = i
            while j < len(texts) and j < i + 50:
                t = texts[j]
                if t in ("1st Prize", "1St Prize"):
                    if j + 1 < len(texts) and re.match(r"^\d{4}$", texts[j + 1]):
                        entry["first"] = [texts[j + 1]]
                        j += 2
                        continue
                elif t in ("2nd Prize", "2Nd Prize"):
                    if j + 1 < len(texts) and re.match(r"^\d{4}$", texts[j + 1]):
                        entry["second"] = [texts[j + 1]]
                        j += 2
                        continue
                elif t in ("3rd Prize", "3Rd Prize"):
                    if j + 1 < len(texts) and re.match(r"^\d{4}$", texts[j + 1]):
                        entry["third"] = [texts[j + 1]]
                        j += 2
                        continue
                elif re.match(r"^\d{4}$", t):
                    # Determine which category based on count
                    if len(entry["starter"]) < 10:
                        entry["starter"].append(t)
                    elif len(entry["consolation"]) < 10:
                        entry["consolation"].append(t)
                    j += 1
                    continue
                # If we hit a new date, stop
                elif re.match(r"\w+,\s+\d+ \w+ \d{4}", t):
                    break
                j += 1

            i = j
            if entry["first"]:
                draws.append(entry)
        else:
            i += 1

    return draws


def main():
    print("Fetching TOTO results...")
    toto_draws = []
    try:
        html = fetch_html(TOTO_URL)
        toto_draws = parse_toto(html)
        print(f"  Got {len(toto_draws)} TOTO draws")
        if toto_draws:
            print(f"  Latest: Draw {toto_draws[0]['draw']} on {toto_draws[0]['date']}")
    except Exception as e:
        print(f"  TOTO error: {e}")

    print("Fetching 4D results...")
    fourd_draws = []
    try:
        html = fetch_html(FOURD_URL)
        fourd_draws = parse_4d(html)
        print(f"  Got {len(fourd_draws)} 4D draws")
        if fourd_draws:
            print(f"  Latest: Draw {fourd_draws[0]['draw']} on {fourd_draws[0]['date']}")
    except Exception as e:
        print(f"  4D error: {e}")

    # Warn if data looks wrong
    if not toto_draws:
        print("WARNING: No TOTO data, Singapore Pools HTML structure may have changed!")
    if not fourd_draws:
        print("WARNING: No 4D data, Singapore Pools HTML structure may have changed!")

    data = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "toto": toto_draws,
        "four_d": fourd_draws
    }

    os.makedirs("data", exist_ok=True)
    with open("data/results.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to data/results.json")


if __name__ == "__main__":
    main()
