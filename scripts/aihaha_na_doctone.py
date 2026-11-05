#!/usr/bin/env python3
"""『母が遺したビデオレター』 내레이션 다큐 톤 보정(고니감독님 승인 2026-11-05 「보정본으로 진행」, 최우선 원칙 7·19_통합지침-적용표).
NA 46줄에 같은 체인을 적용: 피치 −1반음(포먼트 보존·길이 불변 → Lock 그대로) · 80Hz 저역 컷 · 250Hz +1.5dB(낮은 몸통) · 6kHz 고역 −2dB ·
완만한 압축(2.5:1) — 반사음 없음(클로즈마이크). 줄마다 처리 전 평균 음량에 맞춰 되돌려 대사와의 음량 균형은 바꾸지 않는다.
원본: assets/auditions/aihaha-tts-b/_v1/ 보관(이미 있으면 덮어쓰지 않음). 처리 후 assets/audio-overrides/aihaha/의 해당 번호에 복사.
사용법: python3 scripts/aihaha_na_doctone.py"""
import json, os, re, shutil, subprocess

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = os.path.join(ROOT, "assets", "auditions", "aihaha-tts-b"); BAK = os.path.join(SRC, "_v1")
OVR = os.path.join(ROOT, "assets", "audio-overrides", "aihaha")
CHAIN = ("rubberband=pitch=0.9439:formant=preserved,highpass=f=80,equalizer=f=250:t=q:w=1:g=1.5,"
         "highshelf=f=6000:g=-2,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120")


def mean_db(p):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True)
    return float(re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr).group(1))


def main():
    lock = json.load(open(os.path.join(ROOT, "productions", "aihaha-ja", "lock.json")))
    na = {x["tag"]: x["id"] for x in lock["lines"] if x.get("spk") == "NA"}
    amap = json.load(open(os.path.join(ROOT, "scripts", "storyboard", "aihaha.json")))["audio_map"]
    os.makedirs(BAK, exist_ok=True); done = 0
    for tag, lid in sorted(na.items()):
        src = os.path.join(SRC, lid + ".mp3"); bak = os.path.join(BAK, lid + ".mp3")
        if not os.path.exists(bak):
            shutil.copy(src, bak)
        tmp = src + ".tmp.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", bak, "-af", CHAIN, "-ar", "44100", "-ac", "1", tmp], check=True)
        gain = mean_db(bak) - mean_db(tmp)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"volume={gain:.2f}dB,alimiter=limit=0.89",
                        "-c:a", "libmp3lame", "-q:a", "2", src], check=True)
        os.remove(tmp); done += 1
        for cache, t, orig in amap:
            if orig == lid:
                shutil.copy(src, os.path.join(OVR, cache + ".mp3"))
    print(f"내레이션 다큐 톤 보정 {done}줄 완료(원본 {BAK})")


if __name__ == "__main__":
    main()
