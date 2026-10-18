#!/usr/bin/env python3
"""프롬프트 5단 공식(고니감독님 확정 2026-10-12, 제12장 1): 모든 키프레임·i2v 프롬프트는 아래 순서로 조립한다.
  [CAMERA] 앵글·사이즈·렌즈·구도  →  [CHARACTER] 인물(IDENTITY FIRST·시트 참조)  →  [ACTION] 행동·표정(소동작)
  →  [SETTING] 배경·조명(로케이션 시트)  →  [NEGATIVE] 금지(외계어·텍스트 등)
오디오·대사는 영상 프롬프트에 넣지 않는다(음성은 Typecast→OmniHuman, 효과음은 별도 생성·믹스 — 제11장 19·22).
PHASE 3·4 생성기가 compose_*()로 조립하고 check_*()로 금지어를 검사한다."""
import re

SECTIONS = ("CAMERA", "CHARACTER", "ACTION", "SETTING", "NEGATIVE")

# 제2장 3·제7장 4: 큰 동작·급격한 표정 변화 금지(영상 모델이 얼굴·소품을 무너뜨린다)
BIG_MOTION = ("slam", "slams", "slamming", "sprint", "sprints", "spin", "spins", "spinning", "whirl",
              "jump", "jumps", "jumping", "punch", "punches", "throw", "throws", "throwing", "hurl", "kick", "kicks",
              "dramatic body movement", "rapid facial expression", "turns 90", "turns around fully")
# 「run」은 사람이 주어일 때만(「foam running over」「the aisle runs along」 같은 사물 표현은 #02 실증 오탐)
BIG_MOTION_RE = (r"\b(?:he|she|they|someone|\w+ (?:man|woman|staff|employee|figure|colleague)s?) (?:runs?|sprints?|starts running|is running)\b",
                 r"\brunning (?:toward|towards|away|across|down|up|into|out)\b")
# 영상 프롬프트에 오디오·대사를 넣는 Veo 계열 문법은 불채택(배역 음성 고정·대본 동결·효과음 믹스 규칙과 충돌)
AUDIO_WORDS = ("sfx:", "sound:", "says in", "says:", "voice:", "dialogue:", "speaks", "narration:", "ambient hum", "music:")
# i2v가 무시하는 카메라 무빙(제8장 6: 편집에서 구현). 설계 문서에는 써도 되지만 생성 프롬프트에는 넣지 않는다
EDIT_ONLY_MOVES = ("tracking camera", "tracking shot", "dolly", "crane", "jib", "whip pan", "handheld", "zoom in", "zoom out", "push-in", "pull back")


def _join(label, text):
    text = (text or "").strip()
    return f"[{label}] {text}" if text else ""


def compose_keyframe(camera, character, action, setting, negative, style=""):
    """5단 순서로 키프레임(정지 이미지) 프롬프트를 조립한다. style은 공통 프리셋(맨 앞, 선택)."""
    parts = [style.strip()] if style else []
    parts += [_join("CAMERA", camera), _join("CHARACTER", character), _join("ACTION", action),
              _join("SETTING", setting), _join("NEGATIVE", negative)]
    return " ".join(p for p in parts if p)


def compose_motion(action, locks="", character="", camera="Static, locked-off camera."):
    """i2v 동작 프롬프트: 카메라(고정) → 인물 유지 → 소동작 → 금지 동작·잠금. 오디오 지시 없음."""
    parts = [_join("CAMERA", camera), _join("CHARACTER", character), _join("ACTION", action), _join("LOCK", locks)]
    return " ".join(p for p in parts if p)


def split_sections(prompt):
    """라벨이 있는 프롬프트를 {"_pre": 스타일, "CAMERA": …, …}로 나눈다(생성기 간 재조립용). 라벨이 없으면 {"_pre": 전체}."""
    out = {"_pre": prompt.strip()}
    hits = sorted((m.start(), m.group(1)) for m in re.finditer(r"\[(CAMERA|CHARACTER|ACTION|SETTING|NEGATIVE|LOCK)\]", prompt))
    if not hits:
        return out
    out["_pre"] = prompt[:hits[0][0]].strip()
    for k, (pos, lab) in enumerate(hits):
        end = hits[k + 1][0] if k + 1 < len(hits) else len(prompt)
        out[lab] = (out.get(lab, "") + " " + prompt[pos + len(lab) + 2:end].strip()).strip()
    return out


def check_order(prompt):
    """[CAMERA]…[NEGATIVE] 라벨이 있으면 순서를 검사한다. 위반 목록을 돌려준다(빈 리스트 = 합격)."""
    pos = [(prompt.find(f"[{s}]"), s) for s in SECTIONS]
    seen = [(p, s) for p, s in pos if p >= 0]
    order = [s for _, s in sorted(seen)]
    expected = [s for s in SECTIONS if s in order]
    return [] if order == expected else [f"순서 위반: {' → '.join(order)} (기대: {' → '.join(expected)})"]


def check_motion(prompt, sid=""):
    """i2v·키프레임 동작 문장의 금지어 검사. 위반 목록(빈 리스트 = 합격)."""
    low = prompt.lower()
    bad = []
    for w in BIG_MOTION:
        if re.search(r"\b" + re.escape(w) + r"\b", low) and not re.search(r"\bno\b[^.]{0,40}\b" + re.escape(w) + r"\b", low):
            bad.append(f"{sid} 큰 동작 「{w}」")
    for rx in BIG_MOTION_RE:
        m = re.search(rx, low)
        if m and not re.search(r"\bno\b[^.]{0,40}" + re.escape(m.group(0)), low):
            bad.append(f"{sid} 큰 동작 「{m.group(0)}」")
    for w in AUDIO_WORDS:
        if w in low:
            bad.append(f"{sid} 오디오 지시 「{w}」(영상 프롬프트 금지)")
    for w in EDIT_ONLY_MOVES:
        if w in low and "edit" not in low:
            bad.append(f"{sid} 편집 전용 무빙 「{w}」(i2v 무시 — 편집에서 구현)")
    return bad


if __name__ == "__main__":   # 자가 검사
    p = compose_keyframe("Medium close-up, eye level, 50mm.", "IDENTITY FIRST: reference image 1.",
                         "Right hand resting flat on a letter on the desk, jaw set, cold gaze.",
                         "SETTING: dim industrial control room (loc sheet), hard side light from left, 4500K.",
                         "gibberish, foreign text, logo, watermark.", style="Photorealistic cinematic film still.")
    assert check_order(p) == [], check_order(p)
    assert check_motion("He slams the letter and says: 'You will regret this'.", "T") == [
        "T 큰 동작 「slams」", "T 오디오 지시 「says:」(영상 프롬프트 금지)"]
    assert check_motion("No slamming; fingers press the letter slightly.", "T") == []
    assert check_motion("foam running over the rim; the aisle runs along the racks.", "T") == []
    assert check_motion("She runs toward the door.", "T") == ["T 큰 동작 「she runs」"]
    assert check_motion("Tracking camera follows him.", "T") == ["T 편집 전용 무빙 「tracking camera」(i2v 무시 — 편집에서 구현)"]
    d = split_sections(p)
    assert d["_pre"].startswith("Photorealistic") and d["CAMERA"].startswith("Medium") and d["NEGATIVE"].startswith("gibberish"), d
    print("prompt_format OK")
