#!/usr/bin/env python3
"""일일 점검 — 고니감독님 요청 시(「점검」) 실행해 채널 전체를 검사하고 「지금 할 일」을 우선순위로 낸다.

사용법: python3 scripts/yt_daily_check.py [--out docs/분석/일일점검-<날짜>.md]
검사(공개 데이터만, 약 30~60유닛):
  A. 쇼츠: 설명 첫 줄 본편 링크 · 채널 댓글(고정 댓글 후보) 본편 링크 · 【】 태그 · 한글/빈칸 양식 노출 ·
     자정(0時) 공개 · 다른 작품 링크 혼입 · 맵(docs/분석/쇼츠-본편맵.json)에 없는 새 쇼츠
  B. 본편: 장르 재생목록(スカッと·感動) 미등록 · 제목 앞 【】 · 설명 첫 줄
  C. 성과: 직전 스냅샷(docs/분석/history/channel-*.json) 대비 조회 증감 상위·정체, 좋아요율
  D. 댓글: 채널 답글 없는 시청자 댓글(답글 문안 `docs/분석/댓글답글-문안.md`) · 「AI·不自然」 언급
  E. 운영: 등록 대장 studio_synced 경과일 · 진행 중 A/B 테스트 경과일
고정 여부·관련 동영상·썸네일 테스트 결과는 API로 볼 수 없으므로 「스튜디오 확인」 항목으로 낸다.
환경 goni 프록시가 키를 넣으므로 key= 를 붙이지 않는다(제21장 2).
"""
import datetime as dt
import glob
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
B = "https://www.googleapis.com/youtube/v3/"
JST = dt.timezone(dt.timedelta(hours=9))
CH = "UCUyQLjV4AzMd06WUl3yMzyw"
PLAYLISTS = {"スカッと": "PLR6E1N7S9lz8", "感動": "PLALpkojDUWmo"}
PLACEHOLDER = re.compile(r"（本編URL）|（本編リンク）|[가-힣]")
AI_WORDS = re.compile(r"AI|ＡＩ|不自然|違和感|作り物|CG")


def api(res, **p):
    return json.load(urllib.request.urlopen(B + res + "?" + urllib.parse.urlencode(p)))


def iso(s):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
    h, mi, se = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + se


def uploads():
    ids, tok = [], None
    while True:
        p = dict(part="contentDetails", playlistId="UU" + CH[2:], maxResults=50)
        if tok:
            p["pageToken"] = tok
        d = api("playlistItems", **p)
        ids += [i["contentDetails"]["videoId"] for i in d["items"]]
        tok = d.get("nextPageToken")
        if not tok:
            return ids


def details(ids):
    out = {}
    for k in range(0, len(ids), 50):
        for v in api("videos", part="snippet,contentDetails,statistics", id=",".join(ids[k:k + 50]))["items"]:
            out[v["id"]] = v
    return out


def playlist_ids(pl):
    d = api("playlistItems", part="contentDetails", playlistId=pl, maxResults=50)
    return {i["contentDetails"]["videoId"] for i in d.get("items", [])}


def comments(vid):
    try:
        return api("commentThreads", part="snippet,replies", videoId=vid, maxResults=50, order="time").get("items", [])
    except Exception:
        return []


