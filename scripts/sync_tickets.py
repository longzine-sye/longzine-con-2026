"""Read https://mindwellexpo.com/ticket/longzine and write status.json.

state per slot: open | soon | soldout | sep
Run by .github/workflows/sync-tickets.yml every 30 minutes.
"""
import html, json, re, sys, urllib.request
from datetime import datetime, timezone, timedelta

URL = "https://mindwellexpo.com/ticket/longzine"
SOLD = re.compile(r"마감|매진|sold\s*out|품절|잔여\s*0", re.I)

def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (longzine-con status sync)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def text(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()

def parse(page):
    slots = {}
    for lab in re.findall(r'<label class="lz-slot[^"]*">.*?</label>', page, flags=re.S):
        m = re.search(r'name="slot" value="(\d+)"', lab)
        if not m:
            continue
        sid = m.group(1)
        off = "is-off" in lab.split(">", 1)[0] or 'disabled' in re.search(r"<input[^>]*>", lab).group(0)
        pick = text((re.search(r'class="lz-slot__pick[^"]*"[^>]*>(.*?)</span>', lab, re.S) or [None, ""])[1])
        t = text((re.search(r'class="lz-slot__time"[^>]*>(.*?)</span>', lab, re.S) or [None, ""])[1])
        full = text(lab)
        if SOLD.search(pick) or SOLD.search(full):
            state = "soldout"
        elif not off:
            state = "open"
        elif "별도" in pick:
            state = "sep"
        else:
            state = "soon"
        slots[sid] = {"state": state, "time": t.replace("~", "-")}
    return slots

def main(out="status.json"):
    slots = parse(fetch())
    if len(slots) < 5:
        print("parse looked wrong; keeping previous status.json", file=sys.stderr)
        return 1
    try:
        prev = json.load(open(out, encoding="utf-8"))
    except Exception:
        prev = {}
    if prev.get("slots") == slots:
        print("no change")
        return 0
    kst = timezone(timedelta(hours=9))
    data = {"source": URL, "updated": datetime.now(kst).isoformat(timespec="minutes"), "slots": slots}
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("updated", {k: v["state"] for k, v in slots.items()})
    return 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
