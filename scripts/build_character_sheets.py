#!/usr/bin/env python3
"""캐릭터 시트 생성 (docs/영화제작규칙집.md §2 규격, 인물당 1장 3패널).

왼쪽: 전신 앞모습+뒷모습(목에서 잘림, 얼굴 없음) / 오른쪽: 얼굴 클로즈업 1장.
같은 얼굴을 시트 한 장에 여러 번 넣으면 도플갱어가 생기므로(규칙집 실증) 얼굴은
오른쪽 한 곳에만. 이 시트를 이후 reference-to-video 생성의 image_urls로 써서
인물 일관성을 고정한다(참교육사이다 118장면 본 제작에서 같은 인물이 다른 사람처럼
나오는 사고가 다수 발견돼, 사용자 지시로 이 단계를 사후 도입).

fal.ai가 이 세션 sandbox에서 막혀 있어 GitHub Actions에서만 실행 가능
(다른 fal 시험 스크립트와 같은 패턴).

사용법 (워크플로 내부):
    python3 scripts/build_character_sheets.py [--only 한도희,서회장]
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_video import http_json, download  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "characters")

IMAGE_MODEL = "fal-ai/flux/dev"

TEMPLATE = (
    'Character reference sheet, one single 16:9 image on a pure white background, '
    'photorealistic, soft studio lighting, minimal style, fashion-lookbook layout. '
    'Top-left header in clean black sans-serif text: large bold title "{name_en}", '
    'then four small lines below it: "Height: {height} cm" / "{personality}" / '
    '"Voice: {voice}" / "Photorealistic, soft studio lighting, minimal style, '
    'contemporary Korean drama". Left half: full-body front view and full-body back '
    'view of the same {age_desc} standing side by side, feet visible, both figures '
    'cropped at the neck so the head is cut off by the top edge of the frame — no face '
    'shown on the left side. Wardrobe: {wardrobe}. {identifiers}. Right half: one large '
    'close-up portrait from the shoulders up, straight to camera, {expression}, {hair}, '
    '{face_identifiers}, no headwear. No text other than the header.'
)

# 참교육사이다 — build_참교육사이다_assets.py의 인물 상수와 같은 설정을 시트용으로 재구성
CHARACTERS = {
    "한도희": dict(
        name_en="HAN DOHEE", height=165,
        personality="Calm and composed, quietly resolute beneath a gentle surface",
        voice="Soft Jeolla dialect, firm and decisive under pressure",
        age_desc="Korean woman in her late twenties",
        wardrobe="beige caregiver uniform vest over a white blouse, blank plain white "
                 "name tag with no text on the chest",
        identifiers="Round face shape, slim athletic build from former coast guard training",
        expression="steady composed expression, eyes sharp and grounded",
        hair="short neat black hair tied back neatly",
        face_identifiers="round face, straight nose, firm jawline",
    ),
    "서회장": dict(
        name_en="CHAIRMAN SEO", height=172,
        personality="Sharp-eyed and dignified despite illness, quietly perceptive",
        voice="Slow, low, weighty Jeolla dialect",
        age_desc="Korean man in his seventies",
        wardrobe="dark navy silk patient pajamas",
        identifiers="Thin frail build, deep wrinkles, short neatly trimmed white hair",
        expression="calm knowing expression, bright clear eyes",
        hair="short trimmed white hair",
        face_identifiers="gaunt cheeks, deep forehead wrinkles, thin white eyebrows",
    ),
    "엄마": dict(
        name_en="DOHEE'S MOTHER", height=158,
        personality="Worn down by hardship, blunt but deeply protective underneath",
        voice="Rough coarse Jeolla dialect, loud when emotional",
        # 실제 본편 22개 장면(생성 완료분)에서 이미 확립된 외형을 시트에 맞춰
        # 역으로 기록 — 영상이 기준, 시트가 그걸 따라간다(사용자 확정).
        age_desc="Korean woman in her late fifties, weathered face",
        wardrobe="a faded floral-pattern cardigan over a plain blouse",
        identifiers="Short stout build, tired rounded face",
        expression="weary but warm expression",
        hair="short gray-streaked curly permed hair",
        face_identifiers="round tired face, deep smile lines, gray-streaked "
                          "curly hair",
    ),
    "서미령": dict(
        name_en="SEO MIRYEONG", height=168,
        personality="Cold, calculating, condescending",
        voice="Crisp sharp standard Korean, clipped tone",
        age_desc="Korean woman in her thirties",
        wardrobe="a tailored dark navy suit jacket over a white blouse",
        identifiers="Slim tall build, sleek shoulder-length straight black hair",
        expression="cold contemptuous expression",
        hair="sleek shoulder-length straight black hair, center part",
        face_identifiers="angular sharp face shape, thin arched eyebrows",
    ),
    "서준혁": dict(
        name_en="SEO JUNHYUK", height=180,
        personality="Arrogant, short-tempered, entitled",
        voice="Low threatening standard Korean",
        age_desc="Korean man in his thirties",
        wardrobe="a slim-fit gray business suit with no tie",
        identifiers="Tall athletic build, sharply combed black hair",
        expression="arrogant sneering expression",
        hair="short sharply combed black hair, side part",
        face_identifiers="square jawline, sharp angular face",
    ),
    "사내": dict(
        name_en="HENCHMAN", height=178,
        personality="Rough, intimidating, low-level enforcer",
        voice="Rough gravelly Jeolla dialect",
        age_desc="burly South Korean man in his forties, clearly Korean East Asian "
                  "ethnicity",
        wardrobe="a dark worn work jumpsuit jacket, plain with no text or logos",
        identifiers="Stocky muscular build, short buzzed hair",
        expression="rough intimidating expression",
        hair="short buzzed black hair",
        face_identifiers="broad rough-featured Korean face, thick eyebrows",
    ),
    "목포해경": dict(
        name_en="COAST GUARD CAPTAIN", height=175,
        personality="Heavy with guilt and duty, weathered composure",
        voice="Deep grave Jeolla dialect",
        age_desc="Korean man in his fifties",
        wardrobe="a navy coast guard dress uniform with no insignia text",
        identifiers="Sturdy build, short graying hair",
        expression="heavy solemn expression",
        hair="short graying hair",
        face_identifiers="square weathered face, deep-set eyes",
    ),
    # 아웃트로 진행자 — 사용자 제공 실사진은 fal reference-to-video 콘텐츠 정책
    # (실존 인물 초상 처리 불가)에 막혀, 사용자 확정대로 비슷한 분위기의 AI
    # 가상 인물로 대체(CLAUDE.md 성장 전략 체크리스트 ⑦용).
    "아웃트로진행자": dict(
        name_en="OUTRO HOST", height=163,
        personality="Warm, friendly, sincere and approachable",
        voice="Warm gentle standard Korean, welcoming tone",
        age_desc="Korean woman in her late twenties",
        wardrobe="a cream cable-knit sweater",
        identifiers="Slim build, shoulder-length straight black hair with a side part",
        expression="warm friendly smile, eyes crinkled warmly",
        hair="shoulder-length straight black hair, side part",
        face_identifiers="oval face, warm smiling eyes, soft gentle features",
    ),
}


def find_image_url(obj):
    if isinstance(obj, str):
        import re
        return obj if obj.startswith("http") and re.search(r"\.(png|jpg|jpeg|webp)(\?|$)", obj) else None
    if isinstance(obj, dict):
        for k in ("images", "image"):
            if k in obj:
                found = find_image_url(obj[k])
                if found:
                    return found
        for v in obj.values():
            found = find_image_url(v)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = find_image_url(v)
            if found:
                return found
    return None


def fal_image(key, prompt, label):
    headers = {"Authorization": f"Key {key}"}
    status, task = http_json(f"https://queue.fal.run/{IMAGE_MODEL}", {
        "prompt": prompt,
        "image_size": "landscape_16_9",
        "num_images": 1,
    }, headers)
    if status != 200:
        print(f"  [{label}] 작업 생성 실패 (HTTP {status}): {task}")
        return None
    status_url, result_url = task["status_url"], task["response_url"]
    while True:
        time.sleep(5)
        _, info = http_json(status_url, headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            _, result = http_json(result_url, headers=headers)
            url = find_image_url(result)
            if not url:
                print(f"  [{label}] 응답에서 이미지 URL을 못 찾음: {result}")
                return None
            return url
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [{label}] 생성 실패: {info}")
            return None
        print(f"  [{label}] 대기 중... ({state})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="쉼표 구분 인물 이름 (비우면 전체)")
    args = ap.parse_args()

    key = (os.environ.get("FAL_API_KEY") or "").strip()
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다.")

    only = {s.strip() for s in args.only.split(",") if s.strip()}
    os.makedirs(OUT_DIR, exist_ok=True)

    for name, fields in CHARACTERS.items():
        if only and name not in only:
            continue
        path = os.path.join(OUT_DIR, f"{fields['name_en'].lower().replace(chr(32), '-')}.jpg")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            print(f"[{name}] 기존 파일 재사용 → {path}")
            continue
        prompt = TEMPLATE.format(**fields)
        print(f"[{name}] 생성 중...")
        url = fal_image(key, prompt, name)
        if not url:
            sys.exit(f"[{name}] 캐릭터 시트 생성 실패")
        download(url, path)
        print(f"[{name}] 완료 → {path}")


if __name__ == "__main__":
    main()
