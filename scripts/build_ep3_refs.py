#!/usr/bin/env python3
"""EP3 캐릭터 시트 · 로케이션 시트 프롬프트 생성기.

docs/영화제작규칙집.md 2장(캐릭터 시트)·3장(로케이션 시트) 규격을 그대로 따른다.
무료 단계(텍스트만 생성, API 호출 없음) — 실제 이미지 생성은 별도 승인 후 진행.

주의(규칙집 §2 "왜 이 구조인가"): 시트 안에 얼굴을 두 번 이상 넣으면 도플갱어가
생긴다 — 얼굴 정보는 오른쪽 클로즈업 한 곳에만. 왼쪽 전신은 목에서 잘라 얼굴이
프레임 밖으로 나가게 한다.

주의(비용 원칙 #4, 화면 속 글자): 생성 모델은 한글은 물론 라틴 문자도 정교하게
못 쓴다(실증). 시트 헤더에 들어가는 문자는 이미지에 실제로 렌더링되는 텍스트이므로
글자 수가 적고 폰트가 단순한 영문으로 표기해 실패 확률을 낮춘다 — 한글 이름은
프로젝트 문서(이 파일이 만드는 리뷰용 .md)에만 병기하고, 프롬프트 안 텍스트는
영문으로 둔다. 최종 영상에는 이 시트가 노출되지 않으므로(레퍼런스 전용) 시청자가
볼 일이 없다.

docs/영화제작규칙집.md 4장(스토리보드 콘택트시트) 규격도 이 파일에서 함께 만든다 —
scripts/build_ep3_assets.py의 SECTIONS를 그대로 읽어와 같은 소스에서 생성하므로
대본을 고치면 컷 프롬프트·스토리보드가 항상 같이 갱신된다(드리프트 방지).

사용법: python3 scripts/build_ep3_refs.py
"""

import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ep3_assets as ep3  # noqa: E402 — SECTIONS/EN_NAME/SHEET_REF 재사용

# 캡션 정리용: 긴 장소 상수 접두어와 인물 고정 식별자 괄호를 짧은 이름으로 치환한다.
# (그대로 두면 "…70대 후반 한국 여성(마르고 굽은 허리, 깊은…" 처럼 괄호 중간에서
# 잘려 알아볼 수 없는 캡션이 나온다 — 반드시 사람이 읽는 라벨이므로 손봐야 한다.)
LOCATION_PREFIXES = [ep3.GUARD_BOOTH, ep3.APT_GATE, ep3.DEMOLITION, ep3.ALLEY_NIGHT, ep3.JUNKYARD]
NAME_PATTERNS = [
    (re.compile(r"60대 초반 한국 남성 아파트 경비원\([^)]*\)"), "김씨"),
    (re.compile(r"70대 후반 한국 여성\([^)]*\)"), "할머니"),
    (re.compile(r"50대 한국 남성 고물상 주인\([^)]*\)"), "최사장"),
]
# 김씨/할머니는 모음(ㅣ)으로 끝나 원문(경비원/여성 — 자음 받침)에 붙어 있던 조사가
# 그대로 남으면 "김씨이", "할머니을"처럼 어색해진다 — 좁은 범위로만 교정.
PARTICLE_FIXES = [
    (re.compile(r"(김씨|할머니)이(?!\w)"), r"\1가"),
    (re.compile(r"(김씨|할머니)을(?!\w)"), r"\1를"),
    (re.compile(r"(김씨|할머니)은(?!\w)"), r"\1는"),
]
OBJECT_PATTERNS = [(re.compile(re.escape(ep3.CART)), "리어카")]

STYLE_NOTE = "modern Korean apartment complex, contemporary, worn everyday clothing"