def main():
    today = dt.datetime.now(JST).date()
    out_path = os.path.join(ROOT, "docs", "분석", f"일일점검-{today}.md")
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    vids = details(uploads())
    mains = {k: v for k, v in vids.items() if iso(v["contentDetails"]["duration"]) > 180}
    shorts = {k: v for k, v in vids.items() if k not in mains}
    mp = json.load(open(os.path.join(ROOT, "docs", "분석", "쇼츠-본편맵.json"), encoding="utf-8"))
    short2main = {s: m for m, ss in mp.items() for s in ss}
    req = []          # (우선순위, 분류, 영상, 할 일)
    midnight = []

    # A. 쇼츠
    for sid, v in shorts.items():
        sn = v["snippet"]; t = sn["title"]; desc = sn["description"]
        first = (desc.splitlines() or [""])[0]
        pub = dt.datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00")).astimezone(JST)
        main_id = short2main.get(sid)
        if PLACEHOLDER.search(t + desc):
            req.append((1, "쇼츠·빈칸/한글 노출", f"{t[:28]} ({sid})", "설명·제목의 빈칸 양식(（本編リンク）)·한글 제거"))
        if main_id is None:
            linked = [m for m in mains if m in desc]
            req.append((1, "쇼츠·맵 미등록", f"{t[:28]} ({sid})",
                        f"쇼츠-본편맵.json에 추가 필요 — 설명에서 찾은 본편: {linked or '없음'} → 본편을 알려 주세요"))
            continue
        cs = comments(sid)
        own = [c for c in cs if c["snippet"]["topLevelComment"]["snippet"]["authorChannelId"]["value"] == CH]
        if main_id not in first:
            req.append((1, "쇼츠·설명", f"{t[:28]} ({sid})", f"설명 첫 줄을 `▶本編：https://youtu.be/{main_id}` 로"))
        if not any(main_id in c["snippet"]["topLevelComment"]["snippet"]["textOriginal"] for c in own):
            req.append((1, "쇼츠·고정 댓글", f"{t[:28]} ({sid})", f"본편 링크 댓글 달고 고정(본편 {main_id})"))
        others = [m for m in mains if m != main_id and m in desc]
        if others:
            req.append((1, "쇼츠·다른 작품 링크", f"{t[:28]} ({sid})", f"설명에서 {others} 제거"))
        if not t.startswith("【"):
            req.append((3, "쇼츠·제목 태그", f"{t[:28]} ({sid})", "제목 맨 앞에 【スカッと】/【感動】"))
        if pub.hour == 0 and pub.minute == 0:
            midnight.append(sid)

    if midnight:
        req.append((3, "쇼츠·자정 공개(누적)", f"{len(midnight)}편", "이미 0時에 공개된 쇼츠 — 앞으로 예약은 오후 12:00/6:00 직접 입력(제22장 6)"))

    # B. 본편 재생목록·제목
    in_pl = set().union(*[playlist_ids(p) for p in PLAYLISTS.values()])
    for mid, v in mains.items():
        t = v["snippet"]["title"]
        if mid not in in_pl:
            req.append((2, "본편·재생목록", f"{t[:28]} ({mid})", "장르 재생목록(スカッと 또는 感動)에 추가"))
        if not t.startswith("【") and not t.startswith("「"):
            req.append((3, "본편·제목 태그", f"{t[:28]} ({mid})", "제목 앞 30자에 【태그】(제13장 6)"))

    # C. 성과(직전 스냅샷 대비)
    snaps = sorted(glob.glob(os.path.join(ROOT, "docs", "분석", "history", "channel-*.json")))
    prev = {}
    prev_date = None
    if snaps:
        pj = json.load(open(snaps[-1], encoding="utf-8"))
        prev = {r["id"]: r for r in pj["videos"]}
        prev_date = pj.get("date")
    perf = []
    for k, v in vids.items():
        st = v["statistics"]; views = int(st.get("viewCount", 0)); likes = int(st.get("likeCount", 0))
        dv = views - prev[k]["views"] if k in prev else None
        perf.append((k, v["snippet"]["title"], "본편" if k in mains else "쇼츠", views, dv, likes / views * 100 if views else 0))
    perf.sort(key=lambda r: -(r[4] or 0))

    # D. 댓글(본편+쇼츠 전부, 채널 답글 없는 시청자 댓글)
    pending, ai_hits = [], []
    for k, v in vids.items():
        if int(v["statistics"].get("commentCount", 0)) == 0:
            continue
        for c in comments(k):
            top = c["snippet"]["topLevelComment"]["snippet"]
            if top["authorChannelId"]["value"] == CH:
                continue
            replied = any(r["snippet"]["authorChannelId"]["value"] == CH for r in c.get("replies", {}).get("comments", []))
            txt = top["textOriginal"].replace("\n", " ")
            if AI_WORDS.search(txt):
                ai_hits.append((k, txt[:60]))
            if not replied:
                pending.append((k, v["snippet"]["title"][:24], top["authorDisplayName"], txt[:60]))
    for k, t, a, txt in pending:
        req.append((2, "댓글·답글", f"{t} ({k})", f"{a}: 「{txt}」 → 하트 + 답글(문안 파일)"))
    for k, txt in ai_hits:
        req.append((1, "댓글·AI 언급", k, f"「{txt}」 → 시각·장면 확인, 실증 기록(KPI 0건)"))

    # E. 운영
    reg = json.load(open(os.path.join(ROOT, "docs", "등록현황-美談ものがたり.json"), encoding="utf-8"))
    for kind, d0 in reg.get("studio_synced", {}).items():
        age = (today - dt.date.fromisoformat(d0)).days
        if age > 2:
            req.append((2, "운영·예약 대조", f"studio_synced.{kind}={d0}", f"{age}일 경과 — 스튜디오 「예약됨」({kind}) 캡처 요청(제0장 9④)"))
    ab = open(os.path.join(ROOT, "docs", "분석", "AB테스트-기록.md"), encoding="utf-8").read()
    for m in re.finditer(r"## #(\d+) (\S+) 본편 (\S+) — 썸네일만 3안 \((\d{4}-\d\d-\d\d) 시작", ab):
        age = (today - dt.date.fromisoformat(m.group(4))).days
        if age >= 7:
            req.append((2, "운영·A/B 결과", f"#{m.group(1)} {m.group(2)}", f"시작 {age}일 — 스튜디오 「테스트 보고서」 캡처 요청 → 승자 기록"))

    req.sort(key=lambda r: r[0])
    L = [f"# 일일 점검 {today} (영상 {len(vids)}: 본편 {len(mains)}·쇼츠 {len(shorts)})", "",
         f"요청 {len(req)}건 — 1 = 오늘 반드시 · 2 = 이번 주 · 3 = 여유 있을 때", "",
         "| 우선 | 분류 | 영상 | 할 일 |", "|---|---|---|---|"]
    L += [f"| {p} | {c} | {v} | {t} |" for p, c, v, t in req]
    L += ["", f"## 조회 증감(직전 스냅샷 {prev_date} 대비, 상위 10)", "", "| 영상 | 종류 | 조회 | 증가 | 좋아요율 |", "|---|---|---|---|---|"]
    L += [f"| {t[:30]} | {k2} | {vw:,} | {('+' + format(dv, ',')) if dv is not None else '신규'} | {lr:.2f}% |" for _, t, k2, vw, dv, lr in perf[:10]]
    L += ["", "## 스튜디오에서만 확인 가능(API로 안 보임)", "",
          "- 고정 댓글이 실제 「고정」 상태인지, 쇼츠 「관련 동영상」 연결, 썸네일 A/B 진행·결과, 예약 영상(비공개)"]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[:12 + len(req)]))
    print("\n저장:", out_path)


if __name__ == "__main__":
    main()
