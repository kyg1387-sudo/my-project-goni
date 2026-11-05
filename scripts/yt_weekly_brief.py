#!/usr/bin/env python3
"""주간 관리 보고 골격 (제21장 8 — 공개 후 지속 관리).

history/channel-*.json 스냅샷(매일 수집)으로 영상별 7일 추세·쇼츠→본편 비율·공개 +7일/+30일 성과를 계산해
docs/분석/주간관리-<날짜>.md 를 만들고, +7/+30일 도달 영상은 docs/시리즈-성과.md 에 행을 추가한다.
「부족한 부분·보완안」 칸은 세션(Claude)이 상위 30선 대조와 함께 채운다.

사용법: python3 scripts/yt_weekly_brief.py [--out docs/분석] [--date YYYY-MM-DD]
"""
import argparse
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yt_public_report import JST, fmt_dur, short_title  # noqa: E402


def load_snaps(hist):
    out = {}
    for f in sorted(os.listdir(hist)):
        if f.startswith("channel-") and f.endswith(".json"):
            with open(os.path.join(hist, f), encoding="utf-8") as fh:
                out[f[8:18]] = json.load(fh)
    return out


def nearest(snaps, target):
    """target 날짜 이전 가장 가까운 스냅샷."""
    ks = [k for k in snaps if k <= target]
    return snaps[ks[-1]] if ks else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/분석")
    ap.add_argument("--date", default=dt.datetime.now(JST).strftime("%Y-%m-%d"))
    a = ap.parse_args()
    hist = os.path.join(a.out, "history")
    snaps = load_snaps(hist)
    if not snaps:
        sys.exit("[중단] history 스냅샷 없음 — 먼저 yt_public_report.py")
    today_k = max(k for k in snaps if k <= a.date) if any(k <= a.date for k in snaps) else max(snaps)
    cur = snaps[today_k]
    d7 = dt.date.fromisoformat(today_k) - dt.timedelta(days=7)
    prev = nearest(snaps, d7.isoformat())
    pv = {r["id"]: r for r in prev["videos"]} if prev else {}

    rows = []
    for r in cur["videos"]:
        p = pv.get(r["id"])
        rows.append({**r, "d7_views": (r["views"] - p["views"]) if p else None,
                     "d7_comments": (r["comments"] - p["comments"]) if p else None})
    mains = [r for r in rows if r["kind"] == "본편"]
    shorts = [r for r in rows if r["kind"] == "쇼츠"]
    L = [f"# 주간 관리 보고 — 美談ものがたり · {a.date} (스냅샷 {today_k}, 7일 전 비교 {prev['date'] if prev else '없음'})", "",
         "제21장 8. 수치는 공개 데이터(조회·좋아요·댓글). 유지율·CTR은 2단계(Analytics) 설정 후 추가.", "",
         "## 1. 채널 7일 요약", "",
         "| 항목 | 지금 | 7일 전 | 증감 |", "|---|---|---|---|"]
    for k, lab in (("views", "누적 조회"), ("subscribers", "구독자"), ("videos", "영상 수")):
        c = cur["channel"][k]
        p = prev["channel"][k] if prev else None
        L.append(f"| {lab} | {c:,} | {format(p, ',') if p is not None else '—'} | {('+' + format(c - p, ',')) if p is not None else '—'} |")
    sv = sum(r["d7_views"] or 0 for r in shorts); mv = sum(r["d7_views"] or 0 for r in mains)
    L += [f"| 7일 조회(본편/쇼츠) | {mv:,} / {sv:,} | — | 쇼츠→본편 비율 {mv / sv * 100 if sv else 0:.1f}% (KPI 2% 이상) |", ""]

    L += ["## 2. 본편 추세(7일 조회 많은 순)", "",
          "| 공개일 | 제목 | 조회 | 7일 Δ | 조회/일 | 좋아요/조회 | 7일 댓글 | 신호 |", "|---|---|---|---|---|---|---|---|"]
    for r in sorted(mains, key=lambda r: -(r["d7_views"] or 0)):
        lr = r["likes"] / r["views"] * 100 if r["views"] else 0
        sig = []
        if r["days"] <= 14 and (r["d7_views"] or 0) < 50:
            sig.append("초기 노출 약함")
        if r["views"] and lr < 1.0 and r["views"] > 100:
            sig.append("좋아요율 1% 미만")
        if (r["d7_comments"] or 0) > 0:
            sig.append("새 댓글")
        L.append(f"| {r['date']} | {short_title(r['title'], 30)} | {r['views']:,} | {('+' + format(r['d7_views'], ',')) if r['d7_views'] is not None else '—'} | "
                 f"{r['views_per_day']} | {lr:.1f}% | {r['d7_comments'] if r['d7_comments'] is not None else '—'} | {', '.join(sig) or '—'} |")
    L += ["", "## 3. 쇼츠 추세(7일 조회 상위 8)", "",
          "| 공개일 | 제목 | 길이 | 조회 | 7일 Δ | 조회/일 |", "|---|---|---|---|---|---|"]
    for r in sorted(shorts, key=lambda r: -(r["d7_views"] or 0))[:8]:
        L.append(f"| {r['date']} | {short_title(r['title'], 30)} | {fmt_dur(r['duration'])} | {r['views']:,} | "
                 f"{('+' + format(r['d7_views'], ',')) if r['d7_views'] is not None else '—'} | {r['views_per_day']} |")

    # +7/+30일 성과표
    perf_p = os.path.join(os.path.dirname(a.out.rstrip("/")), "시리즈-성과.md")
    perf = open(perf_p, encoding="utf-8").read() if os.path.exists(perf_p) else "# 시리즈 성과표 (제21장 3 사후, 자동 추가 + 세션 보완)\n\n| 공개일 | 작품(제목) | 시점 | 조회 | 좋아요/조회 | 댓글 | 조회/일 | 기록일 | 메모(세션) |\n|---|---|---|---|---|---|---|---|---|\n"
    added = []
    for r in mains:
        for mark in (7, 30):
            if mark <= r["days"] < mark + 7:
                key = f"| {r['date']} | {short_title(r['title'], 24)} | +{mark}일 |"
                if key not in perf:
                    lr = r["likes"] / r["views"] * 100 if r["views"] else 0
                    perf += f"{key} {r['views']:,} | {lr:.1f}% | {r['comments']} | {r['views_per_day']} | {a.date} |  |\n"
                    added.append((r["title"], mark))
    os.makedirs(os.path.dirname(perf_p), exist_ok=True)
    with open(perf_p, "w", encoding="utf-8") as f:
        f.write(perf)
    L += ["", "## 4. 공개 +7일·+30일 성과표 추가", "",
          ("- " + "\n- ".join(f"{short_title(t, 30)} +{m}일" for t, m in added)) if added else "- 이번 주 도달 영상 없음", "",
          "## 5. 부족한 부분·보완안(세션 기입 — 비우면 보고 금지)", "",
          "상위 30선 재대조(`yt_genre_report.py`)와 위 표를 근거로 **3개 이상**. 각 항목에 「무엇이 부족한가(수치) · 보완안 · 고니감독님이 스튜디오에서 할 일 · 기대 효과」.", "",
          "| # | 부족한 부분(수치) | 보완안 | 스튜디오 작업 | 기대 효과 |", "|---|---|---|---|---|",
          "| 1 |  |  |  |  |", "| 2 |  |  |  |  |", "| 3 |  |  |  |  |", "",
          "## 6. 다음 작품 소재 제안(상위 30선 근거)", "", "- ", ""]
    path = os.path.join(a.out, f"주간관리-{a.date}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"[주간] 본편 {len(mains)} · 쇼츠 {len(shorts)} · 성과표 추가 {len(added)} → {path}")


if __name__ == "__main__":
    main()
