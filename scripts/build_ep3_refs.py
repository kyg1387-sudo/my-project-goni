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

사용법: python3 scripts/build_ep3_refs.py
"""

import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

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


if __name__ == "__main__":
    write_char_files()
    write_location_files()
