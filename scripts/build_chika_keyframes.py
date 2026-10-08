#!/usr/bin/env python3
"""『地下倉庫の伝票』 PHASE 4 키프레임 스펙 생성기 (build_tower_keyframes.py 구조, 규격 제7장 1·5·7).

scripts/storyboard/chika.json(PHASE 3)을 읽어 generate_portraits.py 스펙을 만든다. 스펙을 손으로 고치지 않는다.
단계:
  pilot    scripts/portraits/chika-kf-pilot.json  파일럿 3장(S03d 곤도 OMNI CU · S15e 사오리 OMNI CU · S11d 곤도 역광 실루엣)
  a        scripts/portraits/chika-kf-a.json      OMNI 대사 CU 27장 — 참조 = PHASE 2 셀(표정 셀 + 로케이션)
  b        scripts/portraits/chika-kf-b.json      나머지 — 얼굴이 보이는 컷은 A에서 승인한 인물별 기준 얼굴을 1번 참조로 추가
  collect  승인된 pilot/a/b 결과를 assets/portraits/chika-keyframes/<id>-1.png(스토리보드 경로)로 모은다
generate-video.yml portraits_spec=<스펙> → assets/portraits/<스펙>/<id>-1.png
사용법: python3 scripts/build_chika_keyframes.py pilot|a|b[:ID,ID]|collect
"""
import json
import os
import shutil
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SB_PATH = os.path.join(ROOT, "scripts", "storyboard", "chika.json")
OUT = os.path.join(ROOT, "scripts", "portraits", "chika-kf-{}.json")
KF_DIR = "assets/portraits/chika-keyframes"
STAGE_DIRS = ("assets/portraits/chika-kf-pilot", "assets/portraits/chika-kf-pilot-r", "assets/portraits/chika-kf-a", "assets/portraits/chika-kf-a-r",
              "assets/portraits/chika-kf-b", "assets/portraits/chika-kf-b-r")
PILOT = ["S03d", "S15e", "S11d"]
KF_RATE = 0.04

# 인물 식별 특징(PHASE 2 마스터 시트에서 잠근 것) — 참조 셀 설명과 함께 글로 한 번 더 못 박는다(제7장 7)
PEOPLE = {
    "saori": "Saori (34, straight black shoulder-length hair with bangs, upper half tied back in a small knot, thin silver-rimmed oval glasses)",
    "saori-b": "Saori (34, straight black shoulder-length hair with bangs, upper half tied back in a small knot, thin silver-rimmed oval glasses, light-grey knit sweater + navy canvas apron)",
    "saori-e": "Saori (34, black hair with bangs tied back in a low bun, thin silver-rimmed oval glasses)",
    "gondo": "Gondo (52, heavyset, double chin, salt-and-pepper hair slicked straight back, thick gold-rimmed rectangular glasses, glossy navy double-breasted suit, wine-red tie)",
    "miyamoto": "Miyamoto (64, thin, short white hair, full bushy white moustache, half-moon reading glasses hanging on a black cord around the neck, not on the face)",
    "kiritani": "Kiritani (early 50s, lean, hollow cheeks, short neatly parted black hair with grey temples, frameless rimless glasses)",
    "okochi": "Okochi (mid-60s, square jaw, short silver hair, thick dark eyebrows, NO glasses)",
}
# 인물별 기준 얼굴 = A단계 승인 OMNI 컷(제7장 7: 기준 얼굴은 대사 키프레임). 사오리 엔딩(saori-e)은 대사 컷이 없어 셀 유지.
FACE_KF = {"saori": "S03c", "saori-b": "S15e", "gondo": "S03d", "miyamoto": "S06c", "kiritani": "S01b", "okochi": "S16b"}
FACE_KINDS = ("face", "react", "d", "sil")   # sil: 실루엣이라도 체형·머리 윤곽은 기준 얼굴 컷을 따른다

TIGHT = ("FRAMING FIRST: a tight single-person chest-up close-up — head and shoulders fill the frame, the top of the head near the top edge, "
         "the frame cut at mid-chest; the face occupies about one third of the frame height; hands NOT visible; NOT a medium shot, NOT a full-body shot. "
         "Full-frame 16:9 image, no black bars.")
FULL = "Full-frame 16:9 image filling the whole canvas: NO black bars, NO white borders, NO letterbox or pillarbox."
LOC_NOTE = {
    "loc-aud": "The auditorium walls and stage are plain; the projection screen, the stage banner and any lectern plate are completely blank.",
    "loc-off": "Open-plan office: monitors show only a blank blue-grey glow, every paper, binder spine, partition label and whiteboard is completely blank; no posters with writing.",
    "loc-ev": "Elevator hall: the floor indicator is a plain dark panel with no digits; wall plates are blank brushed steel.",
    "loc-arc": "Basement archive: cardboard box labels, binder spines and the door plate are completely blank; no readable writing on any paper.",
    "loc-arcv": "Basement archive: cardboard box labels, binder spines and the door plate are completely blank; no readable writing on any paper.",
    "angle-arc": "Basement archive: cardboard box labels, binder spines and the door plate are completely blank; no readable writing on any paper.",
    "loc-cor": "Basement corridor: pipe tags and the door plates are blank; no stencilled letters on walls or pipes.",
    "loc-bq": "Banquet hall: the stage banner and the projection screen are completely blank; table cards and name tags are blank white.",
    "angle-bq": "Banquet hall: the stage banner and the projection screen are completely blank; table cards and name tags are blank white.",
    "prop-case": "The attaché case has NO logo, NO monogram, NO tag — plain leather and brass only.",
    "prop-tripod": "The tripod and camera have NO brand logo or lettering.",
}


