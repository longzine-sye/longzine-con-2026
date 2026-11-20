"""Compact admin rows on stdin ("title DAYn hh:mm-hh:mm|cap|sold|left" per line) -> status.json (argv[1])."""
import json, re, sys
from datetime import datetime, timezone, timedelta

MAP = [("SMCC Book Dive", "1"), ("웰니스 키 플레이어", "2"), ("웰니스 커뮤니티", "4"), ("틈새운동", "5"),
       ("에블바레", "6"), ("노화를 늦추는 과학", "7"), ("스킨 롱제비티", "8"), ("달라지는 몸", "9"),
       ("혈당 스파이크", "10"), ("연희 시이작", "15"), ("오래, 건강하게", "11"), ("인간은 오래", "12"),
       ("같은 체중", "13"), ("롱제비티의 마지막 퍼즐", "14")]
SEP = {"1", "6", "15"}
n = lambda s: int(s.replace(",", ""))

slots = {}
for line in sys.stdin.read().replace("\\n", "\n").strip().strip('"').splitlines():
    p = line.split("|")
    if len(p) != 4:
        continue
    sid = next((v for k, v in MAP if p[0].startswith(k)), None)
    tm = re.search(r"(\d\d:\d\d)\s*[-~]\s*(\d\d:\d\d)", p[0])
    if not sid or not tm:
        continue
    left = 0 if p[3] == "마감" else n(p[3])
    st = "sep" if sid in SEP else ("soldout" if left <= 0 else "open")
    slots[sid] = {"state": st, "time": f"{tm.group(1)}-{tm.group(2)}", "cap": n(p[1]), "sold": n(p[2]), "left": left}

if len(slots) < 12:
    print("parse looked wrong", len(slots), file=sys.stderr); sys.exit(1)
out = sys.argv[1]
try:
    prev = json.load(open(out, encoding="utf-8"))
except Exception:
    prev = {}
if prev.get("slots") == slots:
    print("no change"); sys.exit(3)
kst = timezone(timedelta(hours=9))
json.dump({"source": "mindwellexpo admin sales", "updated": datetime.now(kst).isoformat(timespec="minutes"), "slots": slots},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("updated", {k: (v["state"], v["left"]) for k, v in slots.items()})
