#!/usr/bin/env python3
"""최종본 자동 검수(제19장 정리 — 『引きこもりの息子』 최종 검수에서 사람이 놓친 결함을 도구로, 지속 개선 원칙 4).
사용법: python3 scripts/qa_final.py <작품> <완성본.mp4> [--omni-dir 립싱크 원본 폴더] [--covered 147,…(재생성 클립으로 메운 번호)]

검사(하나라도 FAIL이면 종료 코드 1):
  1 길이        본편+아웃트로 ≥ 9:40(제0장 1)
  2 라우드니스   통합 −15~−13.5 LUFS, 피크 ≤ −1.0 dBFS(제12장 3)
  3 무음        −60 dB 2초 이상 0건(제6장 4·제15장 13)
  4 후크 암전    0~20초 검은 화면 2초 초과 0건(제15장 20·제19장 23)
  5 정점 소리    bgm_silence 구간 평균 −36 dB 이상(제19장 26 — 계약서 찢기 −40 dB 실증으로 보정, 키 소리·숨만 남는 긴장 구간 −33 dB는 정상)
  6 립싱크 누락  omnihuman_scenes 번호마다 omniNN.mp4 존재(제19장 19, --omni-dir 지정 시)
  7 자막 글꼴    로컬 fc-match가 Noto Sans CJK Bold(제19장 22 — 로컬 패치 자막이 대체 글꼴로 구워지는 것 방지)
"""
import json, os, re, shutil, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FF = shutil.which("ffmpeg")


def stderr(args):
    return subprocess.run([FF, "-v", "info", "-nostats"] + args + ["-f", "null", "-"], capture_output=True, text=True).stderr


def mean_db(path, a, b):
    m = re.search(r"mean_volume: (-?[\d.]+)", stderr(["-ss", f"{a}", "-to", f"{b}", "-i", path, "-vn", "-af", "volumedetect"]))
    return float(m.group(1)) if m else -99.0


def main():
    a = sys.argv
    skit, final = a[1], a[2]
    omni_dir = a[a.index("--omni-dir") + 1] if "--omni-dir" in a else None
    cfg = json.load(open(os.path.join(ROOT, "scripts", "audio", f"{skit}.json"), encoding="utf-8"))
    res = []

    def check(name, ok, info):
        res.append(ok); print(f"[{'PASS' if ok else 'FAIL'}] {name}: {info}")

    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final]))
    check("길이", d - 5.5 >= 580, f"{d:.1f}초(엔드카드 5.5초 제외 {d - 5.5:.1f}초)")
    e = stderr(["-i", final, "-vn", "-af", "ebur128=peak=true"])
    i_ = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1]); pk = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    check("라우드니스", -15.0 <= i_ <= -13.5 and pk <= -1.0, f"{i_} LUFS / 피크 {pk} dBFS")
    sil = re.findall(r"silence_start: ([\d.]+)", stderr(["-i", final, "-vn", "-af", "silencedetect=n=-60dB:d=2"]))
    check("무음(−60dB 2초)", not sil, f"{len(sil)}건 {sil[:5]}")
    bl = [(float(s), float(du)) for s, du in re.findall(r"black_start:([\d.]+) black_end:[\d.]+ black_duration:([\d.]+)",
                                                         stderr(["-t", "20", "-i", final, "-an", "-vf", "blackdetect=d=0.3:pix_th=0.06"]))]
    check("후크 0~20초 암전", all(du <= 2.0 for _, du in bl), f"{bl}")
    lows = []
    for w in cfg.get("bgm_silence") or []:
        m = mean_db(final, w["start"], w["end"])
        if m < -36:
            lows.append((w["start"], round(m, 1)))
    check("정점 구간 소리(bgm_silence ≥ −36 dB)", not lows, f"약한 구간 {lows}" if lows else f"{len(cfg.get('bgm_silence') or [])}구간 정상(최저 {min(mean_db(final, w['start'], w['end']) for w in cfg['bgm_silence']):.1f} dB)" if cfg.get('bgm_silence') else '구간 없음')
    if omni_dir:
        cov = {int(x) for x in a[a.index("--covered") + 1].split(",")} if "--covered" in a else set()
        miss = [n for n in cfg.get("omnihuman_scenes", []) if n not in cov and not os.path.exists(os.path.join(omni_dir, f"omni{n:02d}.mp4"))]
        check("립싱크 누락", not miss, f"없는 번호 {miss} — 교체 클립(CLIP_OVERRIDE)으로 메웠는지 확인" if miss else "전부 있음")
    fm = subprocess.run(["fc-match", "Noto Sans CJK JP:bold"], capture_output=True, text=True).stdout.strip()
    check("로컬 자막 글꼴", "NotoSansCJK" in fm and "Bold" in fm, fm or "fc-match 없음")
    print(f"\n결과: {'전부 PASS' if all(res) else f'FAIL {res.count(False)}건'}")
    sys.exit(0 if all(res) else 1)


if __name__ == "__main__":
    main()