# 파일럿 1차 검수(2026-10-08) 결과 보정 문장 — 프롬프트 맨 앞에 넣어 참조 셀(흰 배경·플랫 조명)보다 우선시킨다
FIX = {
    # S03d: 미디엄(노트북·손 노출)·플랫 밝은 조명·친절한 미소·아이레벨로 생성됨 → 설계(로우앵글 CU·압박 형광등·비웃음)
    "S03d": ("LIGHTING AND FRAMING NEXT. The office is dim at the edges: the only strong light is a hard, cold fluorescent panel directly above "
             "Gondo, pressing straight down — bright forehead and nose bridge, deep dark eye sockets behind the gold-rimmed glasses, a hard shadow under "
             "the chin and nose, the far desks fading into cool shadow; NO bright even daylight, NO flat lighting. Camera is BELOW his eye line "
             "looking UP at him (low angle), tight chest-up close-up: head and shoulders fill the frame, cut at mid-chest; NO laptop, NO desk, NO hands "
             "in the frame. Expression: a thin one-sided SNEER — lips pressed with one corner pulled up, eyes narrowed, chin raised, looking down his nose "
             "at the camera with contempt; NOT a friendly smile, NOT warm."),
    # S11d: 아이레벨로 생성되고 하단에 흰 띠(레터박스) → 바닥 높이 극단 로우앵글, 전체 화면
    "S11d": ("CAMERA FIRST: the camera sits on the concrete floor of the archive (lens about 30 cm above the floor) looking UP: the open steel door and "
             "the backlit figure tower above the lens, the floor runs away from the bottom edge of the frame toward the door, the fluorescent tube and "
             "ceiling converge upward. Extreme low angle, 35mm lens. Full-frame 16:9 image with NO white or black strip at any edge."),
}


# 파일럿 2차: 시트 표정 셀 1(「비웃음」)이 실제로는 옅은 미소라 친절한 얼굴을 끌고 옴 → 정면 중립 셀 + 표정은 글로 지시
# 파일럿 2차 합격 → 곤도 「비웃음」 컷 전부에 적용(gondo-expr1 참조 시 자동 치환 + 표정 문장)
REF_SWAP = {"*": {"gondo-expr1.png": "gondo-front.png"}}
SNEER = ("EXPRESSION FIRST: Gondo is NOT smiling. His face shows cold CONTEMPT — mouth closed with the lips pressed into a thin line and ONE corner "
         "pulled slightly up into a sneer, nostrils a little flared, eyelids half lowered, brows slightly raised as he looks DOWN his nose "
         "while his chin is raised; a cruel, bored, superior look.")


def person_key(path):
    b = os.path.basename(path).rsplit(".", 1)[0]
    for k in ("saori-b", "saori-e", "saori", "gondo", "miyamoto", "kiritani", "okochi"):
        if b == k or b.startswith(k + "-"):
            return k
    return None


def describe(path, i):
    name = os.path.basename(path).rsplit(".", 1)[0]
    if path.startswith(STAGE_DIRS):
        k = person_key(path) or next((k for k, v in FACE_KF.items() if name.startswith(v)), "")
        who = PEOPLE.get(k, "this character")
        return (f"Reference image {i} is the APPROVED keyframe face of {who}: reproduce exactly this face, hair, eyewear and wardrobe; "
                "ignore its background and framing unless the description below says otherwise.")
    k = person_key(path)
    if k:
        who = PEOPLE[k]
        hair = "facial hair" if k in ("miyamoto", "gondo", "kiritani", "okochi") else "clean face with NO facial hair"
        if "expr" in name:
            return (f"Reference image {i} is the expression cell of {who}: copy exactly this face, hair, eyewear, {hair} and wardrobe, and this "
                    "emotional expression (about 60 percent intensity); ignore its plain background and any borders or labels.")
        if "full" in name:
            return (f"Reference image {i} is the full-body wardrobe cell of {who}: copy exactly the body type, wardrobe and shoes; ignore its plain background.")
        return (f"Reference image {i} is the master face cell of {who}: copy exactly this face, hair, eyewear, {hair} and wardrobe; "
                "ignore its plain background and any borders or labels.")
    if name.startswith("angle-"):
        return (f"Reference image {i} is the SAME location seen from this camera angle: match its architecture, colours, set dressing, light direction and depth; "
                "people in it are only a placement guide; ignore any borders or labels.")
    if name.startswith("prop-"):
        return f"Reference image {i} is the prop: reproduce exactly its shape, material and colour."
    return (f"Reference image {i} is the location reference: match its architecture, colours, set dressing and light direction; "
            "ignore any borders or labels.")


