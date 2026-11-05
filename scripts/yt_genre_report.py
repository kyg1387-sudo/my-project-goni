#!/usr/bin/env python3
"""장르별 상위 30선 정밀 비교 분석 (최우선 원칙 8 — 고니감독님 요구 시 제출).

사용법:
  python3 scripts/yt_genre_report.py "<장르 키워드>" [--days 30] [--top 30] [--kind main|shorts|both]
         [--ours <우리 기획 한 줄>] [--out docs/분석]
  예: python3 scripts/yt_genre_report.py "スカッと 妻" --kind main --ours "六日の期限、戻った妻の目的"

산출: docs/분석/<날짜>-장르정밀-<키워드>.md
  1 요약(주제어 분포·후크 유형·반전 신호어·길이·공개 요일/시각·채널 규모·조회/일·반응률)
  2 상위 30 표(제목·태그·후크 1행·반응)
  3 상위 5 정밀(제목 분해·설명문 앞 3줄=도입부 추정·상위 댓글 3·구조 기입 칸)
  4 우리 채널 최근 3편 같은 지표
  5 결론 칸(세션 기입: 주제 3·후크 3·제목 3·썸네일 양식·쇼츠 4)
한계: 경쟁 영상 대본 전문은 공개 API로 받을 수 없다 → 제목·설명문·태그·댓글로 구조를 추정하고, 그렇게 적는다.
할당량: 검색 100×(1~2) + 목록 + 댓글 5 ≈ 300유닛.
"""
import argparse
import datetime as dt
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yt_public_report import (api, video_details, channel_details, iso_dur, fmt_dur, jst_date,  # noqa: E402
                              parse_ts, n, short_title, median, title_patterns, JST)

TWIST = ["正体", "実は", "結果", "末路", "後悔", "逆転", "真実", "衝撃", "復讐", "制裁", "言葉を失", "絶句", "顔面蒼白", "【完結】", "涙"]
STOP = set("の に は を が と で も から まで や へ て た し ます です こと もの ため それ これ あの その ある いる する なる さん ちゃん 私 俺 僕 夫 妻 話 動画 チャンネル 登録 お願い ください 皆様 今回 本編 再生 リスト ご覧 いただき ありがとう".split())
REACT = [("続き·次回 요청", r"続き|次回|続編|第2|シリーズ"), ("공감·눈물", r"泣|涙|感動|泣け|胸"), ("スカッと 반응", r"スカッと|ざまあ|すっきり|スッキリ|気持ちいい"),
         ("비판·AI 지적", r"AI|ＡＩ|不自然|合成|棒読み|機械|つまらな|長い|嘘"), ("인물 반응", r"夫|妻|姑|社長|上司|息子|娘")]
DOW = "月火水木金土日"


def words(text):
    toks = re.findall(r"[一-龥々]{2,4}|[ァ-ヶー]{2,}", text)
    return [t for t in toks if t not in STOP]


def hook_type(desc):
    first = (desc or "").strip().split("\n")[0]
    if not first:
        return "없음", ""
    if re.match(r"^[「『]", first):
        return "대사 인용", first
    if re.search(r"\d|[一二三四五六七八九十百千万億]+(円|年|日|歳|人)", first):
        return "숫자·기한", first
    if re.search(r"[?？]$", first):
        return "질문", first
    return "상황 서술", first


def fetch_group(kw, days, top, kind):
    after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    got = []
    variants = [{}] if kind == "main" else ([{"videoDuration": "short"}] if kind == "shorts" else [{}, {"videoDuration": "short"}])
    for extra in variants:
        d = api("search", part="snippet", q=kw, type="video", order="viewCount", publishedAfter=after,
                regionCode="JP", relevanceLanguage="ja", maxResults=50, **extra)
        got += [i["id"]["videoId"] for i in d.get("items", [])]
    vids = video_details(list(dict.fromkeys(got)))
    items = sorted(vids.values(), key=lambda v: -n(v["statistics"].get("viewCount")))
    if kind == "main":
        items = [v for v in items if iso_dur(v["contentDetails"]["duration"]) > 180]
    elif kind == "shorts":
        items = [v for v in items if iso_dur(v["contentDetails"]["duration"]) <= 180]
    items = items[:top]
    chans = channel_details({v["snippet"]["channelId"] for v in items})
    return items, chans


