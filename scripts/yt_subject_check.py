#!/usr/bin/env python3
"""작품 착수 소재 대조(최우선 원칙 7 — PHASE 1 착수 전 의무).

어느 세션이든 이 한 명령으로 최근 N일 일본 상위 영상을 꺼내 `docs/분석/<날짜>-소재대조-<작품>.md`를 만든다.
표는 자동으로 채우고, 「판정」 칸(같은 반전 여부·바꿀 것)은 제작 세션이 시청자 관점으로 채운 뒤 착수 보고에 붙인다.

사용법:
  python3 scripts/yt_subject_check.py <작품명> "<소재어1>" ["<소재어2>" ...] [--days 30] [--top 20]
  예: python3 scripts/yt_subject_check.py ブラックカード2話 "捨てた妻 スカッと" "六日 期限 妻"

산출: docs/分析/<날짜>-소재대조-<작품명>.md  (qa_final.py --work 가 이 파일을 찾는다)
할당량: 소재어 1개당 100유닛 + 목록 조회.
"""
import argparse
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yt_public_report import (api, video_details, channel_details, iso_dur, fmt_dur, jst_date,  # noqa: E402
                              n, short_title, median, title_patterns, JST)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("work")
    ap.add_argument("keywords", nargs="+")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", default="docs/분석")
    a = ap.parse_args()

    today = dt.datetime.now(JST).strftime("%Y-%m-%d")
    after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=a.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    L = [f"# 소재 대조 — 『{a.work}』 ({today}, 최근 {a.days}일 일본 상위, YouTube Data API)", "",
         "최우선 원칙 7 · 제21장 3. 표는 자동, **판정 칸은 제작 세션이 채운다**(비우면 착수 보고 불가).", ""]
    all_titles = []
    for kw in a.keywords:
        d = api("search", part="snippet", q=kw, type="video", order="viewCount", publishedAfter=after,
                regionCode="JP", relevanceLanguage="ja", maxResults=min(a.top, 50))
        ids = [i["id"]["videoId"] for i in d.get("items", [])]
        vids = video_details(ids)
        chans = channel_details({v["snippet"]["channelId"] for v in vids.values()})
        items = [vids[i] for i in ids if i in vids]
        titles = [v["snippet"]["title"] for v in items]
        all_titles += titles
        longs = [iso_dur(v["contentDetails"]["duration"]) for v in items if iso_dur(v["contentDetails"]["duration"]) > 180]
        shorts = [iso_dur(v["contentDetails"]["duration"]) for v in items if iso_dur(v["contentDetails"]["duration"]) <= 180]
        pat = title_patterns(titles) if titles else {"len_median": 0, "tag_ratio": 0, "top_tags": []}
        L += [f"## 「{kw}」 상위 {len(items)}편", "",
              f"- 제목 길이 중앙값 {pat['len_median']:.0f}자 · 【】태그 {pat['tag_ratio']*100:.0f}% · "
              f"태그: {', '.join(f'【{t}】{c}' for t, c in pat['top_tags']) or '없음'}",
              f"- 본편(3분 초과) {len(longs)}편 길이 중앙값 {fmt_dur(int(median(longs))) if longs else '—'} · "
              f"쇼츠 {len(shorts)}편 길이 중앙값 {fmt_dur(int(median(shorts))) if shorts else '—'}",
              "",
              "| # | 조회 | 채널(구독) | 길이 | 공개일 | 제목 | 반전·구조(세션 기입) |",
              "|---|---|---|---|---|---|---|"]
        for k, v in enumerate(items, 1):
            ch = chans.get(v["snippet"]["channelId"], {})
            subs = n(ch.get("statistics", {}).get("subscriberCount"))
            L.append(f"| {k} | {fmt_n(n(v['statistics'].get('viewCount')))} | {short_title(v['snippet']['channelTitle'], 14)}({subs:,}) | "
                     f"{fmt_dur(iso_dur(v['contentDetails']['duration']))} | {jst_date(v['snippet']['publishedAt'])} | "
                     f"{short_title(v['snippet']['title'], 44)} | {'' if k > 5 else '(상위 5는 필수 기입)'} |")
        L.append("")
    pats = re.findall(r"(…した結果|正体|末路|【完結】|後悔|言葉を失う|真実|衝撃|涙|スカッと)", " ".join(all_titles))
    cnt = {}
    for p in pats:
        cnt[p] = cnt.get(p, 0) + 1
    L += ["## 제목 패턴(전 키워드 합산)", "",
          "- " + (", ".join(f"「{k}」{v}" for k, v in sorted(cnt.items(), key=lambda x: -x[1])) or "패턴어 없음"), "",
          "## 판정(제작 세션 기입 — 비우면 착수 불가)", "",
          "| 항목 | 판정 |", "|---|---|",
          "| 같은 반전이 상위 3편 안에 있는가 → 있으면 무엇을 바꾸는가 |  |",
          "| 본편 길이: 상위 본편 중앙값 ±2분 vs 채널 규격 10~11분 |  |",
          "| 제목 2안(앞 30자에 장르 태그 + 반전 핵심) |  |",
          "| 쇼츠 4편 제목(앞 20자)·길이(상위 쇼츠 중앙값 ±15초) |  |",
          "| 썸네일 대조 시트(`yt_thumb_sheet.py`, PHASE 6에 채움) |  |",
          "| 이번 작품에서 바꾼 것(착수 보고 「데이터 근거 3줄」 ③) |  |", ""]
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"{today}-소재대조-{a.work}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"[소재대조] 키워드 {len(a.keywords)}개 → {path}  (판정 칸을 채운 뒤 착수 보고에 붙인다)")


def fmt_n(x):
    return f"{x:,}"


if __name__ == "__main__":
    main()
