#!/usr/bin/env python3
"""bento PHASE 6 효과음·룸톤 믹스(로컬·무과금) — sfx_timeline.json(제19장 10)의 화면 밖 소리를 타임코드에 얹고,
전편에 룸톤 베드(약 −52 dBFS, 제15장 13)를 깐 뒤 −14 LUFS·−1 dBTP로 마스터링한다(제13장 3).
대사 구간(lock.json 줄)에 걸리는 효과음은 −6 dB(제15장 22). 영상 트랙은 그대로 복사.
사용법: python3 productions/bento-ja/mix_sfx.py <입력.mp4> <출력.mp4>
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SFX = os.path.join(REPO, "assets", "auditions", "bento-sfx")


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def vol(p, key):
    r = subprocess.run(["ffmpeg", "-i", p, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(r.split(key + ":")[1].split()[0])


def main(src, out):
    tl = json.load(open(os.path.join(HERE, "sfx_timeline.json"), encoding="utf-8"))["events"]
    lines = [(x["start"], x["end"]) for x in json.load(open(os.path.join(HERE, "lock.json")))["lines"] if x.get("start") is not None]
    total = dur(src)
    ins, fl = ["-i", src, "-stream_loop", "-1", "-i", os.path.join(SFX, "roomtone.mp3")], []
    room_gain = -52 - vol(os.path.join(SFX, "roomtone.mp3"), "mean_volume")  # 소스 평균을 −52 dBFS로
    fl.append(f"[1:a]atrim=0:{total:.3f},highpass=f=60,lowpass=f=3000,volume={room_gain:.1f}dB[room]")
    mix = ["[0:a]", "[room]"]
    for k, e in enumerate(tl):
        p = os.path.join(SFX, e["name"] + ".mp3")
        n = ins.count("-i")  # 입력 번호(-stream_loop 인자 때문에 길이/2는 틀림)
        ins += ["-i", p]
        d = dur(p)
        talk = any(a < e["at"] + d and b > e["at"] for a, b in lines)
        db = e["dbfs"] - vol(p, "max_volume") - (6 if talk else 0)  # 소스 피크를 지정 dBFS로(소스마다 음량이 제각각 — 실측)
        ms = int(e["at"] * 1000)
        fl.append(f"[{n}:a]afade=t=in:d=0.05,afade=t=out:st={max(0.0, d - 0.6):.2f}:d=0.6,volume={db:.1f}dB,adelay={ms}|{ms}[s{k}]")
        mix.append(f"[s{k}]")
    fl.append("".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0,"
              "loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000[a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", out], check=True)
    r = subprocess.run(["ffmpeg", "-i", out, "-af", "silencedetect=n=-60dB:d=2", "-f", "null", "-"], capture_output=True, text=True).stderr
    print(out, f"{total:.1f}s", "무음 2초+ 구간:", r.count("silence_start"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