def row_stats(v, chans):
    sn, st = v["snippet"], v["statistics"]
    views = n(st.get("viewCount")); likes = n(st.get("likeCount")); com = n(st.get("commentCount"))
    pub = parse_ts(sn["publishedAt"]).astimezone(JST)
    days = max((dt.datetime.now(JST) - pub).total_seconds() / 86400, 1 / 24)
    ch = chans.get(sn["channelId"], {})
    return dict(id=v["id"], title=sn["title"], desc=sn.get("description", ""), tags=sn.get("tags", []),
                dur=iso_dur(v["contentDetails"]["duration"]), views=views, likes=likes, com=com,
                vpd=views / days, like_r=likes / views * 100 if views else 0, com_r=com / views * 1000 if views else 0,
                dow=DOW[pub.weekday()], hour=pub.hour, date=pub.strftime("%m-%d"),
                ch=sn["channelTitle"], subs=n(ch.get("statistics", {}).get("subscriberCount")),
                chv=n(ch.get("statistics", {}).get("videoCount")))


def top_comments(vid, k=3):
    d = api("commentThreads", part="snippet", videoId=vid, maxResults=k, order="relevance", textFormat="plainText")
    if d.get("_disabled"):
        return []
    return [(t["snippet"]["topLevelComment"]["snippet"].get("textDisplay", ""),
             n(t["snippet"]["topLevelComment"]["snippet"].get("likeCount"))) for t in d.get("items", [])]


