#!/usr/bin/env python3
"""『時給5万円の罠』 음성 줄 장소감 선처리(로컬·무료, 제20장 7 ② 발성 디렉션) — burn 전에 assets/audio-overrides/yamibaito/ 줄 파일에 적용.

- 母 전화 줄(L03·L05·L21): 수화기 너머 소리 = highpass 300Hz + lowpass 3.4kHz + 가벼운 압축(제20장 7 ② 「전화 = 로우패스」).
- 폐쇄 실내(S04 승합차·S05 공장 마당·S06 작업실·S07): 근접 마이크 + 짧은 하드 반사 = 짧은 aecho 소량(전역 voice_reverb 0.08 위에 +0.06).
- 야외(S08·S09·S11)와 원룸(S01~S03)은 전역 0.08만(바람 베드는 sfx_timeline wind_*).
길이 보존: 필터 뒤 원래 길이로 atrim(Lock 타임라인 불변, 제11장 4). 원본은 _orig/에 보관하고 두 번 실행해도 원본에서 다시 만든다.
사용법: python3 scripts/yamibaito_voice_fx.py [--dry]
"""
import json, os, shutil, subprocess, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
AO = os.path.join(ROOT, "assets", "audio-overrides", "yamibaito")
ORIG = os.path.join(AO, "_orig")
LOCK = json.load(open(os.path.join(ROOT, "productions", "yamibaito-ja", "lock.json"), encoding="utf-8"))
PHONE = {"母"}  # 전화 너머 화자
INDOOR = {"S04", "S05", "S06", "S07"}  # 폐쇄 실내(하드 반사)
FX_PHONE = "highpass=f=300,lowpass=f=3400,acompressor=threshold=-18dB:ratio=3:attack=5:release=60:makeup=2,volume=0.9"
FX_INDOOR = "aecho=0.9:0.8:18|31:0.06|0.035"


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def main():
    dry = "--dry" in sys.argv
    os.makedirs(ORIG, exist_ok=True)
    n = 0
    for l in LOCK["lines"]:
        fx = None
        if l["spk"] in PHONE:
            fx = FX_PHONE
        elif l["scene"][:3] in INDOOR and l["spk"] != "NA":
            fx = FX_INDOOR
        if not fx:
            continue
        src = os.path.join(AO, f"{l['audio']}.mp3")
        if not os.path.exists(src):
            print("없음:", src); continue
        keep = os.path.join(ORIG, f"{l['audio']}.mp3")
        if not os.path.exists(keep):
            shutil.copy2(src, keep)
        d = dur(keep)
        print(f"{l['tag']:5} {l['scene']:4} {l['spk']:3} {l['audio']} {d:.2f}s  {'전화' if fx is FX_PHONE else '실내'}")
        n += 1
        if dry:
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", keep, "-af", f"{fx},atrim=0:{d:.4f}", "-ar", "44100", "-b:a", "192k", src], check=True)
        d2 = dur(src)
        assert abs(d2 - d) < 0.06, (src, d, d2)
    print(f"처리 {n}줄 (원본 {ORIG})")


if __name__ == "__main__":
    main()
