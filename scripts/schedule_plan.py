#!/usr/bin/env python3
"""美談ものがたり 등록 일정 관리(고니감독님 지시 2026-10-18 — 영상 제작할 때마다 등록 일자 정리·관리·일정 잡기, 제0장 9).
대장: docs/등록현황-美談ものがたり.json(스튜디오 확인 후 갱신).
사용법:
  python3 scripts/schedule_plan.py check                      # 하루 쇼츠 2편 초과·같은 시각 중복·본편 요일·편당 쇼츠 수 검사
  python3 scripts/schedule_plan.py next <작품> <スカッと|美談> [시작일 YYYY-MM-DD]
                                                             # 다음 빈 본편 슬롯(スカッと=화, 美談=금 19:00) + 쇼츠 4편 슬롯 제안
  python3 scripts/schedule_plan.py table                      # 본편·쇼츠 등록 현황 표(markdown)
"""
import collections
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "docs", "등록현황-美談ものがたり.json")
WD = ["月", "火", "水", "木", "金", "土", "日"]


def load():
    return json.load(open(LEDGER, encoding="utf-8"))


def d(s):
    return dt.date.fromisoformat(s)


def check(L):
    warn = []
    per_day = collections.defaultdict(list)
    for s in L["shorts"]:
        per_day[s["date"]].append(s)
    for day, ss in sorted(per_day.items()):
        if len(ss) > L["rules"]["shorts_per_day_max"]:
            warn.append(f"{day} 쇼츠 {len(ss)}편(하루 최대 {L['rules']['shorts_per_day_max']}편): " + " / ".join(x["title"][:16] for x in ss))
        times = [x.get("time") for x in ss if x.get("time")]
        if len(times) != len(set(times)):
            warn.append(f"{day} 같은 시각 쇼츠 중복: {times}")
    for m in L["main"]:
        if d(m["date"]).weekday() not in (1, 4) and d(m["date"]) >= dt.date(2026, 10, 20):
            warn.append(f"본편 {m['date']}({WD[d(m['date']).weekday()]}) — 화·금이 아님: {m['work']}")
    works = {m["work"] for m in L["main"]}
    cnt = collections.Counter(s["work"] for s in L["shorts"])
    for w in works:
        if cnt[w] < L["rules"]["shorts_per_main"] and w not in ("リヤカー", "柳の葉"):
            warn.append(f"{w} 쇼츠 {cnt[w]}편(편당 {L['rules']['shorts_per_main']}편 기준)")
    for w in cnt:
        if w not in works:
            warn.append(f"본편 없는 쇼츠 {cnt[w]}편: {w}")
    md = collections.Counter(m["date"] for m in L["main"])
    for day, n in md.items():
        if n > 1:
            warn.append(f"{day} 본편 {n}편 겹침")
    print("검사 결과:", "이상 없음" if not warn else f"{len(warn)}건")
    for w in warn:
        print(" -", w)
    return warn


def next_slot(L, work, genre, start=None):
    start = d(start) if start else dt.date.today() + dt.timedelta(days=7)    # 편당 제작 7일(제0장 7)
    want = 1 if genre.startswith("スカッと") else 4                          # 화 = スカッと, 금 = 美談
    taken = {m["date"] for m in L["main"]}
    day = start
    while day.weekday() != want or day.isoformat() in taken:
        day += dt.timedelta(days=1)
    per_day = collections.defaultdict(list)
    for s in L["shorts"]:
        per_day[s["date"]].append(s.get("time"))
    slots = L["rules"]["tue_short_slots" if want == 1 else "fri_short_slots"]
    out = []
    for off, tm in slots:
        sd = day + dt.timedelta(days=off)
        while len(per_day[sd.isoformat()]) >= L["rules"]["shorts_per_day_max"] or tm in per_day[sd.isoformat()]:
            if len(per_day[sd.isoformat()]) < L["rules"]["shorts_per_day_max"]:
                tm = "18:00" if tm == "12:00" else "12:00"                  # 같은 시각만 겹치면 다른 시각으로
                if tm not in per_day[sd.isoformat()]:
                    break
            sd += dt.timedelta(days=1)                                       # 그날 2편 차면 다음 날
        per_day[sd.isoformat()].append(tm)
        out.append((sd, tm))
    print(f"[{work}] 본편 {day.isoformat()}({WD[day.weekday()]}) 19:00 · 예약 업로드 마감 {(day - dt.timedelta(days=1)).isoformat()}")
    for k, (sd, tm) in enumerate(out, 1):
        print(f"  쇼츠 {k}: {sd.isoformat()}({WD[sd.weekday()]}) {tm}  (그날 기존 {len([x for x in L['shorts'] if x['date'] == sd.isoformat()])}편)")
    return day, out


def table(L):
    def tm(x):
        t = x.get("time", "—")
        return t + ("?" if "미확인" in x.get("time_src", "미확인") and t != "—" else "")
    print("| 날짜 | 시각 | 본편 | 상태 |\n|---|---|---|---|")
    for m in sorted(L["main"], key=lambda x: x["date"]):
        print(f"| {m['date'][5:].replace('-', '/')}({WD[d(m['date']).weekday()]}) | {tm(m)} | {m['work']} — {m['title']} | {m['status']} |")
    print("\n| 날짜 | 시각 | 쇼츠 | 본편 | 상태 |\n|---|---|---|---|---|")
    for s in sorted(L["shorts"], key=lambda x: (x["date"], x.get("time", ""))):
        print(f"| {s['date'][5:].replace('-', '/')}({WD[d(s['date']).weekday()]}) | {tm(s)} | {s['title']} | {s['work']} | {s['status']} |")
    print("\n시각: — = 스튜디오 목록에 시각이 없어 미확인, ? = 계획값(스튜디오 미확인)")


def sync_guard(L, max_days=2):
    """스튜디오 「예약됨」 목록 대조일 검사(2026-10-31 실증: 대장 10/18 이후 미대조 → 11/10 본편 2편 겹침).
    대장 'updated'는 내가 고친 날일 뿐이므로, 고니감독님이 보낸 스튜디오 목록을 반영한 날짜(studio_synced)로만 판정한다."""
    s = L.get("studio_synced") or {}
    today = dt.date.today()
    bad = []
    for k, name in (("videos", "동영상"), ("shorts", "Shorts")):
        v = s.get(k)
        age = (today - d(v)).days if v else None
        if age is None or age > max_days:
            bad.append(f"{name} 탭 예약 목록 대조 {'없음' if v is None else f'{v}({age}일 전)'}")
    if bad:
        print("⚠ 확정 금지 — " + " / ".join(bad) + ". 스튜디오 「예약됨」 목록(동영상·Shorts)을 받아 대장 반영 후 다시 실행. 아래 날짜는 잠정.")
    return not bad


if __name__ == "__main__":
    L = load()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd in ("check", "next"):
        sync_guard(L)
    if cmd == "check":
        check(L)
    elif cmd == "next":
        next_slot(L, sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else:
        table(L)
