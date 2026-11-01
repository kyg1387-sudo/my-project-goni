#!/usr/bin/env python3
"""생성된 클립 일부를 잘라 길이를 줄이고, 뒤따르는 모든 자막·대사 타이밍을 자동으로 당긴다.

AI 생성 클립은 종종 실제 필요한 길이보다 길게 나온다 — 대사·동작이 끝난 뒤에도
모델이 주어진 시간을 채우려 하기 때문이다(EP1 실증: 침묵 구간에도 말하는 몸짓을
만듦). 화면에 보여줄 필요가 없는 뒷부분을 잘라내면 같은 생성 비용으로 편집
속도감을 높일 수 있다(전문가 검토 반영: "전체를 쓰지 말고 필요한 만큼만").

이 스크립트는 실제로 생성된 클립을 보면서(=화요일 이후) 판단할 값만 받는다 —
대본 단계에서는 어느 컷의 어디까지가 "필요한 부분"인지 알 수 없으므로 미리
채워둘 수 없다.

동작:
    1. out/sceneNN.mp4를 지정한 새 길이로 자른다(-c copy, 앞부분 유지·뒷부분 삭제,
       빠르고 화질 손실 없음). 원본은 out/sceneNN.orig.mp4로 백업(멱등 — 이미
       있으면 안 덮어씀, 여러 번 실행해도 안전).
    2. scripts/scenes/<스킷>.json의 durations 배열을 갱신한다.
    3. subs/<스킷>.ass에서, 잘라낸 장면 뒤에 오는 모든 Dialogue 타임코드를
       줄어든 시간만큼 당긴다.
    4. **안전장치**: 잘라내려는 구간(새 길이~원래 길이 사이)에 걸리는 대사·
       내레이션·캡션이 하나라도 있으면 그 소리가 잘려나가므로 즉시 중단한다 —
       "필요한 부분만 남긴다"는 원칙 자체가 깨지기 때문에 경고가 아니라 차단.

--apply 없이 실행하면 무엇이 바뀔지만 보여주고 파일은 하나도 건드리지 않는다
(dry-run 기본값 — 실수로 되돌릴 수 없는 편집을 하지 않도록).

사용법:
    python3 scripts/trim_and_retime.py --skit kim-cart-grandma --scenes-dir out \
        --trims "12:6,27:4"
    (문제없으면) python3 scripts/trim_and_retime.py --skit kim-cart-grandma \
        --scenes-dir out --trims "12:6,27:4" --apply

--trims: "장면번호:새길이초" 쌍을 콤마로 나열. 장면번호는 1부터, scripts/scenes/
<스킷>.json의 순서 기준(=out/sceneNN.mp4의 NN과 동일).
"""

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def parse_trims(spec):
    trims = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        idx_s, dur_s = part.split(":")
        idx, dur = int(idx_s), float(dur_s)
        if idx < 1:
            sys.exit(f"장면 번호는 1부터입니다: {part}")
        if dur <= 0:
            sys.exit(f"새 길이는 0보다 커야 합니다: {part}")
        trims[idx] = dur
    return trims


