#!/usr/bin/env python3
"""Lock 타임라인대로 전 대사를 배치한 청취용 오디오(라디오 드라마 가편집, 무료).
무언 비트는 무음 대신 아주 작은 룸톤(-50dB 핑크 노이즈)으로 채워 길이감을 들려준다.
출력: voice/전체청취_Lock타임라인.mp3
"""
import json, os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from build_tts import SPLIT
from build_lock import SPLIT_GAP, speech_span

SR = 44100
PICK = {}  # 대안 채택: {"line010": "line010v2"}
if os.path.exists(os.path.join(HERE, "tts_pick.json")):
    PICK = json.load(open(os.path.join(HERE, "tts_pick.json")))


def load(path, a, b):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
                          "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def main():
    lock = json.load(open(os.path.join(HERE, "lock.json"), encoding="utf-8"))
    adir = os.path.join(REPO, "assets", "auditions", "tower-tts")
    total = int((lock["total"] + 1) * SR)
    rng = np.random.default_rng(0)
    out = (np.cumsum(rng.standard_normal(total)) * 0).astype(np.float32)
    out += (rng.standard_normal(total).astype(np.float32) * 10 ** (-50 / 20))
    for x in lock["lines"]:
        lid = PICK.get(x["id"], x["id"])
        n = int(x["id"][4:])
        if n in SPLIT:
            parts = []
            for s, *_ in SPLIT[n]:
                p = os.path.join(adir, f"{lid}{s}.mp3")
                a, b = speech_span(p)
                parts += [load(p, a, b), np.zeros(int(SPLIT_GAP * SR), np.float32)]
            y = np.concatenate(parts[:-1])
        else:
            p = os.path.join(adir, f"{lid}.mp3")
            a, b = speech_span(p)
            y = load(p, a, b)
        i = int(x["start"] * SR)
        out[i:i + len(y)] += y[: max(0, total - i)]
    out = np.clip(out, -1, 1)
    dst = os.path.join(HERE, "voice", "전체청취_Lock타임라인.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-i", "-",
                    "-c:a", "libmp3lame", "-b:a", "96k", dst], input=out.tobytes(), check=True)
    print("저장:", dst, f"{lock['total']:.1f}초")


if __name__ == "__main__":
    main()