CHARACTERS = [
    dict(
        slug="kim",
        name_kr="경비원 김씨 (김영곤)",
        header="GUARD KIM",
        height="Height: 170cm",
        personality="Quiet, dutiful, gentle beneath a gruff exterior",
        voice="Voice: low, calm, few words",
        age_desc="60대 초반 한국 남성(a Korean man in his early 60s)",
        wardrobe=("plain dark navy security guard uniform, a blank white nameplate with "
                  "absolutely no text or lettering on the left chest, a black leather duty "
                  "belt with an old handheld radio, black work shoes"),
        body="sturdy build, slightly stooped shoulders from long standing, weathered hands",
        expression="calm, neutral, watchful",
        hair="short salt-and-pepper buzz cut, round face",
        headwear="no hat",
        identifiers=["가슴의 흰색 무지 명찰표(글자 없음)", "짧은 반백 스포츠머리", "짙은 감색 유니폼"],
        note=("**카메오 확정(시리즈 전편 공통, CLAUDE.md 참고)**: 경비원 김씨 역은 감독 "
              "김영곤 본인 얼굴로 EP1부터 마지막 편까지 출연한다. 아래 프롬프트는 사진이 "
              "없을 때 쓰는 순수 텍스트 생성용 폴백이다 — **실제로는 감독 정면 사진을 "
              "이미지 편집 모델(예: 얼굴을 보존하며 의상만 바꾸는 nano-banana류)에 입력해 "
              "만들어야 한다.** 사진을 받으면 이 시트를 그 사진 기반 image-to-image "
              "프롬프트로 다시 만들 것 — 지금 프롬프트로 먼저 생성하지 말 것."),
    ),
    dict(
        slug="grandma",
        name_kr="폐지 줍는 할머니",
        header="GRANDMOTHER",
        height="Height: 150cm",
        personality="Frail but fiercely independent, quietly warm",
        voice="Voice: soft, raspy, few words",
        age_desc="70대 후반 한국 여성(a Korean woman in her late 70s)",
        wardrobe=("a faded brown floral headscarf tied over her hair, a plain worn dark "
                  "brown baggy work trousers (\"monpe\") and a thick navy quilted jacket, "
                  "worn brown work gloves"),
        body="thin frame, stooped back, deeply wrinkled hands",
        expression="tired but gentle, quiet dignity",
        hair="grey hair mostly covered by the headscarf",
        headwear="faded brown floral headscarf",
        identifiers=["색 바랜 갈색 꽃무늬 두건", "굽은 허리", "해진 갈색 목장갑"],
    ),
    dict(
        slug="choi",
        name_kr="고물상 주인 최사장",
        header="CHOI - SCRAPYARD OWNER",
        height="Height: 173cm",
        personality="Gruff, businesslike, secretly soft-hearted",
        voice="Voice: brisk, low, businesslike",
        age_desc="50대 한국 남성(a Korean man in his 50s)",
        wardrobe=("a grease-stained plain grey work vest over a dark shirt, black work "
                  "gloves, a worn radio clipped to his belt"),
        body="stocky, sturdy build, calloused hands",
        expression="wary, businesslike",
        hair="short greying hair",
        headwear="no hat",
        identifiers=["기름때 묻은 무늬 없는 회색 작업 조끼", "짧게 깎은 희끗한 머리", "검은 목장갑"],
    ),
]

