#!/usr/bin/env python3
"""흥행 30선 자동 갱신 (제21장 9 — 고니감독님 지시 2026-11-06 「30일 기준 30선을 수시로, 30일 지나면 자동 갱신」).

yt_config.json 의 top30_genres 마다 최근 30일 본편 30선·쇼츠 30선을 yt_genre_report.py 로 만들고
  docs/분석/흥행30선/<날짜>-<장르>-<kind>.md      (그날 판)
  docs/분석/흥행30선/최신-<장르>-<kind>.md         (항상 최신 — 제작 세션이 읽는 파일)
  docs/분석/흥행30선/_ids.json                      (이전 판 영상 ID, 교체 계산용)
  docs/분석/흥행30선/갱신-<날짜>.md                 (요약: 장르별 새로 진입·빠진 영상, 상위 5)
를 쓴다. 매주 월요일 주간 보고와 매월 1일 확정판 작업이 호출한다.

사용법: python3 scripts/yt_top30_refresh.py [--kinds main,shorts] [--genres "..." ...]
할당량: 장르 4 × kind 2 × 약 150유닛 ≈ 1,200유닛.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yt_public_report import JST  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "docs/분석/흥행30선"


def ids_in(md):
    """상위 30 표에서 제목 열이 아니라 ID를 쓰기 위해 보고 생성 시 숨겨 둔 주석을 읽는다."""
    return re.findall(r"<!-- id:([A-Za-z0-9_-]{11}) -->", md)


def _num(x):
    return float(re.sub(r"[^\d.]", "", x) or 0)


def genre_stats(rows):
    """최신 표 행에서 장르 통계: 조회·조회/일·구독·구독 대비 배수·길이·좋아요율 중앙값, 1만 미만 채널 비율."""
    vs, vpd, subs, spread, dur, like = [], [], [], [], [], []
    for ln in rows:
        c = re.split(r"\s*\|\s*", ln)
        try:
            vs.append(_num(c[3])); vpd.append(_num(c[4]))
            m = re.search(r"\(([\d,]+)\)\s*$", c[5]); subs.append(_num(m.group(1)) if m else 0)
            spread.append(_num(c[6]))
            mm, ss = c[7].split(":")[-2:]; dur.append(int(mm) * 60 + int(ss) + (3600 * int(c[7].split(":")[0]) if c[7].count(":") == 2 else 0))
            like.append(_num(c[12]))
        except (IndexError, ValueError):
            continue
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
    return {"n": len(vs), "views": med(vs), "vpd": med(vpd), "small": sum(1 for x in subs if x < 10000) / len(subs) if subs else 0,
            "spread": med(spread), "dur": med(dur), "like": med(like)}


def genre_ranking(stats, genres):
    """분야 추천: 우리처럼 작은 채널(구독 39)이 뚫기 쉬운 순 — 1만 미만 채널 비율 40%·구독자 대비 배수 30%·좋아요율 20%·조회/일 10%(장르 간 백분위)."""
    keys = [k for k in stats if k.endswith("-main") and stats[k]["n"] >= 10]
    if len(keys) < 2:
        return []
    W = {"small": 0.4, "spread": 0.3, "like": 0.2, "vpd": 0.1}
    pct = {k: {} for k in keys}
    for m in W:
        order = sorted(keys, key=lambda k: stats[k][m])
        for r, k in enumerate(order):
            pct[k][m] = r / (len(keys) - 1)
    score = {k: round(100 * sum(W[m] * pct[k][m] for m in W)) for k in keys}
    L = ["## 분야 추천(본편 30선 기준 — 작은 채널이 뚫기 쉬운 순, 최우선 원칙 8⑨)", "",
         "| 순위 | 분야 | 추천 점수 | 1만 미만 채널 비율 | 구독 대비 배수(중앙값) | 좋아요율(중앙값) | 조회/일(중앙값) | 조회(중앙값) | 길이(중앙값) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for i, k in enumerate(sorted(keys, key=lambda k: -score[k]), 1):
        st = stats[k]
        L.append(f"| {i} | {k[:-5].replace('_', ' ')} | {score[k]} | {st['small']*100:.0f}% | {st['spread']:.1f}x | {st['like']:.1f}% | "
                 f"{st['vpd']:,.0f} | {st['views']:,.0f} | {st['dur']//60}:{st['dur']%60:02d} |")
    L += ["", "읽는 법: 1만 미만 채널 비율·구독 대비 배수가 높을수록 「콘텐츠만으로 뚫리는 분야」, 좋아요율은 만족도(유지율 대리). 추천 점수는 장르 간 상대값. 세션은 이 표 아래에 「이번 달 추천 분야 1개 + 소재 2개 + 이유」를 적어 고니감독님께 보고한다.", ""]
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kinds", default="main,shorts")
    ap.add_argument("--genres", nargs="*", default=None)
    ap.add_argument("--config", default="scripts/yt_config.json")
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding="utf-8"))
    genres = a.genres or cfg.get("top30_genres") or ["スカッと"]
    today = dt.datetime.now(JST).strftime("%Y-%m-%d")
    os.makedirs(OUT, exist_ok=True)
    idp = os.path.join(OUT, "_ids.json")
    prev = json.load(open(idp, encoding="utf-8")) if os.path.exists(idp) else {}
    stats = {}
    cur, summary = {}, [f"# 흥행 30선 갱신 — {today} (최근 30일 창, 장르 {len(genres)}개)", "",
                        "제작 세션은 `docs/분석/흥행30선/최신-<장르>-<kind>.md`를 읽는다(최우선 원칙 7·8). 아래는 이전 판 대비 변동.", ""]
    for g in genres:
        for kind in a.kinds.split(","):
            r = subprocess.run([sys.executable, os.path.join(HERE, "yt_genre_report.py"), g, "--kind", kind,
                                "--out", OUT, "--config", a.config], capture_output=True, text=True)
            if r.returncode != 0:
                summary += [f"## {g} · {kind}", "", f"실패: {r.stderr.strip()[-300:]}", ""]
                continue
            src = r.stdout.strip().split("→")[-1].strip()
            md = open(src, encoding="utf-8").read()
            tag = g.replace(" ", "_")
            dated = os.path.join(OUT, f"{today}-{tag}-{kind}.md")
            latest = os.path.join(OUT, f"최신-{tag}-{kind}.md")
            os.replace(src, dated)
            with open(latest, "w", encoding="utf-8") as f:
                f.write(md)
            ids = ids_in(md)
            key = f"{tag}-{kind}"
            cur[key] = ids
            old = set(prev.get(key, []))
            new_in = [i for i in ids if i not in old]
            dropped = [i for i in old if i not in ids]
            rows = [ln for ln in md.splitlines() if re.match(r"\| \d+ \|", ln) and "<!-- id:" in ln]
            top5 = [re.split(r"\s*\|\s*", ln)[9] for ln in rows[:5]] if rows else []
            stats[key] = genre_stats(rows)
            summary += [f"## {g} · {'본편' if kind == 'main' else '쇼츠'} 30선", "",
                        f"- 이전 판 대비: 새로 진입 {len(new_in)}편 · 빠짐 {len(dropped)}편" + ("" if old else " (첫 판)"),
                        "- 상위 5: " + " / ".join(top5), f"- 파일: `{os.path.basename(latest)}`", ""]
    summary += genre_ranking(stats, genres)
    with open(idp, "w", encoding="utf-8") as f:
        json.dump({**prev, **cur, "_updated": today}, f, ensure_ascii=False, indent=1)
    sp = os.path.join(OUT, f"갱신-{today}.md")
    with open(sp, "w", encoding="utf-8") as f:
        f.write("\n".join(summary))
    print(f"[흥행30선] 장르 {len(genres)} × {a.kinds} → {OUT}/ (요약 {os.path.basename(sp)})")


if __name__ == "__main__":
    main()
