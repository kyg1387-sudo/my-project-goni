#!/usr/bin/env python3
"""YouTube 공개 데이터 수집·보고 (CLAUDE.md 제21장 1단계, docs/데이터기반제작-운영규격.md 2절).

사용법:
  python3 scripts/yt_public_report.py [--date YYYY-MM-DD] [--out docs/분석]
         [--config scripts/yt_config.json] [--keyword 소재어 ...]
         [--no-search] [--no-comments]

인증:
  - 클라우드 세션: 환경 Network secrets(호스트 www.googleapis.com, 헤더 X-Goog-Api-Key)를
    프록시가 넣어 주므로 key 파라미터를 붙이지 않는다.
  - GitHub Actions: 환경 변수 YOUTUBE_API_KEY가 있으면 key 파라미터로 보낸다.
  키 값은 코드·문서·채팅에 쓰지 않는다.

산출물(모두 --out 아래):
  YYYY-MM-DD-채널수치.md   우리 채널 전 영상 수치(조회·좋아요·댓글·조회/일·전 수집 대비 증감), 댓글 AI 언급
  YYYY-MM-DD-장르동향.md   장르 키워드별 최근 N일 상위 영상·제목/길이 패턴·자주 보이는 채널
  comments/<videoId>.json  우리 영상 댓글 전문
  history/channel-YYYY-MM-DD.json  증감 계산용 스냅샷
  최신-채널수치.md / 최신-장르동향.md  같은 내용 복사본(다른 세션이 바로 읽는 용도)

할당량: 검색 100유닛 × 키워드 수 + 목록 조회 약 20유닛 → 하루 1회 약 1,100유닛(무료 1만 유닛 안).
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/youtube/v3/"
JST = dt.timezone(dt.timedelta(hours=9))


# ---------------------------------------------------------------- API 호출
def api(resource, **params):
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if key:
        params["key"] = key
    url = API + resource + "?" + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code in (403, 400) and "quota" in body.lower():
                sys.exit(f"[중단] YouTube API 할당량 초과: {body[:200]}")
            if e.code == 403 and "commentsDisabled" in body:
                return {"items": [], "_disabled": True}
            if attempt == 2:
                sys.exit(f"[오류] {resource} HTTP {e.code}: {body[:300]}")
            time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 2:
                sys.exit(f"[오류] {resource}: {e}")
            time.sleep(2 * (attempt + 1))


def paged(resource, max_items=10**9, **params):
    out, token = [], None
    while True:
        if token:
            params["pageToken"] = token
        d = api(resource, **params)
        out.extend(d.get("items", []))
        token = d.get("nextPageToken")
        if not token or len(out) >= max_items:
            return out[:max_items]


def chunks(xs, n=50):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


# ---------------------------------------------------------------- 유틸
def iso_dur(s):
    """PT1H2M3S → 초."""
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return 0
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se


def fmt_dur(sec):
    return f"{sec // 60}:{sec % 60:02d}"


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def jst_date(s):
    return parse_ts(s).astimezone(JST).strftime("%Y-%m-%d")


def n(x):
    return int(x) if x not in (None, "") else 0


def fmt_n(x):
    return f"{x:,}"


def short_title(t, k=30):
    t = t.replace("|", "｜").replace("\n", " ")
    return t if len(t) <= k else t[:k] + "…"


def median(xs):
    xs = sorted(xs)
    if not xs:
        return 0
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def video_details(ids):
    out = {}
    for c in chunks(ids):
        d = api("videos", part="snippet,statistics,contentDetails", id=",".join(c), maxResults=50)
        for it in d.get("items", []):
            out[it["id"]] = it
    return out


def channel_details(ids):
    out = {}
    for c in chunks(list(ids)):
        d = api("channels", part="snippet,statistics", id=",".join(c), maxResults=50)
        for it in d.get("items", []):
            out[it["id"]] = it
    return out


# ---------------------------------------------------------------- 우리 채널
def collect_channel(cfg, today, out_dir, with_comments=True):
    cid = cfg["channel_id"]
    ch = api("channels", part="snippet,statistics,contentDetails", id=cid)["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    items = paged("playlistItems", part="contentDetails", playlistId=uploads, maxResults=50)
    ids = [i["contentDetails"]["videoId"] for i in items]
    vids = video_details(ids)

    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for vid in ids:
        v = vids.get(vid)
        if not v:
            continue
        sn, st = v["snippet"], v.get("statistics", {})
        dur = iso_dur(v["contentDetails"].get("duration"))
        pub = parse_ts(sn["publishedAt"])
        days = max((now - pub).total_seconds() / 86400, 1 / 24)
        views = n(st.get("viewCount"))
        rows.append({
            "id": vid, "title": sn["title"], "published": sn["publishedAt"],
            "date": jst_date(sn["publishedAt"]), "duration": dur,
            "kind": "쇼츠" if dur <= cfg.get("short_max_seconds", 180) else "본편",
            "views": views, "likes": n(st.get("likeCount")), "comments": n(st.get("commentCount")),
            "days": round(days, 1), "views_per_day": round(views / days, 1),
            "tags": sn.get("tags", []),
        })
    rows.sort(key=lambda r: r["published"], reverse=True)

    # 이전 스냅샷과 증감
    hist_dir = os.path.join(out_dir, "history")
    os.makedirs(hist_dir, exist_ok=True)
    prev, prev_date = {}, None
    snaps = sorted(f for f in os.listdir(hist_dir) if f.startswith("channel-") and f.endswith(".json"))
    snaps = [f for f in snaps if f != f"channel-{today}.json"]
    if snaps:
        prev_date = snaps[-1][8:18]
        with open(os.path.join(hist_dir, snaps[-1]), encoding="utf-8") as f:
            prev = {r["id"]: r for r in json.load(f)["videos"]}
    for r in rows:
        p = prev.get(r["id"])
        r["d_views"] = r["views"] - p["views"] if p else None
        r["d_comments"] = r["comments"] - p["comments"] if p else None

    stats = ch["statistics"]
    snap = {"date": today, "channel": {"views": n(stats.get("viewCount")),
                                        "subscribers": n(stats.get("subscriberCount")),
                                        "videos": n(stats.get("videoCount"))}, "videos": rows}
    with open(os.path.join(hist_dir, f"channel-{today}.json"), "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)

    # 댓글
    ai_hits, new_comments = [], 0
    pat = re.compile(cfg.get("ai_mention_pattern", "AI|不自然"), re.I)
    if with_comments:
        cdir = os.path.join(out_dir, "comments")
        os.makedirs(cdir, exist_ok=True)
        for r in rows:
            if r["comments"] <= 0:
                continue
            d = api("commentThreads", part="snippet,replies", videoId=r["id"], maxResults=100,
                    order="time", textFormat="plainText")
            if d.get("_disabled"):
                continue
            cs = []
            for t in d.get("items", []):
                top = t["snippet"]["topLevelComment"]["snippet"]
                cs.append({"id": t["id"], "author": top.get("authorDisplayName"),
                           "text": top.get("textDisplay"), "likes": n(top.get("likeCount")),
                           "published": top.get("publishedAt")})
                for rp in t.get("replies", {}).get("comments", []):
                    s = rp["snippet"]
                    cs.append({"id": rp["id"], "author": s.get("authorDisplayName"),
                               "text": s.get("textDisplay"), "likes": n(s.get("likeCount")),
                               "published": s.get("publishedAt"), "reply_to": t["id"]})
            path = os.path.join(cdir, f"{r['id']}.json")
            old_ids = set()
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    old_ids = {c["id"] for c in json.load(f).get("comments", [])}
            new_comments += sum(1 for c in cs if c["id"] not in old_ids)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"video_id": r["id"], "title": r["title"], "fetched": today, "comments": cs},
                          f, ensure_ascii=False, indent=1)
            for c in cs:
                if c["text"] and pat.search(c["text"]):
                    ai_hits.append((r, c))
    return ch, snap, rows, prev_date, ai_hits, new_comments


def write_channel_md(cfg, today, ch, snap, rows, prev_date, ai_hits, new_comments, path):
    st = snap["channel"]
    L = [f"# 채널 수치 — {cfg['channel_title']} ({cfg['channel_handle']}) · {today} 수집",
         "",
         f"출처: YouTube Data API v3(공개 수치). 이전 수집: {prev_date or '없음(첫 수집)'}. "
         "수치는 수집 시각 기준이며 스튜디오 비공개 지표(유지율·CTR)는 2단계(Analytics API)에서 다룬다.",
         "",
         "## 1. 채널 합계",
         "",
         "| 항목 | 값 |", "|---|---|",
         f"| 누적 조회수 | {fmt_n(st['views'])} |",
         f"| 구독자 | {fmt_n(st['subscribers'])} |",
         f"| 영상 수 | {st['videos']} (본편 {sum(1 for r in rows if r['kind']=='본편')} · 쇼츠 {sum(1 for r in rows if r['kind']=='쇼츠')}) |",
         ]
    if new_comments or ai_hits:
        L.append(f"| 새 댓글(전 수집 이후) | {new_comments} |")
    L += ["", "## 2. 최근 30일 주목 영상(조회/일 상위 5)", "",
          "| 공개일 | 종류 | 제목 | 길이 | 조회 | 조회/일 | 좋아요 | 댓글 |",
          "|---|---|---|---|---|---|---|---|"]
    recent = [r for r in rows if r["days"] <= 30]
    for r in sorted(recent, key=lambda r: r["views_per_day"], reverse=True)[:5]:
        L.append(f"| {r['date']} | {r['kind']} | {short_title(r['title'])} | {fmt_dur(r['duration'])} | "
                 f"{fmt_n(r['views'])} | {r['views_per_day']} | {r['likes']} | {r['comments']} |")
    L += ["", "## 3. 본편 전체(최신순)", "",
          "| 공개일 | 제목 | 길이 | 조회 | Δ조회 | 조회/일 | 좋아요 | 댓글 | 좋아요/조회 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["kind"] != "본편":
            continue
        dv = "—" if r["d_views"] is None else f"+{r['d_views']:,}"
        lr = f"{r['likes']/r['views']*100:.1f}%" if r["views"] else "—"
        L.append(f"| {r['date']} | {short_title(r['title'], 34)} | {fmt_dur(r['duration'])} | {fmt_n(r['views'])} | "
                 f"{dv} | {r['views_per_day']} | {r['likes']} | {r['comments']} | {lr} |")
    L += ["", "## 4. 쇼츠 전체(최신순)", "",
          "| 공개일 | 제목 | 길이 | 조회 | Δ조회 | 조회/일 | 좋아요 | 댓글 |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["kind"] != "쇼츠":
            continue
        dv = "—" if r["d_views"] is None else f"+{r['d_views']:,}"
        L.append(f"| {r['date']} | {short_title(r['title'], 34)} | {fmt_dur(r['duration'])} | {fmt_n(r['views'])} | "
                 f"{dv} | {r['views_per_day']} | {r['likes']} | {r['comments']} |")
    L += ["", "## 5. 댓글 — 「AI·不自然」 언급(KPI 4, 목표 0건)", ""]
    if not ai_hits:
        L.append("0건.")
    else:
        L += ["| 영상 | 작성자 | 댓글 |", "|---|---|---|"]
        for r, c in ai_hits:
            L.append(f"| {short_title(r['title'], 20)} | {c['author']} | {short_title(c['text'] or '', 80)} |")
    L += ["", "## 6. 읽는 법", "",
          "- 조회/일 = 조회수 ÷ 공개 후 경과일. 공개 7일 안 영상끼리 비교한다.",
          "- 좋아요/조회 1.5% 미만이면 제목·썸네일이 끌어온 시청자와 내용이 어긋났을 가능성(사후 성과표에 기록).",
          "- 댓글 전문은 `comments/<videoId>.json`. 「続き」「次回」 요청 수는 시리즈 연장 판단(5절)에 쓴다.",
          ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------- 장르 동향
def collect_trends(cfg, today, extra_keywords):
    days = cfg.get("search_days", 30)
    after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    kws = list(cfg["keywords"]) + list(cfg.get("extra_keywords", [])) + list(extra_keywords)
    per_kw, all_ids = {}, set()
    for kw in kws:
        d = api("search", part="snippet", q=kw, type="video", order="viewCount",
                publishedAfter=after, regionCode=cfg.get("region", "JP"),
                relevanceLanguage=cfg.get("language", "ja"), maxResults=min(cfg.get("search_max", 20), 50))
        ids = [i["id"]["videoId"] for i in d.get("items", [])]
        per_kw[kw] = ids
        all_ids.update(ids)
    vids = video_details(list(all_ids))
    chans = channel_details({v["snippet"]["channelId"] for v in vids.values()})
    return kws, per_kw, vids, chans, days


def title_patterns(titles):
    tags = re.findall(r"【([^】]{1,12})】", " ".join(titles))
    cnt = {}
    for t in tags:
        cnt[t] = cnt.get(t, 0) + 1
    top = sorted(cnt.items(), key=lambda x: -x[1])[:6]
    with_tag = sum(1 for t in titles if "【" in t)
    return {"len_median": median([len(t) for t in titles]),
            "tag_ratio": with_tag / len(titles) if titles else 0,
            "top_tags": top}


def write_trends_md(cfg, today, kws, per_kw, vids, chans, days, path, our_id):
    L = [f"# 장르 동향 — 일본 YouTube 최근 {days}일 상위 영상 · {today} 수집", "",
         f"출처: YouTube Data API v3 search(order=viewCount, regionCode={cfg.get('region','JP')}, "
         f"relevanceLanguage={cfg.get('language','ja')}) + videos/channels. "
         "검색 상위는 YouTube 관련도 필터를 거치므로 「그 키워드로 찾았을 때 가장 많이 본 영상」으로 읽는다.", ""]
    chan_hits = {}
    for kw in kws:
        items = [vids[i] for i in per_kw[kw] if i in vids]
        if not items:
            L += [f"## {kw}", "", "결과 없음.", ""]
            continue
        titles = [v["snippet"]["title"] for v in items]
        longs = [iso_dur(v["contentDetails"]["duration"]) for v in items
                 if iso_dur(v["contentDetails"]["duration"]) > 180]
        pat = title_patterns(titles)
        L += [f"## {kw}", "",
              f"- 제목 길이 중앙값 {pat['len_median']:.0f}자 · 【】태그 사용 {pat['tag_ratio']*100:.0f}% · "
              f"자주 쓰는 태그: {', '.join(f'【{t}】{c}' for t, c in pat['top_tags']) or '없음'}",
              f"- 본편(3분 초과) 길이 중앙값 {fmt_dur(int(median(longs))) if longs else '—'} · "
              f"쇼츠 비율 {sum(1 for v in items if iso_dur(v['contentDetails']['duration'])<=180)/len(items)*100:.0f}%",
              "",
              "| # | 조회 | 채널(구독) | 길이 | 공개일 | 제목 |", "|---|---|---|---|---|---|"]
        for k, v in enumerate(items[:10], 1):
            ch = chans.get(v["snippet"]["channelId"], {})
            subs = n(ch.get("statistics", {}).get("subscriberCount"))
            L.append(f"| {k} | {fmt_n(n(v['statistics'].get('viewCount')))} | "
                     f"{short_title(v['snippet']['channelTitle'], 14)}({subs:,}) | "
                     f"{fmt_dur(iso_dur(v['contentDetails']['duration']))} | {jst_date(v['snippet']['publishedAt'])} | "
                     f"{short_title(v['snippet']['title'], 40)} |")
        L.append("")
        for v in items:
            c = v["snippet"]["channelId"]
            chan_hits.setdefault(c, set()).add(kw)
    # 자주 보이는 채널
    L += ["## 여러 키워드에 걸친 채널(경쟁·참고 후보)", "",
          "| 채널 | 구독 | 영상 수 | 걸린 키워드 |", "|---|---|---|---|"]
    ranked = sorted(chan_hits.items(), key=lambda x: (-len(x[1]), x[0]))
    for c, ks in ranked[:15]:
        if len(ks) < 2:
            continue
        ch = chans.get(c, {})
        st = ch.get("statistics", {})
        mark = " ★우리" if c == our_id else ""
        L.append(f"| {short_title(ch.get('snippet', {}).get('title', c), 20)}{mark} | "
                 f"{n(st.get('subscriberCount')):,} | {n(st.get('videoCount'))} | {', '.join(sorted(ks))} |")
    L += ["", "## 기획 적용(제21장 3)", "",
          "- 소재 키워드 상위 3편과 같은 반전 구조면 반전 또는 소재를 바꾼다.",
          "- 본편 길이는 해당 키워드 본편 중앙값 ±2분 안(채널 규격 10~11분과 겹치는지 확인).",
          "- 제목 앞 30자에 장르 태그 + 반전 핵심(제13장 6). 상위 영상의 태그 표기를 그대로 쓰되 실존 인물·기업명은 쓰지 않는다.",
          ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=dt.datetime.now(JST).strftime("%Y-%m-%d"))
    ap.add_argument("--out", default="docs/분석")
    ap.add_argument("--config", default="scripts/yt_config.json")
    ap.add_argument("--keyword", action="append", default=[], help="이번 작품 소재 키워드(임시 추가)")
    ap.add_argument("--no-search", action="store_true", help="장르 검색 생략(할당량 절약)")
    ap.add_argument("--no-comments", action="store_true")
    a = ap.parse_args()

    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    os.makedirs(a.out, exist_ok=True)

    ch, snap, rows, prev_date, ai_hits, new_comments = collect_channel(cfg, a.date, a.out, not a.no_comments)
    p1 = os.path.join(a.out, f"{a.date}-채널수치.md")
    write_channel_md(cfg, a.date, ch, snap, rows, prev_date, ai_hits, new_comments, p1)
    with open(p1, encoding="utf-8") as f, open(os.path.join(a.out, "최신-채널수치.md"), "w", encoding="utf-8") as g:
        g.write(f.read())
    print(f"[채널] 영상 {len(rows)}편 · 누적 조회 {snap['channel']['views']:,} · 구독 {snap['channel']['subscribers']} "
          f"· AI 언급 댓글 {len(ai_hits)}건 → {p1}")

    if not a.no_search:
        kws, per_kw, vids, chans, days = collect_trends(cfg, a.date, a.keyword)
        p2 = os.path.join(a.out, f"{a.date}-장르동향.md")
        write_trends_md(cfg, a.date, kws, per_kw, vids, chans, days, p2, cfg["channel_id"])
        with open(p2, encoding="utf-8") as f, open(os.path.join(a.out, "최신-장르동향.md"), "w", encoding="utf-8") as g:
            g.write(f.read())
        print(f"[동향] 키워드 {len(kws)}개 · 영상 {len(vids)}편 · 채널 {len(chans)}개 → {p2}")


if __name__ == "__main__":
    main()
