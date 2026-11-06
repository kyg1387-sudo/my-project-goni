#!/usr/bin/env python3
"""쇼츠 → 본편 전환 장치 자동 점검 (제22장 5·11, 지속 개선 원칙 4).

2026-11-07 실증: 설명 빈칸 양식(「（本編URL）」「（本編リンク）」, 한국어 「(아래 표의 한 줄 요약)」)이
11편에 그대로 공개, 링크 없는 설명 4편, 고정 댓글 0편, 계약사원 쇼츠 제목 한 칸 밀림 4편.

사용법: python3 scripts/yt_shorts_link_check.py [--map docs/분석/쇼츠-본편맵.json]
맵 파일: {"<본편 ID>": ["<쇼츠 ID>", ...], ...}
검사: ① 설명 첫 줄에 해당 본편 링크 ② 채널 댓글에 해당 본편 링크(고정 여부는 API로 못 봄)
      ③ 제목·설명의 한글·빈칸 양식 문구 ④ 다른 작품 링크 혼입 ⑤ 제목 맨 앞 【】 태그(경고)
환경 goni 프록시가 키를 넣으므로 key= 를 붙이지 않는다(제21장 2).
"""
import json, re, sys, urllib.request

B = "https://www.googleapis.com/youtube/v3/"
PLACEHOLDER = re.compile(r"（本編URL）|（本編リンク）|本編URL|[가-힣]")


def get(u):
    return json.load(urllib.request.urlopen(B + u))


def main():
    path = "docs/분석/쇼츠-본편맵.json"
    if "--map" in sys.argv:
        path = sys.argv[sys.argv.index("--map") + 1]
    m = json.load(open(path, encoding="utf-8"))
    ids = [s for v in m.values() for s in v]
    info = {}
    for k in range(0, len(ids), 50):
        for v in get("videos?part=snippet&id=" + ",".join(ids[k:k + 50])).get("items", []):
            info[v["id"]] = v["snippet"]
    fails = 0
    for main_id, shorts in m.items():
        for s in shorts:
            sn = info.get(s)
            if not sn:
                print(f"{s}: 비공개·예약 또는 없음(API로 확인 불가)")
                continue
            first = (sn["description"].splitlines() or [""])[0]
            texts = [t["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
                     for t in get(f"commentThreads?part=snippet&videoId={s}&maxResults=20").get("items", [])]
            prob = []
            if main_id not in first:
                prob.append("설명 첫 줄 본편 링크 없음")
            if not any(main_id in t for t in texts):
                prob.append("고정 댓글(본편 링크) 없음")
            if PLACEHOLDER.search(sn["title"] + sn["description"]):
                prob.append("빈칸 양식·한글 노출")
            other = [x for x in m if x != main_id and any(x in t for t in texts + [sn["description"]])]
            if other:
                prob.append(f"다른 작품 링크 {other}")
            warn = "" if sn["title"].startswith("【") else " (경고: 제목 앞 【】 태그 없음)"
            fails += bool(prob)
            print(f"{s} {'FAIL ' + ' / '.join(prob) if prob else 'PASS'}{warn} | {sn['title'][:32]}")
    print(f"\nFAIL {fails} / {len(ids)}  — 고정 여부·관련 동영상은 스튜디오에서 확인")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
