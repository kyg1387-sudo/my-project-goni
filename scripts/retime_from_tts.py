#!/usr/bin/env python3
"""PHASE 1-3 오디오 앵커링: 선행 생성한 보이스의 실측 길이로 자막 타임라인을 재확정한다.

규격서 PHASE 1: 음성 트랙을 먼저 배치하고 샷당 타임코드를 강제 확정한다. 이 도구는
  1) subs/<skit>.ass 의 대사 줄(Caption 제외)에 실측 TTS 길이를 적용하고,
  2) 같은 블록(원래 0.6초 간격으로 이어진 줄들) 안의 호흡을 --pause(기본 0.5초, 규격 0.3~0.5)로
     맞추되, 의도된 긴 앞침묵(씬 전환·감정 전환)은 그대로 둔다,
  3) 어느 줄이 자기 섹션(씬 묶음) 끝을 넘기면 먼저 그 블록의 호흡을 --min-pause까지 줄이고,
     그래도 넘치면 그 섹션의 5초 장면 하나를 10초로 늘려(fal Seedance는 5/10초만 가능)
     뒤쪽 타임라인을 함께 밀어 해소한다.
  4) 결과를 .ass / scripts/scenes/<skit>.json(durations) / scripts/audio/<skit>.json(bgm_segments 시간)
     에 반영한다(--apply 없으면 보고만).

사용법:
  python3 scripts/retime_from_tts.py --skit kim-cart-grandma \
      --durations assets/auditions/kim-cart-grandma-tts/durations.json [--pick line012=B,line038=B] [--apply]
"""
import argparse
import json
import re
import sys

ASS_TIME = re.compile(r"^(\d+):(\d\d):(\d\d\.\d\d)$")


