#!/usr/bin/env python3
"""PHASE 6 타임라인 재잠금: 디졸브 겹침(압축) + 내레이션 배속을 자막·오디오 설정에 반영한다.

- 전환: scripts/storyboard/<skit>.json 의 transition_out 문구에서 겹침 초를 읽는다
  ("Dissolve 0.5s"→0.5, "... Dissolve 0.4s"→0.4, "Hard cut"/"Match cut"/"J-Cut"/"Fade out"→0).
- 압축: 장면 k 시작 = Σ_{j<k}(길이_j - 겹침_j). 자막 줄은 '속한 장면 + 장면 내 오프셋'으로 옮긴다.
- 내레이션 배속: --narration-tempo N 이면 Naration 스타일 줄의 끝 시각을 길이/N 로 줄이고,
  assets/audio-overrides/<skit>/lineNNN.mp3 를 atempo 적용본으로 갱신한다(원본은 _orig/).
- 결과: subs/<skit>.ass, scripts/audio/<skit>.json(transitions, bgm_segments 시간), --apply 없으면 보고만.
"""
import argparse, json, os, re, shutil, subprocess, sys

ASS_T = re.compile(r"^(\d+):(\d\d):(\d\d\.\d\d)$")
def pt(s):
    m = ASS_T.match(s); return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