def notes(refs):
    out = []
    for r in refs:
        b = os.path.basename(r)
        for k, v in LOC_NOTE.items():
            if b.startswith(k) and v not in out:
                out.append(v)
    return out


def build(sc, face_refs):
    refs = list(face_refs) + [r for r in sc["refs"] if r not in face_refs]
    swap = {**REF_SWAP["*"], **REF_SWAP.get(sc["id"], {})}
    sneer = any(os.path.basename(r) == "gondo-expr1.png" for r in refs)
    refs = [os.path.join(os.path.dirname(r), swap.get(os.path.basename(r), os.path.basename(r))) for r in refs]
    parts = ["Create ONE single photorealistic cinematic film still in 16:9 widescreen — one frame only, NOT a grid, no panels, no borders, no captions."]
    parts += [describe(p, i + 1) for i, p in enumerate(refs)]
    if sneer:
        parts.insert(1, SNEER)
    if sc["id"] in FIX:
        parts.insert(1 + sneer, FIX[sc["id"]])
    parts.append(sc["keyframe_prompt"])
    parts += notes(refs)
    if sc["kind"] == "d":
        parts.append(TIGHT)
        parts.append("Soft fill light keeps the mouth and jaw readable (lip-sync cut). Mouth gently closed or barely parted (speech is added later); "
                     "natural skin texture, both eyes sharp and symmetrical.")
    else:
        parts.append(FULL)
    if sc["kind"] == "sil":
        parts.append("The figure is a true backlit silhouette: no facial features readable, only outline, hair shape and body mass.")
    parts.append("Absolutely no text, letters, numbers, logos or symbols anywhere in the image.")
    return {"id": sc["id"], "count": 1, "aspect_ratio": "16:9", "refs": refs, "prompt": " ".join(parts)}


def face_refs_for(sc):
    out = []
    if sc["kind"] not in FACE_KINDS:
        return out
    for r in sc["refs"]:
        k = person_key(r)
        if k and k in FACE_KF:
            p = f"assets/portraits/chika-kf-a/{FACE_KF[k]}-1.png"
            if sc["id"] == FACE_KF[k]:
                continue
            if not os.path.exists(os.path.join(ROOT, p)):
                raise SystemExit(f"{sc['id']}: 기준 얼굴 {p} 없음 — A단계 먼저")
            if p not in out:
                out.append(p)
    return out


def done(sc):
    """앞 단계(파일럿 등)에서 이미 생성·승인된 컷은 유료 재생성하지 않는다."""
    return any(os.path.exists(os.path.join(ROOT, d, f"{sc['id']}-1.png")) for d in STAGE_DIRS)


def collect(shots):
    os.makedirs(os.path.join(ROOT, KF_DIR), exist_ok=True)
    n, missing = 0, []
    for s in shots:
        dst = os.path.join(ROOT, s["keyframe"])
        src = next((os.path.join(ROOT, d, f"{s['id']}-1.png") for d in STAGE_DIRS[::-1]
                    if os.path.exists(os.path.join(ROOT, d, f"{s['id']}-1.png"))), None)
        if src is None:
            missing.append(s["id"])
            continue
        if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
            shutil.copy2(src, dst)
            n += 1
    print(f"{KF_DIR}: {n}장 복사, 누락 {len(missing)}장" + (f" → {', '.join(missing)}" if missing else ""))


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    stage, _, only = arg.partition(":")
    sb = json.load(open(SB_PATH, encoding="utf-8"))
    shots = [s for s in sb["scenes"] if s.get("keyframe")]
    if stage == "collect":
        return collect(shots)
    if stage == "pilot":
        items = [build(s, []) for s in shots if s["id"] in PILOT]
    elif stage == "a":
        items = [build(s, []) for s in shots if s["kind"] == "d" and (only or not done(s))]
    elif stage == "b":
        items = [build(s, face_refs_for(s)) for s in shots if s["kind"] != "d" and (only or not done(s))]
    else:
        raise SystemExit("단계: pilot|a|b[:ID,ID]|collect")
    if only:
        ids = set(only.split(","))
        items = [x for x in items if x["id"] in ids]
        stage += "-r"
    for x in items:
        for r in x["refs"]:
            if not os.path.exists(os.path.join(ROOT, r)):
                raise SystemExit(f"{x['id']}: 참조 없음 {r}")
    spec = {"_설명": f"chika PHASE 4 키프레임 {stage}(build_chika_keyframes.py 생성, 직접 수정 금지). {len(items)}장 약 {len(items) * KF_RATE:.2f}달러.",
            "_style_preset": sb["preset"], "characters": items}
    path = OUT.format(stage)
    json.dump(spec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{path}: {len(items)}장 약 {len(items) * KF_RATE:.2f}달러")


if __name__ == "__main__":
    main()