def parse_time(s):
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def fmt_time(t):
    t = max(t, 0.0)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def scene_bounds(durations):
    """durations 배열로 각 장면의 (시작, 끝) 절대 시각 목록을 만든다(0-index)."""
    bounds, t = [], 0.0
    for d in durations:
        bounds.append((t, t + d))
        t += d
    return bounds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skit", required=True)
    ap.add_argument("--scenes-dir", default="out")
    ap.add_argument("--trims", required=True, help='"장면번호:새길이초" 콤마 나열')
    ap.add_argument("--apply", action="store_true", help="실제로 파일을 바꾼다(기본은 dry-run)")
    args = ap.parse_args()

    trims = parse_trims(args.trims)

    scenes_path = os.path.join(ROOT, "scripts", "scenes", f"{args.skit}.json")
    ass_path = os.path.join(ROOT, "subs", f"{args.skit}.ass")
    with open(scenes_path, encoding="utf-8") as f:
        scenes_data = json.load(f)
    durations = list(scenes_data.get("durations") or
                      [scenes_data.get("duration", 5)] * len(scenes_data["scenes"]))
    n = len(scenes_data["scenes"])

    for idx in trims:
        if idx > n:
            sys.exit(f"장면 {idx}는 전체 장면 수({n})를 넘습니다.")
        if trims[idx] >= durations[idx - 1]:
            sys.exit(f"장면 {idx}: 새 길이({trims[idx]}s)가 원래 길이({durations[idx-1]}s) "
                      "이상입니다 — 줄이는 것만 지원합니다.")

    old_bounds = scene_bounds(durations)

    with open(ass_path, encoding="utf-8") as f:
        ass_lines = f.readlines()
    events = []  # (원본 줄 인덱스, start, end, 나머지 필드 문자열)
    for i, raw in enumerate(ass_lines):
        if not raw.startswith("Dialogue:"):
            continue
        rest = raw[len("Dialogue:"):].rstrip("\n")
        fields = rest.split(",", 9)
        start, end = parse_time(fields[1]), parse_time(fields[2])
        events.append((i, start, end, fields))

    # 안전장치: 잘라내는 구간(새 길이~원래 길이)에 걸리는 대사/내레이션/캡션이
    # 있으면 그 소리가 통째로 잘려나가므로 즉시 중단한다.
    blocked = []
    for idx, new_dur in trims.items():
        old_start, old_end = old_bounds[idx - 1]
        cut_from, cut_to = old_start + new_dur, old_end
        for _, ev_start, ev_end, fields in events:
            if ev_start < cut_to and ev_end > cut_from:
                blocked.append((idx, fields[3], fields[9] if len(fields) > 9 else "", ev_start))
    if blocked:
        print("중단: 잘라내려는 구간에 대사/내레이션/캡션이 걸립니다 — 화면과 소리가 "
              "어긋나므로 자를 수 없습니다.")
        for idx, style, text, ev_start in blocked:
            print(f"  장면 {idx}: {style} '{text[:30]}' (시작 {ev_start:.2f}s)")
        print("해당 장면은 --trims에서 빼거나, 대사가 안 걸리는 길이로 조정하세요.")
        sys.exit(1)

    # 각 트림의 감소량과, 그 트림 이후 시각에 적용될 누적 감소량을 계산.
    reductions = {idx: durations[idx - 1] - new_dur for idx, new_dur in trims.items()}
    trim_points = sorted((old_bounds[idx - 1][1], reductions[idx]) for idx in trims)  # (원래 끝시각, 감소량)

    def shift_for(t):
        return sum(red for cut_end, red in trim_points if t >= cut_end)

    print(f"=== {args.skit}: 트림 계획 ({'적용' if args.apply else 'dry-run'}) ===")
    total_reduction = sum(reductions.values())
    for idx, new_dur in sorted(trims.items()):
        print(f"  장면 {idx}: {durations[idx-1]:.1f}s → {new_dur:.1f}s "
              f"(-{reductions[idx]:.1f}s)")
    print(f"  전체 길이: {old_bounds[-1][1]:.1f}s → {old_bounds[-1][1]-total_reduction:.1f}s")

    if not args.apply:
        print("\ndry-run입니다 — 실제로 적용하려면 --apply를 추가하세요.")
        return

    # 1) 클립 트리밍 (원본 백업 후 -c copy로 자름)
    scenes_dir = os.path.join(ROOT, args.scenes_dir) if not os.path.isabs(args.scenes_dir) else args.scenes_dir
    for idx, new_dur in trims.items():
        src = os.path.join(scenes_dir, f"scene{idx:02d}.mp4")
        backup = os.path.join(scenes_dir, f"scene{idx:02d}.orig.mp4")
        if not os.path.exists(src):
            sys.exit(f"클립을 찾을 수 없습니다: {src}")
        if not os.path.exists(backup):
            os.replace(src, backup)
        else:
            print(f"  [scene {idx:02d}] 이미 트림된 상태로 보입니다(백업 존재) — 백업에서 다시 자름")
        subprocess.run(["ffmpeg", "-y", "-i", backup, "-t", f"{new_dur:.3f}",
                        "-c", "copy", src], check=True, capture_output=True)
        actual = probe_duration(src)
        print(f"  [scene {idx:02d}] 트림 완료 → {actual:.2f}s (요청 {new_dur:.2f}s — "
              "키프레임 위치에 따라 약간 다를 수 있음)")

    # 2) scenes.json의 durations 갱신
    for idx, new_dur in trims.items():
        durations[idx - 1] = new_dur
    scenes_data["durations"] = durations
    scenes_data.pop("duration", None)
    with open(scenes_path, "w", encoding="utf-8") as f:
        json.dump(scenes_data, f, ensure_ascii=False, indent=2)
    print(f"갱신: {scenes_path}")

    # 3) .ass 타임코드 당기기
    new_lines = list(ass_lines)
    for i, ev_start, ev_end, fields in events:
        shift = shift_for(ev_start)
        if shift <= 0:
            continue
        fields[1] = fmt_time(ev_start - shift)
        fields[2] = fmt_time(ev_end - shift)
        # fields[0]은 "Dialogue:" 뒤를 그대로 슬라이스한 거라 앞 공백을 이미 갖고
        # 있다 — 여기서 또 공백을 붙이면 "Dialogue:  0,..." 처럼 이중 공백이 된다.
        new_lines[i] = "Dialogue:" + ",".join(fields) + "\n"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"갱신: {ass_path} (총 {total_reduction:.1f}s 당김)")

    print("\n완료. scene_speakers/ambience_prompts/section_ends는 장면 '개수'가 "
          "그대로라 안 바뀝니다 — audio json은 다시 만들 필요 없음. TTS는 "
          "generate_audio.py가 갱신된 .ass 타이밍 기준으로 다시 배치합니다.")


if __name__ == "__main__":
    main()