def parse_t(s):
    m = ASS_TIME.match(s)
    if not m:
        sys.exit(f"시간 형식 오류: {s}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def fmt_t(x):
    x = max(0.0, x)
    h = int(x // 3600); m = int((x % 3600) // 60); s = x - h * 3600 - m * 60
    return f"{h}:{m:02d}:{s:05.2f}"


def tc(x):
    m = int(x // 60); s = x - m * 60; f = int(round((s - int(s)) * 24))
    return f"{m:02d}:{int(s):02d}.{f:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skit", required=True)
    ap.add_argument("--durations", required=True, help="실측 길이 json {lineNNN[_A|_B]: 초}")
    ap.add_argument("--pick", default="", help="후보 선택: line012=B,line038=B (미지정 줄은 A/B 중 긴 쪽)")
    ap.add_argument("--pause", type=float, default=0.5)
    ap.add_argument("--min-pause", type=float, default=0.3)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    ass_path = f"subs/{a.skit}.ass"
    scenes_path = f"scripts/scenes/{a.skit}.json"
    audio_path = f"scripts/audio/{a.skit}.json"
    meas = json.load(open(a.durations, encoding="utf-8"))
    pick = dict(kv.split("=") for kv in a.pick.split(",") if kv)
    scenes = json.load(open(scenes_path, encoding="utf-8"))
    audio = json.load(open(audio_path, encoding="utf-8"))
    silent = set(audio.get("silent_styles", []))
    durations = [int(d) for d in scenes["durations"]]
    section_ends = [int(x) for x in audio.get("section_ends", [])]

    raw = open(ass_path, encoding="utf-8").read().split("\n")
    rows = []  # (line_idx_in_file, start, end, style, text)
    for i, ln in enumerate(raw):
        if ln.startswith("Dialogue:"):
            p = ln.split(",", 9)
            rows.append([i, parse_t(p[1]), parse_t(p[2]), p[3], p[9], p])
    tts_i = 0
    for r in rows:
        if r[3] in silent:
            r.append(r[2] - r[1])  # 자막카드는 원래 길이 유지
            continue
        tts_i += 1
        lid = f"line{tts_i:03d}"
        if lid in meas:
            d = meas[lid]
        else:
            cands = {k[-1]: v for k, v in meas.items() if k.startswith(lid + "_")}
            if not cands:
                sys.exit(f"{lid} 실측 길이 없음")
            d = cands[pick[lid]] if lid in pick else max(cands.values())
        r.append(float(d))

    def cum_bounds(durs):
        c = [0]
        for d in durs:
            c.append(c[-1] + d)
        return c

    def sections(durs):
        c = cum_bounds(durs)
        starts = sorted({c[i] for i in section_ends} | {0})
        return starts, c[-1]

    orig_durs = list(durations)
    orig_c = cum_bounds(orig_durs)

    def scene_of(t, durs):
        c = cum_bounds(durs)
        for k in range(len(durs)):
            if c[k] <= t < c[k + 1]:
                return k
        return len(durs) - 1

    # 블록 판정: 직전 줄과의 원래 간격이 0.6초(생성기 기본)면 같은 블록
    in_block = [False]
    for k in range(1, len(rows)):
        in_block.append(abs(rows[k][1] - rows[k - 1][2] - 0.6) < 0.02)

    def layout(durs, pauses):
        """장면 길이(durs)와 블록별 호흡으로 타임라인을 계산. 원래 앵커는 장면 경계 이동량만큼 밀린다."""
        new_c = cum_bounds(durs)
        out = []
        prev_e = None
        for k, r in enumerate(rows):
            orig_s = r[1]
            sc = scene_of(orig_s, orig_durs)
            shifted = orig_s + (new_c[sc] - orig_c[sc])
            if prev_e is not None and in_block[k]:
                s = prev_e + pauses[k]
            else:
                s = shifted if prev_e is None else max(shifted, prev_e + a.min_pause)
            e = s + r[-1]
            out.append((s, e))
            prev_e = e
        return out

    pauses = [a.pause] * len(rows)
    durs = list(durations)
    log = []
    for _round in range(20):
        starts, total = sections(durs)
        tl = layout(durs, pauses)
        bad = None
        for k, (s, e) in enumerate(tl):
            # 줄이 시작한 섹션의 끝
            sec_start = max(x for x in starts if x <= s)
            later = [x for x in starts if x > sec_start]
            sec_end = later[0] if later else total
            if e > sec_end + 0.01:
                bad = (k, s, e, sec_start, sec_end)
                break
        if not bad:
            break
        k, s, e, sec_start, sec_end = bad
        # 1) 같은 블록의 호흡을 최소치로
        blk = [k]
        j = k
        while j > 0 and in_block[j]:
            j -= 1; blk.append(j)
        j = k + 1
        while j < len(rows) and in_block[j]:
            blk.append(j); j += 1
        if any(pauses[i] > a.min_pause for i in blk):
            for i in blk:
                pauses[i] = a.min_pause
            log.append(f"#{k + 1} 섹션 끝({tc(sec_end)}) 초과 {e - sec_end:.2f}s → 블록 호흡 {a.min_pause}s로 축소")
            continue
        # 2) 그 섹션의 5초 장면 하나를 10초로 (뒤에서부터)
        c = cum_bounds(durs)
        idxs = [i for i in range(len(durs)) if sec_start <= c[i] < sec_end]
        cand = [i for i in reversed(idxs) if durs[i] == 5]
        if not cand:
            sys.exit(f"#{k + 1}: 섹션 {tc(sec_start)}~{tc(sec_end)}에 늘릴 5초 장면이 없습니다 — 대본/장면 구성을 조정해야 합니다.")
        durs[cand[0]] = 10
        log.append(f"#{k + 1} 여전히 초과 → 장면 S{cand[0] + 1:02d} 5→10초로 연장")
    else:
        sys.exit("20회 안에 수렴하지 않음")

    tl = layout(durs, pauses)
    starts, total = sections(durs)
    print(f"[{a.skit}] 장면 {len(durs)}개, 총 {sum(orig_durs)}→{total}초, 섹션 경계 {len(starts)}개")
    for l in log:
        print("  -", l)
    print("  - 섹션 경계 침범: 0건")
    changed = [(i + 1, orig_durs[i], durs[i]) for i in range(len(durs)) if orig_durs[i] != durs[i]]
    if changed:
        print("  - 장면 길이 변경:", ", ".join(f"S{i:02d} {o}→{n}" for i, o, n in changed))

    # BGM 구간 시간 이동(장면 경계 이동량 기준)
    new_c = cum_bounds(durs)

    def shift_time(t):
        sc = scene_of(t, orig_durs)
        return t + (new_c[sc] - orig_c[sc])

    if a.apply:
        for r, (s, e) in zip(rows, tl):
            p = r[5]
            p[1], p[2] = fmt_t(s), fmt_t(e)
            raw[r[0]] = ",".join(p)
        open(ass_path, "w", encoding="utf-8").write("\n".join(raw))
        scenes["durations"] = durs
        json.dump(scenes, open(scenes_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        for seg in audio.get("bgm_segments", []):
            seg["start"], seg["end"] = round(shift_time(seg["start"]), 1), round(shift_time(seg["end"]), 1)
        json.dump(audio, open(audio_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("적용 완료:", ass_path, scenes_path, audio_path)
    else:
        print("(dry-run — --apply 로 반영)")
    print()
    print("| # | 타임코드 | 길이 | 화자 | 대사 |")
    print("|---|---|---|---|---|")
    for n, (r, (s, e)) in enumerate(zip(rows, tl), 1):
        print(f"| {n} | {tc(s)}~{tc(e)} | {e - s:.2f}s | {r[3]} | {r[4]} |")


if __name__ == "__main__":
    main()