LOCATIONS = [
    dict(
        slug="guard-booth",
        name_kr="아파트 경비실 부스 내부",
        wide_day="the same small guard booth interior by daylight, sunlight through the window",
        wide_night="the same small guard booth interior at night, warm desk lamp light, dark window",
        pos1="close view of the narrow desk with old black-and-white CCTV monitors and a thermos",
        pos2="close view of the booth window looking out toward the apartment flower bed",
        common="a small apartment security guard booth interior, a narrow desk, several old "
               "black-and-white CCTV monitors, a thermos, a blank plain duty-roster chalkboard "
               "on the wall with no text",
    ),
    dict(
        slug="apt-gate",
        name_kr="아파트 단지 정문 앞 인도",
        wide_day="the same sidewalk by afternoon daylight, ordinary apartment complex",
        wide_night="the same sidewalk at evening dusk, streetlights just turning on",
        pos1="close view of the flower bed and low wall beside the sidewalk",
        pos2="close view of the sidewalk pavement leading toward the apartment gate",
        common="a sidewalk in front of an apartment complex main gate, a flower bed and a low "
               "wall, ordinary modern Korean apartment complex in the background",
    ),
    dict(
        slug="demolition-site",
        name_kr="재개발 철거 공터",
        wide_day="the same demolition site by late-afternoon daylight, dust in the air",
        wide_night="the same demolition site at night, one distant work light, empty and quiet",
        pos1="close view of the collapsed wall rubble and a blank plain safety notice board with no text",
        pos2="close view of the safety fence at the edge of the site",
        common="a demolition site mid-redevelopment, collapsed wall rubble, hazy dust, a safety "
               "fence, a blank plain white notice board with absolutely no text or lettering, "
               "completely empty of people",
    ),
    dict(
        slug="alley-night",
        name_kr="가로등 골목 (야간 수색)",
        wide_day="the same narrow alley by overcast daylight (rarely used, for continuity only)",
        wide_night="the same narrow alley at night, one working streetlamp, thin night mist",
        pos1="close view of the piles of stacked paper and cardboard against an old shutter door",
        pos2="close view of the cracked pavement under the single streetlamp",
        common="a narrow neighborhood alley with a single working streetlamp, piles of stacked "
               "paper and cardboard against old shutter doors, thin night mist, completely "
               "empty of people",
    ),
    dict(
        slug="junkyard",
        name_kr="고물상 마당",
        wide_day="the same scrapyard by daylight, ordinary working hours",
        wide_night="the same scrapyard at dusk, a single bare bulb glowing overhead",
        pos1="close view of the rusty scale and compressed bales of paper",
        pos2="close view of the old truck parked against a blank plain sheet-metal wall with no text",
        common="a small scrapyard, compressed bales of paper, a rusty scale, a bare bulb hanging "
               "overhead, an old truck, a blank plain corrugated sheet-metal wall with "
               "absolutely no text or lettering",
    ),
]


def character_prompt(c):
    return (
        "Character reference sheet, one single 16:9 image on a pure white background, "
        "photorealistic, soft studio lighting, minimal style, fashion-lookbook layout. "
        f"Top-left header in clean black sans-serif text: large bold title \"{c['header']}\", "
        f"then four small lines below it: \"{c['height']}\" / \"{c['personality']}\" / "
        f"\"{c['voice']}\" / \"Photorealistic, soft studio lighting, minimal style, "
        f"{STYLE_NOTE}\". Left half: full-body front view and full-body back view of the "
        f"same {c['age_desc']}, standing side by side, feet visible, both figures cropped "
        "at the neck so the head is cut off by the top edge of the frame — no face shown "
        f"on the left side. Wardrobe: {c['wardrobe']}. Body: {c['body']}. Right half: one "
        "large close-up portrait from the shoulders up, straight to camera, "
        f"{c['expression']}, {c['hair']}, {c['headwear']}. No text other than the header."
    )


def location_prompt(l):
    return (
        f"Location reference sheet, one single 16:9 image, a 2x2 grid of four labeled cells, "
        "clean white gutters between cells, small plain black caption text under each cell "
        "and nothing else. Photorealistic, natural lighting, no people in any cell. "
        f"Setting: {l['common']}. "
        f"Cell 1 (label \"DAY - WIDE\"): {l['wide_day']}. "
        f"Cell 2 (label \"NIGHT - WIDE\"): {l['wide_night']}. "
        f"Cell 3 (label \"KEY POSITION 1\"): {l['pos1']}. "
        f"Cell 4 (label \"KEY POSITION 2\"): {l['pos2']}. "
        "No text anywhere in the image other than the four cell labels."
    )


