#!/usr/bin/env python3
"""채널 업로드 로그(docs/채널-업로드로그.md)를 읽어 기예약·공개 이력과 다음 빈 본편 슬롯(금·화 20:00 JST)·쇼츠 일정을 출력한다.
사용법: next_slot.py [작품명] [--after YYYY-MM-DD]   (PHASE 1 착수·업로드 가이드 작성 때 실행)"""
import re, sys, datetime as dt
ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
LOG = f"{ROOT}/docs/채널-업로드로그.md"
rows = []; shorts_cnt = {}
sec = None
for ln in open(LOG, encoding="utf-8"):
    if ln.startswith("## "): sec = ln.strip()
    m = re.match(r"\|\s*\*{0,2}(\d{4}-\d{2}-\d{2})\*{0,2}\s*\|\s*\*{0,2}(\S+?)\*{0,2}\s*\|\s*\*{0,2}([^|]+?)\*{0,2}\s*\|\s*\*{0,2}([^|]+?)\*{0,2}\s*\|", ln)
    if not m: continue
    d = dt.date.fromisoformat(m.group(1))
    if sec and "쇼츠" in sec:  # 같은 날 행이 여러 개(「+1」)면 더한다
        c = m.group(3).strip().lstrip("+")
        shorts_cnt[d] = shorts_cnt.get(d, 0) + (int(c) if c.isdigit() else 1)
    elif sec and "본편" in sec: rows.append((d, m.group(3).strip(), m.group(4).strip()))  # 「제안」도 찬 칸(11/10 #04와 겹친 실증)
booked = {r[0] for r in rows}
title = next((a for a in sys.argv[1:] if not a.startswith("--")), "(새 작품)")
after = dt.date.today()
if "--after" in sys.argv: after = dt.date.fromisoformat(sys.argv[sys.argv.index("--after") + 1])
print("== 채널 공개 이력·기예약 ==")
for d, t, n in sorted(rows): print(f"  {d} ({'월화수목금토일'[d.weekday()]}) [{t}] {n[:40]}{'  ← 오늘 이후' if d >= after else ''}")
print("  쇼츠 예약일:", ", ".join(f"{d.strftime('%m/%d')}×{c}" for d, c in sorted(shorts_cnt.items())))
# 채널 리듬: 본편은 금·화(10/16·17·20·23·27·30·11/3 실측). 마지막 기예약일 이후 첫 빈 금·화
last = max(booked) if booked else after
d = max(after, last) + dt.timedelta(days=1)
while d.weekday() not in (1, 4) or d in booked: d += dt.timedelta(days=1)
print(f"\n== {title} 제안 ==")
print(f"  본편: {d} ({'월화수목금토일'[d.weekday()]}) 20:00 JST  (커뮤니티 예고 같은 날 12:00)")
# 쇼츠: 본편 다음 날부터 본편 공개일을 빼고, 쇼츠가 없는 날을 먼저(14일 안) → 모자라면 2편 미만인 날로 채운다
free = lambda x, lim: x not in booked and shorts_cnt.get(x, 0) < lim
win = [d + dt.timedelta(days=i) for i in range(1, 15)]
shorts = [x for x in win if free(x, 1)][:5]
x = d + dt.timedelta(days=1)
while len(shorts) < 5:
    if x not in shorts and free(x, 2): shorts.append(x)
    x += dt.timedelta(days=1)
shorts.sort()
for i, s in enumerate(shorts, 1):
    print(f"  쇼츠 {i}: {s} ({'월화수목금토일'[s.weekday()]}) {'12:00' if s.weekday() in (5, 6) else '19:00'}")
print(f"  24시간 지표 확인: {d + dt.timedelta(days=1)} 20:00 / 성과표 기록: {d + dt.timedelta(days=7)}")
print("\n※ 확정 후 docs/채널-업로드로그.md에 예약 행을 추가한다.")
