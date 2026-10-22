#!/usr/bin/env python3
"""채널 업로드 로그(docs/채널-업로드로그.md)를 읽어 기예약·공개 이력과 다음 빈 본편 슬롯(금·토 20:00 JST)·쇼츠 일정을 출력한다.
사용법: next_slot.py [작품명] [--after YYYY-MM-DD]   (PHASE 1 착수·업로드 가이드 작성 때 실행)"""
import re, sys, datetime as dt
ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
LOG = f"{ROOT}/docs/채널-업로드로그.md"
rows = []
for ln in open(LOG, encoding="utf-8"):
    m = re.match(r"\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\S+)\s*\|\s*(\d{1,2}:\d{2})\s*\|\s*([^|]+)\|", ln)
    if m: rows.append((dt.date.fromisoformat(m.group(1)), m.group(3), m.group(4).strip()))
booked = {r[0] for r in rows}
title = next((a for a in sys.argv[1:] if not a.startswith("--")), "(새 작품)")
after = dt.date.today()
if "--after" in sys.argv: after = dt.date.fromisoformat(sys.argv[sys.argv.index("--after") + 1])
print("== 채널 공개 이력·기예약 ==")
for d, t, n in sorted(rows): print(f"  {d} ({'월화수목금토일'[d.weekday()]}) {t}  {n}{'  ← 오늘 이후' if d >= after else ''}")
# 다음 빈 금·토 슬롯: 기예약일과 그 전날·다음날은 피하지 않음(하루 간격 쌍 허용), 같은 날만 금지
d = after + dt.timedelta(days=1)
while d.weekday() not in (4, 5) or d in booked: d += dt.timedelta(days=1)
print(f"\n== {title} 제안 ==")
print(f"  본편: {d} ({'월화수목금토일'[d.weekday()]}) 20:00 JST  (커뮤니티 예고 같은 날 12:00)")
shorts = []; k = 1; x = d + dt.timedelta(days=1)
while len(shorts) < 5:
    if x not in booked:
        shorts.append(x)
    x += dt.timedelta(days=1 if len(shorts) < 2 else 1)
    if len(shorts) == 4: x += dt.timedelta(days=1)  # 5번(결말형)은 하루 띄움
for i, s in enumerate(shorts, 1):
    print(f"  쇼츠 {i}: {s} ({'월화수목금토일'[s.weekday()]}) {'12:00' if s.weekday() in (5, 6) else '19:00'}")
print(f"  24시간 지표 확인: {d + dt.timedelta(days=1)} 20:00 / 성과표 기록: {d + dt.timedelta(days=7)}")
print("\n※ 확정 후 docs/채널-업로드로그.md에 예약 행을 추가한다.")