def write_char_files():
    lines_doc = ["# EP3 캐릭터 시트 프롬프트 (규칙집 §2 규격)", "",
                 "무료 단계 — 텍스트만 생성함(API 호출 없음). 실제 이미지 생성은 승인 후 진행.",
                 "",
                 "**시트 안 텍스트는 영문으로 둠**: 생성 모델이 한글은 물론 라틴 문자도 "
                 "정교하게 못 쓰기 때문에(실증), 글자 수가 적은 영문 라벨로 실패 확률을 "
                 "낮췄다. 이 시트는 레퍼런스 전용이라 시청자에게 노출되지 않는다.", ""]
    for c in CHARACTERS:
        prompt = character_prompt(c)
        path = os.path.join(ROOT, "assets", "character-sheets", f"{c['slug']}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt + "\n")
        lines_doc.append(f"## {c['name_kr']} (`{c['slug']}.txt`)")
        lines_doc.append("")
        lines_doc.append(f"- 고정 식별자: {', '.join(c['identifiers'])}")
        lines_doc.append(f"- 헤더 텍스트: \"{c['header']}\" / \"{c['height']}\" / "
                         f"\"{c['personality']}\" / \"{c['voice']}\"")
        if c.get("note"):
            lines_doc.append("")
            lines_doc.append(c["note"])
        lines_doc.append("")
        lines_doc.append("```")
        lines_doc.append(prompt)
        lines_doc.append("```")
        lines_doc.append("")
    with open(os.path.join(ROOT, "docs", "EP3-캐릭터시트.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines_doc) + "\n")
    print(f"캐릭터 시트 {len(CHARACTERS)}개 저장: assets/character-sheets/*.txt, "
          "docs/EP3-캐릭터시트.md")


def write_location_files():
    lines_doc = ["# EP3 로케이션 시트 프롬프트 (규칙집 §3 규격)", "",
                 "무료 단계 — 텍스트만 생성함(API 호출 없음). 실제 이미지 생성은 승인 후 진행.",
                 ""]
    for l in LOCATIONS:
        prompt = location_prompt(l)
        path = os.path.join(ROOT, "assets", "locations", f"{l['slug']}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt + "\n")
        lines_doc.append(f"## {l['name_kr']} (`{l['slug']}.txt`)")
        lines_doc.append("")
        lines_doc.append("```")
        lines_doc.append(prompt)
        lines_doc.append("```")
        lines_doc.append("")
    with open(os.path.join(ROOT, "docs", "EP3-로케이션시트.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines_doc) + "\n")
    print(f"로케이션 시트 {len(LOCATIONS)}개 저장: assets/locations/*.txt, "
          "docs/EP3-로케이션시트.md")


PROJECT = "EP3 김씨와 폐지 할머니"
MAX_PANELS = 5  # 규칙집 §4: 5개 초과 시 시트 분할


def short_caption(desc, limit=60):
    """전체 컷 묘사에서 스토리보드 패널용 짧은 캡션을 만든다.

    장소 고정 문구(수십 자)와 인물 고정 식별자 괄호(예: "70대 후반 한국 여성(마르고
    굽은 허리, …)")를 걷어내고 짧은 이름으로 바꾼 뒤에 자른다 — 그대로 자르면 괄호
    중간에서 끊겨 알아볼 수 없는 캡션이 나온다.
    """
    text = desc
    for loc in LOCATION_PREFIXES:
        if text.startswith(loc):
            text = text[len(loc):].lstrip(", ")
            break
    for pattern, short_name in NAME_PATTERNS:
        text = pattern.sub(short_name, text)
    for pattern, short_name in OBJECT_PATTERNS:
        text = pattern.sub(short_name, text)
    for pattern, repl in PARTICLE_FIXES:
        text = pattern.sub(repl, text)
    text = text.strip(", ")
    if not text:
        return desc[:limit]
    if len(text) <= limit:
        return text
    cut_at = text.rfind(",", 0, limit)
    return (text[:cut_at] if cut_at > 10 else text[:limit]).strip()


def storyboard_prompt(sec_name, chunk, part_label, all_speakers):
    ids = []
    for s in sorted(all_speakers):
        tag = {"김씨": "the guard Kim", "할머니": "the grandmother", "최사장": "Choi"}[s]
        ids.append(f"{tag} — see the reference character sheet for exact identifiers")
    id_block = " ".join(f"{i}." for i in ids) if ids else "No named characters in this scene."
    title_card = f"{PROJECT} - SCENE {sec_name}{(' ' + part_label) if part_label else ''}"
    lines = [
        f"Cinematic storyboard contact sheet, one single image containing exactly "
        f"{len(chunk)} numbered panels in a 3x2 grid; the remaining cell(s) form a black "
        f"card with the white title text \"{title_card}\". Each panel has a small white "
        "label in its top-left corner showing the cut number and duration and a one-line "
        "caption below it. Photorealistic live-action, Kodak 35mm film grain, natural "
        "lighting, muted warm naturalistic palette, 16:9 panels.",
        f"Setting and characters: {id_block} Use the reference character sheets for faces "
        "and wardrobe only. No blood, no gore.",
    ]
    for i, c in enumerate(chunk, start=1):
        cap = short_caption(c["desc"])
        lines.append(f"Panel {i} — CUT {c['global_idx']} - {c['duration']}s — {c['size']}, "
                     f"{c['movement'].split(',')[0]}. {cap}. Caption: \"{cap}\".")
    return "\n".join(lines)


def write_storyboards():
    lines_doc = ["# EP3 스토리보드 콘택트시트 프롬프트 (규칙집 §4 규격)", "",
                 "무료 단계 — 텍스트만 생성함(API 호출 없음). scripts/build_ep3_assets.py의 "
                 "SECTIONS에서 그대로 가져와 컷 프롬프트와 항상 같은 내용을 유지한다.",
                 "",
                 "**1컷짜리 자막카드 섹션(궁금증 캡션/타이틀/사흘 전/다음날 아침/엔딩 카드/"
                 "다음 편 예고)은 스토리보드를 만들지 않았다** — 인물도 카메라 변화도 없는 "
                 "정지 배경 위 자막 카드라 콘택트시트로 검수할 내용이 없다.", ""]
    n_sheets = 0
    global_idx = 0
    for sec in ep3.SECTIONS:
        cuts = sec["cuts"]
        # global_idx를 각 컷에 매겨 둔다 (EP3-컷프롬프트.md의 CUT 번호와 대응시키기 위해)
        annotated = []
        for c in cuts:
            global_idx += 1
            annotated.append(dict(c, global_idx=global_idx))
        if len(cuts) <= 1:
            continue  # 자막카드 전용 섹션은 생략
        chunks = [annotated[i:i + MAX_PANELS] for i in range(0, len(annotated), MAX_PANELS)]
        lines_doc.append(f"## {sec['name']}")
        lines_doc.append("")
        for k, chunk in enumerate(chunks):
            part_label = chr(ord("A") + k) if len(chunks) > 1 else ""
            all_speakers = {s for c in chunk for s in c["speakers"]}
            prompt = storyboard_prompt(sec["name"], chunk, part_label, all_speakers)
            # "4막 도입 — ..."과 "4막 — 고물상 대치"가 둘 다 "4막"으로 뭉개지지 않도록
            # em dash 앞부분(막 번호+수식어)을 전부 슬러그에 반영한다.
            slug = "".join(ch for ch in sec["name"].split("—")[0] if ch.isalnum())
            slug = slug or f"sec{n_sheets}"
            fname = f"{slug}{part_label}.txt" if part_label else f"{slug}.txt"
            path = os.path.join(ROOT, "assets", "storyboards", fname)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(prompt + "\n")
            n_sheets += 1
            lines_doc.append(f"### {sec['name']}{(' ' + part_label) if part_label else ''} "
                             f"(`{fname}`, 컷 {chunk[0]['global_idx']}~{chunk[-1]['global_idx']})")
            lines_doc.append("")
            lines_doc.append("```")
            lines_doc.append(prompt)
            lines_doc.append("```")
            lines_doc.append("")
    with open(os.path.join(ROOT, "docs", "EP3-스토리보드.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines_doc) + "\n")
    print(f"스토리보드 콘택트시트 {n_sheets}장 저장: assets/storyboards/*.txt, "
          "docs/EP3-스토리보드.md")


if __name__ == "__main__":
    write_char_files()
    write_location_files()
    write_storyboards()
