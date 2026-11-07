#!/usr/bin/env python3
"""흥행 스토리 3관문 분석(고니감독님 지시 2026-11-07 「30선이 아니어도 유사 흥행 스토리를 분석해 적용, 구독·조회·이탈 최소 기준이 있어야」).

검색(search.list)을 쓰지 않는다 — 이 프로젝트는 search.list 「하루 100회」 상한이 따로 있다(2026-11-07 실증, HTTP 429
`defaultSearchListPerDayPerProject`, 창은 매일 17:00 JST에 초기화). 대신 흥행 30선 파일(docs/분석/흥행30선/최신-*.md)에
오른 채널들의 업로드 전부(채널당 최근 최대 200편)를 playlistItems로 받아(약 400유닛, 검색 0회) 3관문으로 거른다.

3관문(모두 통과해야 「참고 흥행 스토리」):
  ① 조회  본편 ≥3만 회 & 같은 채널·같은 형식 중앙값의 2.5배↑ / 쇼츠 ≥50만 회 & 3배↑   (채널 힘이 아니라 이야기 힘)
  ② 구독  조회 ÷ 채널 구독자 ≥ 본편 3배·쇼츠 5배, 채널 구독 30만 이하                 (구독자 밖 새 시청자에게 도달 = 구독 전환 잠재력)
  ③ 이탈  본편 좋아요율 ≥0.4%·댓글율 ≥0.01%·길이 ≥8분 / 쇼츠 좋아요율 ≥1.0%           (만족·유지의 공개 대리 지표)
  공통: 공개 7일 이상.  ※ 경쟁 영상의 실제 유지율은 공개 API로 볼 수 없다 — ③은 대리 지표다.

사용법:
  python3 scripts/yt_story_gate.py [--plan "이름=정규식" ...] [--skip-genre スカッと-main] [--cache <json>]
  예: python3 scripts/yt_story_gate.py --plan "離婚届=離婚届|離婚当日|暗証番号|借金|優しい嘘" --plan "犬=犬|愛犬|猫"
산출: docs/분석/<날짜>-흥행스토리-3관문.md (유형별 통과율 표 · 기획 요소별 근거 · 통과작 목록)
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import statistics as st
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
B = "https://www.googleapis.com/youtube/v3/"
JST = dt.timezone(dt.timedelta(hours=9))

GATE = dict(main=dict(views=30000, up=2.5, mult=3, like=0.4, cm=0.01, sec=480),
            short=dict(views=500000, up=3.0, mult=5, like=1.0), subs_max=300000, age_days=7)

TAGS = {
    "正体·身分(정체)": r"正体|会長|社長|御曹司|財閥|大企業|CEO|資産家|大富豪|理事長",
    "理由(이유)": r"理由|わけ|ワケ|なぜ|どうして",
    "手紙·日記·遺言(편지)": r"手紙|遺書|日記|ノート|メモ|遺言|便箋|年賀状",
    "恩返し·再会(보은)": r"恩返し|あの時の|再会|恩人|助けた|貸した|年後",
    "死別·最期(사별)": r"亡き|亡くなった|天国|最期|葬儀|葬式|遺影|余命",
    "隠した献身·嘘(숨긴 헌신)": r"隠し|秘密|内緒|嘘|黙って|知らなかった|知っていた",
    "介護·認知症(간병)": r"介護|認知症|寝たきり|施設",
    "嫁姑·義実家(시댁)": r"姑|義母|義父|義実家|嫁いびり|トメ",
    "夫婦·離婚(부부)": r"離婚|夫婦|夫が|妻が|結婚記念",
    "親子·父(아버지)": r"父|親父|お父さん",
    "親子·母(어머니)": r"母|お母さん|おふくろ",
    "動物(동물)": r"犬|猫|愛犬|ワンちゃん|保護猫",
    "仕事·職場(직장)": r"上司|部長|課長|社員|新人|クビ|左遷|退職|定年",
    "交通·公共(교통)": r"電車|バス|優先席|駅|タクシー|新幹線",
    "子ども·学校(학교)": r"息子|娘|学校|先生|小学|中学|高校",
    "お金·借金(돈)": r"借金|万円|億|通帳|貯金|年収",
    "毎朝·毎晩(반복)": r"毎晩|毎朝|毎日|毎年|毎週|いつも",
    "期限·最後(기한)": r"最後の日|最終日|あと[一二三四五六七八九十\d]|日後|期限|残り|最後の",
    "電話·通信(전화)": r"電話|通報|無言|LINE|メール|留守電",
    "老人(노인)": r"老人|おばあさん|おじいさん|祖母|祖父|おばあちゃん|おじいちゃん|老婦人",
}


def api(res, **p):
    for k in range(5):
        try:
            return json.load(urllib.request.urlopen(B + res + "?" + urllib.parse.urlencode(p)))
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(3 * (k + 1))
    raise SystemExit("429 반복 — 잠시 뒤 다시")


def dur(s):
    m = re.match(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s)
    h, mi, se = (int(x or 0) for x in m.groups())
    return h * 3600 + mi * 60 + se


def fetch(skip):
    ids = {}
    for f in glob.glob(os.path.join(ROOT, "docs", "분석", "흥행30선", "최신-*.md")):
        g = os.path.basename(f)[3:-3]
        if g in skip:
            continue
        for v in re.findall(r"id:([A-Za-z0-9_-]{11})", open(f, encoding="utf-8").read()):
            ids[v] = g
    vl, ch = list(ids), {}
    for j in range(0, len(vl), 50):
        for v in api("videos", part="snippet", id=",".join(vl[j:j + 50]))["items"]:
            ch.setdefault(v["snippet"]["channelId"], set()).add(ids[v["id"]])
    cl, info = list(ch), {}
    for j in range(0, len(cl), 50):
        for c in api("channels", part="snippet,statistics,contentDetails", id=",".join(cl[j:j + 50]))["items"]:
            info[c["id"]] = dict(t=c["snippet"]["title"], subs=int(c["statistics"].get("subscriberCount", 0) or 0),
                                 up=c["contentDetails"]["relatedPlaylists"]["uploads"], g=sorted(ch[c["id"]]))
    out = []
    for cid, c in info.items():
        if c["subs"] > GATE["subs_max"]:
            continue
        tok, got = None, []
        for _ in range(4):
            p = dict(part="contentDetails", playlistId=c["up"], maxResults=50)
            if tok:
                p["pageToken"] = tok
            try:
                d = api("playlistItems", **p)
            except Exception:
                break
            got += [i["contentDetails"]["videoId"] for i in d["items"]]
            tok = d.get("nextPageToken")
            if not tok:
                break
        for j in range(0, len(got), 50):
            for v in api("videos", part="snippet,statistics,contentDetails", id=",".join(got[j:j + 50]))["items"]:
                s = v["statistics"]
                out.append(dict(id=v["id"], cid=cid, ch=c["t"], subs=c["subs"], t=v["snippet"]["title"],
                                date=v["snippet"]["publishedAt"][:10], views=int(s.get("viewCount", 0) or 0),
                                likes=int(s.get("likeCount", 0) or 0), cms=int(s.get("commentCount", 0) or 0),
                                sec=dur(v["contentDetails"]["duration"])))
    return out


def gate(videos, today):
    V = [v for v in videos if v["views"] > 0 and (today - dt.date.fromisoformat(v["date"])).days >= GATE["age_days"]]
    base = collections.defaultdict(list)
    for v in V:
        base[(v["cid"], v["sec"] > 180)].append(v["views"])
    med = {k: st.median(x) for k, x in base.items()}
    for v in V:
        sh = v["sec"] <= 180
        g = GATE["short" if sh else "main"]
        v["sh"] = sh
        v["up"] = v["views"] / med[(v["cid"], not sh)]
        v["mult"] = v["views"] / max(v["subs"], 1)
        v["lr"] = v["likes"] / v["views"] * 100
        v["cr"] = v["cms"] / v["views"] * 100
        v["g1"] = v["views"] >= g["views"] and v["up"] >= g["up"]
        v["g2"] = v["mult"] >= g["mult"]
        v["g3"] = v["lr"] >= g["like"] and (sh or (v["cr"] >= g["cm"] and v["sec"] >= g["sec"]))
        v["ok"] = v["g1"] and v["g2"] and v["g3"]
    return V


def table(V, pats, title):
    L = [f"### {title}", "", "| 유형 | 본편 통과/편수 | 본편 배율 | 쇼츠 통과/편수 | 쇼츠 배율 | 쇼츠 통과작 이야기 효과 중앙 |", "|---|---|---|---|---|---|"]
    base = {sh: (sum(v["ok"] for v in V if v["sh"] == sh) / max(1, sum(1 for v in V if v["sh"] == sh))) for sh in (False, True)}
    for name, p in pats.items():
        cells = []
        for sh in (False, True):
            T = [v for v in V if v["sh"] == sh and re.search(p, v["t"])]
            O = [v for v in T if v["ok"]]
            lift = (len(O) / len(T) / base[sh]) if T and base[sh] else 0
            cells.append((len(O), len(T), lift, st.median([v["up"] for v in O]) if O else 0))
        (mo, mn, ml, _), (so, sn, sl, su) = cells
        L.append(f"| {name} | {mo}/{mn} | {ml:.2f} | {so}/{sn} | {sl:.2f} | {su:.1f}배 |")
    return L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", action="append", default=[], help='"이름=정규식" (기획 요소 근거 검사)')
    ap.add_argument("--skip-genre", action="append", default=["スカッと-main"], help="제외할 30선 파일(대형 채널 독점 분야)")
    ap.add_argument("--cache", help="받아 둔 목록 JSON(있으면 재사용, 없으면 저장)")
    a = ap.parse_args()
    today = dt.datetime.now(JST).date()
    if a.cache and os.path.exists(a.cache):
        videos = json.load(open(a.cache, encoding="utf-8"))
    else:
        videos = fetch(set(a.skip_genre))
        if a.cache:
            json.dump(videos, open(a.cache, "w", encoding="utf-8"), ensure_ascii=False)
    V = gate(videos, today)
    M = [v for v in V if not v["sh"]]
    S = [v for v in V if v["sh"]]
    om, os_ = [v for v in M if v["ok"]], [v for v in S if v["ok"]]
    L = [f"# 흥행 스토리 3관문 분석 {today}", "",
         f"대상: 흥행 30선 채널 {len({v['cid'] for v in V})}곳의 업로드 {len(V):,}편(본편 {len(M):,} · 쇼츠 {len(S):,}), 검색 0회.", "",
         "| 관문 | 본편 기준 | 쇼츠 기준 | 본편 통과 | 쇼츠 통과 |", "|---|---|---|---|---|",
         f"| ① 조회(이야기 힘) | ≥3만 & 채널 중앙값 2.5배↑ | ≥50만 & 3배↑ | {sum(v['g1'] for v in M)} | {sum(v['g1'] for v in S)} |",
         f"| ② 구독(새 시청자 도달) | 조회/구독 ≥3배, 구독 ≤30만 | ≥5배 | {sum(v['g2'] for v in M)} | {sum(v['g2'] for v in S)} |",
         f"| ③ 이탈(만족 대리) | 좋아요 ≥0.4%·댓글 ≥0.01%·≥8분 | 좋아요 ≥1.0% | {sum(v['g3'] for v in M)} | {sum(v['g3'] for v in S)} |",
         f"| **3관문 모두** | | | **{len(om)} ({len(om)/max(1,len(M))*100:.1f}%)** | **{len(os_)} ({len(os_)/max(1,len(S))*100:.1f}%)** |", "",
         "배율 = 그 유형의 3관문 통과율 ÷ 전체 통과율(1.0 = 평균, 1.2 이상 = 근거 있음). 제목 키워드 기준이므로 오탐은 통과작 목록에서 눈으로 거른다.", ""]
    L += table(V, TAGS, "이야기 유형별")
    if a.plan:
        pats = dict(x.split("=", 1) for x in a.plan)
        L += [""] + table(V, pats, "기획 요소별 근거")
        for name, p in pats.items():
            O = sorted([v for v in V if v["ok"] and re.search(p, v["t"])], key=lambda v: -v["views"])[:5]
            L += ["", f"- **{name}** 통과작: " + ("없음" if not O else " / ".join(
                f"{v['t'][:40]}({v['views']:,}회·채널 {v['up']:.1f}배·{'쇼츠' if v['sh'] else '본편'}, {v['id']})" for v in O))]
    for lab, O in (("본편", om), ("쇼츠", os_)):
        L += ["", f"## 3관문 통과 {lab} 상위 40(조회순)", "", "| 조회 | 채널 대비 | 구독 대비 | 좋아요율 | 길이 | 제목 | ID |", "|---|---|---|---|---|---|---|"]
        for v in sorted(O, key=lambda v: -v["views"])[:40]:
            L.append(f"| {v['views']:,} | {v['up']:.1f}배 | {v['mult']:.0f}배 | {v['lr']:.2f}% | {v['sec']//60}:{v['sec']%60:02d} | {v['t'][:60].replace('|','／')} | {v['id']} |")
    out = os.path.join(ROOT, "docs", "분석", f"{today}-흥행스토리-3관문.md")
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[:12]))
    print("저장:", out)


if __name__ == "__main__":
    main()