def react_class(text):
    return [name for name, pat in REACT if re.search(pat, text)] or ["기타"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keyword")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--kind", choices=("main", "shorts", "both"), default="main")
    ap.add_argument("--ours", default="", help="우리 기획 한 줄(비교 칸에 표시)")
    ap.add_argument("--out", default="docs/분석")
    ap.add_argument("--config", default="scripts/yt_config.json")
    a = ap.parse_args()
    import json
    cfg = json.load(open(a.config, encoding="utf-8"))
    today = dt.datetime.now(JST).strftime("%Y-%m-%d")

    items, chans = fetch_group(a.keyword, a.days, a.top, a.kind)
    rows = [row_stats(v, chans) for v in items]
    if not rows:
        sys.exit("[중단] 검색 결과 없음 — 키워드를 넓힌다")

    # 1 요약
    wc = Counter(w for r in rows for w in set(words(r["title"] + " " + r["desc"][:200])))
    hooks = Counter(hook_type(r["desc"])[0] for r in rows)
    twist = Counter(t for r in rows for t in TWIST if t in r["title"])
    durs = sorted(r["dur"] for r in rows)
    q = lambda p: durs[min(len(durs) - 1, int(len(durs) * p))]
    dows = Counter(r["dow"] for r in rows); hours = Counter(r["hour"] for r in rows)
    subs = sorted(r["subs"] for r in rows)
    pat = title_patterns([r["title"] for r in rows])
    kind_label = {"main": "본편(3분 초과)", "shorts": "쇼츠(3분 이하)", "both": "본편+쇼츠"}[a.kind]
    L = [f"# 장르 정밀 분석 — 「{a.keyword}」 {kind_label} 상위 {len(rows)}선 · 최근 {a.days}일 · {today}", "",
         "최우선 원칙 8. 출처: YouTube Data API(제목·설명문·태그·통계·댓글). **경쟁 영상 대본 전문은 공개 API로 받을 수 없으므로 구조는 제목·설명문·댓글로 추정**한 것이다.",
         f"우리 기획: {a.ours or '(미기입)'}", "",
         "## 1. 요약", "",
         "| 축 | 상위 30선 실측 | 우리 채널 규격·현재 | 판정(세션 기입) |", "|---|---|---|---|",
         f"| 주제어(제목·설명 상위) | {', '.join(f'{w}{c}' for w, c in wc.most_common(12))} | — |  |",
         f"| 후크 유형(설명문 1행) | {', '.join(f'{k} {v}' for k, v in hooks.most_common())} | 제0장 후크 0:00~0:20 결정적 장면 |  |",
         f"| 반전 신호어(제목) | {', '.join(f'{k}{v}' for k, v in twist.most_common(8)) or '없음'} | 제13장 6 앞 30자 반전 핵심 |  |",
         f"| 제목 길이·태그 | 중앙값 {pat['len_median']:.0f}자 · 【】 {pat['tag_ratio']*100:.0f}% · {', '.join(f'【{t}】{c}' for t, c in pat['top_tags'][:4])} | 【スカッと】 앞, 35~40자 |  |",
         f"| 길이 | 중앙값 {fmt_dur(int(median(durs)))} · 25% {fmt_dur(q(.25))} · 75% {fmt_dur(q(.75))} | 10~11분(제0장 1) |  |",
         f"| 공개 요일·시각(JST) | 요일 {', '.join(f'{k}{v}' for k, v in dows.most_common(4))} · 시각 {', '.join(f'{k}時{v}' for k, v in hours.most_common(4))} | 화·금 19:00(제0장 7) |  |",
         f"| 채널 규모(구독) | 중앙값 {subs[len(subs)//2]:,} · 최소 {subs[0]:,} · 1만 미만 {sum(1 for s in subs if s < 10000)}편 | 39 |  |",
         f"| 조회/일 중앙값 | {median([r['vpd'] for r in rows]):,.0f} | 본편 60~80 · 쇼츠 250~3,000 |  |",
         f"| 좋아요율·댓글율 | {median([r['like_r'] for r in rows]):.2f}% · {median([r['com_r'] for r in rows]):.2f}‰ | 본편 0~3% |  |",
         ""]
    # 2 상위 30 표
    L += [f"## 2. 상위 {len(rows)} 표", "",
          "| # | 조회 | 조회/일 | 채널(구독) | 길이 | 공개 | 제목 | 태그 | 후크(설명 1행) | 좋아요율 | 댓글 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in enumerate(rows, 1):
        ht, hl = hook_type(r["desc"])
        L.append(f"| {k} | {r['views']:,} | {r['vpd']:,.0f} | {short_title(r['ch'], 12)}({r['subs']:,}) | {fmt_dur(r['dur'])} | "
                 f"{r['date']}({r['dow']}){r['hour']}時 | {short_title(r['title'], 40)} | {', '.join(r['tags'][:3]) or '—'} | "
                 f"{ht}: {short_title(hl, 28)} | {r['like_r']:.1f}% | {r['com']} |")
    # 3 상위 5 정밀
    L += ["", "## 3. 상위 5 정밀(제목 분해·도입부 추정·댓글 반응)", ""]
    for k, r in enumerate(rows[:5], 1):
        tags_t = re.findall(r"【[^】]+】", r["title"]); core = re.sub(r"【[^】]+】", "", r["title"]).strip()
        parts = re.split(r"[…。→！!？?]", core)
        desc_lines = [ln for ln in r["desc"].split("\n") if ln.strip()][:3]
        cs = top_comments(r["id"])
        L += [f"### {k}. {short_title(r['title'], 60)}", "",
              f"- 수치: {r['views']:,}회 · {r['vpd']:,.0f}/일 · {fmt_dur(r['dur'])} · {r['ch']}({r['subs']:,}, 영상 {r['chv']}편) · 공개 {r['date']}({r['dow']}) {r['hour']}時",
              f"- 제목 분해: 태그 {', '.join(tags_t) or '없음'} / 사건 「{parts[0].strip()[:30]}」 / 결과·반전 「{(parts[1].strip() if len(parts) > 1 else '—')[:30]}」",
              "- 도입부 추정(설명문 앞 3줄):"] + [f"  > {short_title(ln, 70)}" for ln in desc_lines or ["(설명문 없음)"]] + [
              f"- 상위 댓글 {len(cs)}개: " + (" / ".join(f"「{short_title(t, 40)}」({lk}👍, {'·'.join(react_class(t))})" for t, lk in cs) if cs else "없음·비공개"),
              "- 구조 추정(세션 기입): 후크 __ → 갈등 __ → 반전 __ → 결말 __ · 우리와 겹치는 점 __ · 다르게 갈 점 __", ""]
    # 4 우리 채널
    L += ["## 4. 우리 채널 최근 3편(같은 지표)", "",
          "| 공개 | 제목 | 길이 | 조회 | 조회/일 | 좋아요율 | 댓글 |", "|---|---|---|---|---|---|---|"]
    ch = api("channels", part="contentDetails", id=cfg["channel_id"])["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    mine = api("playlistItems", part="contentDetails", playlistId=up, maxResults=50).get("items", [])
    mv = video_details([i["contentDetails"]["videoId"] for i in mine])
    mrows = [row_stats(v, {}) for v in mv.values()]
    want_short = a.kind == "shorts"
    mrows = [r for r in mrows if (r["dur"] <= 180) == want_short]
    mrows.sort(key=lambda r: r["date"], reverse=True)
    for r in mrows[:3]:
        L.append(f"| {r['date']}({r['dow']}) | {short_title(r['title'], 36)} | {fmt_dur(r['dur'])} | {r['views']:,} | {r['vpd']:,.0f} | {r['like_r']:.1f}% | {r['com']} |")
    # 5 결론 칸
    L += ["", "## 5. 결론 — 고니감독님께 제출하는 제안(세션 기입, 비우면 제출 불가)", "",
          "| 항목 | 제안 | 근거(상위 30선 몇 번·어느 수치) |", "|---|---|---|",
          "| 주제 후보 3 |  |  |", "| 후크 문장 3(0~5초 대사) |  |  |", "| 제목 3안(앞 30자 태그+반전) |  |  |",
          "| 길이·광고 지점 |  |  |", "| 썸네일 양식(A/B) |  |  |", "| 쇼츠 4편(제목 앞 20자·길이) |  |  |",
          "| 공개 요일·시각 |  |  |", "| 이탈 위험 3곳(예상) |  |  |", ""]
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, f"{today}-장르정밀-{a.keyword.replace(' ', '_')}-{a.kind}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"[장르정밀] {len(rows)}편 → {path}")


if __name__ == "__main__":
    main()