def ft(x):
    x = max(0.0, x); h = int(x//3600); m = int((x%3600)//60); return f"{h}:{m:02d}:{x-h*3600-m*60:05.2f}"
def tc(x):
    m = int(x//60); s = x-m*60; f = int(round((s-int(s))*24)); return f"{m:02d}:{int(s):02d}.{f:02d}"

def overlap_of(text):
    m = re.search(r"[Dd]issolve\s*([0-9.]+)\s*s", text or "")
    return float(m.group(1)) if m else 0.0

ap = argparse.ArgumentParser()
ap.add_argument("--skit", required=True)
ap.add_argument("--narration-tempo", type=float, default=1.0)
ap.add_argument("--trim", default="", help="조립 길이 조정: 20=7,33=4 (생성 클립보다 짧게만, 영상 재생성 없음)")
ap.add_argument("--anchor", default="", help="줄 앵커링: TTS줄=장면 (예 18=20,19=21) → 그 줄을 해당 장면 시작+0.3s 이후로 맞춤")
ap.add_argument("--gap", type=float, default=0.3, help="줄 사이 최소 호흡(초), 규격 0.3~0.5")
ap.add_argument("--tail", type=float, default=0.0, help="내레이션이 끝난 뒤 컷까지 최소 여운(초). 부족하면 줄을 다음 장면 시작+0.3으로 미룬다(앵커·대사 줄을 밀게 되면 미루지 않음)")
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()

sb = json.load(open(f"scripts/storyboard/{a.skit}.json", encoding="utf-8"))
scenes = json.load(open(f"scripts/scenes/{a.skit}.json", encoding="utf-8"))
audio = json.load(open(f"scripts/audio/{a.skit}.json", encoding="utf-8"))
durs = [float(d) for d in scenes["durations"]]
gen_durs = list(durs)
for kv in [x for x in a.trim.split(",") if x]:
    k, v = kv.split("="); k = int(k) - 1
    assert float(v) <= gen_durs[k], f"S{k+1}: 생성 길이({gen_durs[k]}s)보다 길게 잡을 수 없음"
    durs[k] = float(v)
ov = [overlap_of(s.get("transition_out")) for s in sb["scenes"]]
ov = [o if o >= 1 / 24 else round(1 / 24, 4) for o in ov]  # 하드컷도 1프레임 겹침(xfade 체인 유지, 조립과 동일)
ov[-1] = 0.0
assert len(ov) == len(durs)
old_c = [0.0]
for d in gen_durs: old_c.append(old_c[-1] + d)
new_s = [0.0]
for d, o in zip(durs, ov): new_s.append(new_s[-1] + d - o)
new_total = new_s[-1]

def remap(t):
    k = min(max(i for i in range(len(durs)) if old_c[i] <= t + 1e-6), len(durs)-1)
    off = min(t - old_c[k], durs[k] - 0.05)  # 잘린 장면은 끝에 걸린 줄을 앞당긴다
    return new_s[k] + off

ass_path = f"subs/{a.skit}.ass"
raw = open(ass_path, encoding="utf-8").read().split("\n")
narr_styles = set(audio.get("narration_styles", ["Naration"]))
silent = set(audio.get("silent_styles", []))
ov_dir = f"assets/audio-overrides/{a.skit}"
rows, tts_i = [], 0
for i, ln in enumerate(raw):
    if not ln.startswith("Dialogue:"): continue
    p = ln.split(",", 9); s0, e0, style = pt(p[1]), pt(p[2]), p[3]
    if style not in silent: tts_i += 1
    s1 = remap(s0); dur = e0 - s0
    if style in narr_styles and a.narration_tempo != 1.0:
        src = os.path.join(ov_dir, f"line{tts_i:03d}.mp3")
        dur = dur / a.narration_tempo
        if a.apply and os.path.exists(src):
            orig_dir = os.path.join(ov_dir, "_orig"); os.makedirs(orig_dir, exist_ok=True)
            orig = os.path.join(orig_dir, os.path.basename(src))
            if not os.path.exists(orig): shutil.copy(src, orig)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", orig, "-filter:a", f"atempo={a.narration_tempo}", src], check=True)
    e1 = s1 + dur
    rows.append((i, p, s1, e1, style))

# 앵커링: 내레이션이 장면보다 앞서는 구간은 줄을 해당 장면 시작 뒤로 민다(앞당기지는 않음)
anchors = {}
for kv in [x for x in a.anchor.split(",") if x]:
    k, v = kv.split("=")
    if "@" in v:  # N=M@off : 장면 M 시작+off 에 정확히(앞당김 포함)
        m, off = v.split("@"); anchors[int(k)] = (int(m), float(off), True)
    else:
        anchors[int(k)] = (int(v), 0.3, False)
rows2, n = [], 0
for i, p, s1, e1, style in rows:
    if style not in silent:
        n += 1
        if n in anchors:
            m, off, exact = anchors[n]
            target = new_s[m - 1] + off
            if s1 < target or exact:
                e1 += target - s1; s1 = target
    rows2.append((i, p, s1, e1, style))
rows = rows2

# 겹치지 않게 보정(압축으로 앞뒤 줄이 붙는 경우 --gap 초 호흡 유지)
GAP = a.gap
def sequence(rs):
    prev_e, out = -1.0, []
    for i, p, s1, e1, style in rs:
        g = GAP if style in narr_styles else 0.3  # 대사 줄 간격은 0.3 고정(립싱크 캐시와 위치 일치 유지)
        if style not in silent and s1 < prev_e + g:
            shift = prev_e + g - s1; s1 += shift; e1 += shift
        if style not in silent: prev_e = e1
        out.append((i, p, s1, e1, style))
    return out
fixed = sequence(rows)

# 여운 보정: 내레이션이 다음 컷 직전에 끝나면(여운 < --tail) 그 줄을 다음 장면 시작+0.3 으로 미룬다.
# 단, 그로 인해 앵커 줄이나 대사(비내레이션) 줄이 밀리면 내용 동기가 깨지므로 미루지 않는다.
if a.tail > 0:
    tts_index = {}
    n = 0
    for i, p, s1, e1, style in fixed:
        if style not in silent: n += 1; tts_index[i] = n
    def scene_of(t):
        return min(max(k for k in range(len(durs)) if new_s[k] <= t + 1e-6), len(durs) - 1)
    changed = True
    while changed:
        changed = False
        for idx, (i, p, s1, e1, style) in enumerate(fixed):
            if style not in narr_styles: continue
            ke = scene_of(e1)
            if ke >= len(durs) - 1: continue
            tail = new_s[ke + 1] - e1
            if tail >= a.tail or tail < 0: continue
            target = new_s[ke + 1] + 0.3
            trial = list(fixed); trial[idx] = (i, p, target, target + (e1 - s1), style)
            trial = sequence(trial)
            ok = True
            for (i2, p2, s2, e2, st2), (i3, p3, s3, e3, st3) in zip(fixed[idx + 1:], trial[idx + 1:]):
                if abs(s3 - s2) > 1e-6 and (st2 not in narr_styles or tts_index.get(i2) in anchors):
                    ok = False; break
            if ok and trial[-1][3] <= new_total:
                print(f"  [여운] {tc(s1)} '{p[9][:14]}' 끝~컷 {tail:.1f}s → S{ke + 2:02d} 시작+0.3 으로 미룸")
                fixed = trial; changed = True; break

print(f"[{a.skit}] 총 {sum(durs):.0f}s → {new_total:.1f}s (디졸브 {sum(1 for o in ov if o)}곳, 겹침 {sum(ov):.1f}s), 내레이션 x{a.narration_tempo}")
if a.apply:
    for i, p, s1, e1, style in fixed:
        p[1], p[2] = ft(s1), ft(e1); raw[i] = ",".join(p)
    open(ass_path, "w", encoding="utf-8").write("\n".join(raw))
    # bgm_segments 는 '직전에 적용된 타임라인' 기준 시각이므로 먼저 생성 타임라인으로 되돌린 뒤 새 타임라인으로 옮긴다(재실행 시 이중 압축 방지)
    pt_tr, pt_d = audio.get("transitions"), audio.get("scene_durations")
    if pt_tr and pt_d and len(pt_tr) == len(pt_d) == len(durs):
        ps = [0.0]
        for d, o in zip(pt_d, pt_tr): ps.append(ps[-1] + float(d) - float(o))
        def unmap(t):
            k = min(max(i for i in range(len(durs)) if ps[i] <= t + 1e-6), len(durs) - 1)
            return old_c[k] + (t - ps[k])
    else:
        unmap = lambda t: t
    for seg in audio.get("bgm_segments", []):
        seg["start"], seg["end"] = round(remap(unmap(float(seg["start"]))), 1), round(min(remap(unmap(float(seg["end"]))), new_total), 1)
    audio["transitions"] = ov
    audio["scene_durations"] = [int(d) if float(d).is_integer() else d for d in durs]
    json.dump(audio, open(f"scripts/audio/{a.skit}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("적용 완료:", ass_path, f"scripts/audio/{a.skit}.json", ov_dir)
else:
    print("(dry-run — --apply 로 반영)")
print("| # | 새 타임코드 | 길이 | 화자 |")
for n, (i, p, s1, e1, style) in enumerate(fixed, 1):
    print(f"| {n} | {tc(s1)}~{tc(e1)} | {e1-s1:.2f}s | {style} |")
