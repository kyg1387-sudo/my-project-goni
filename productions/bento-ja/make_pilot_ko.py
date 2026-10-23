#!/usr/bin/env python3
"""bento 대사 3컷 시범 영상 — 립싱크 3컷 이어 붙이기 + 일본어 자막(아래) + [화자] 한국어 검수 자막(위)(제7장 12·제10장 5).

입력 assets/auditions/bento-pilot-omni/omni_<컷>.mp4 · 출력 productions/bento-ja/PHASE4_시범/시범-대사3컷-한국어자막.mp4(1080p) + _480p.mp4
"""
import os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "assets", "auditions", "bento-pilot-omni")
OUT = os.path.join(HERE, "PHASE4_시범")
CUTS = [("S08j", "修三", "じゃあ、出世払いだ。\\N大きくなったら、返しに来い", "그럼, 출세하면 갚아. 크면, 갚으러 와."),
        ("S13d", "拓海", "……半額の弁当、まだ、ありますか", "……반값 도시락, 아직, 있나요."),
        ("S13f", "修三", "……売れ残りなら、な", "……팔다 남은 거라면, 있지.")]
KO_NAME = {"修三": "슈조", "拓海": "타쿠미"}


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def t(x):
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"


def main():
    os.makedirs(OUT, exist_ok=True)
    clips = [os.path.join(SRC, f"omni_{c}.mp4") for c, *_ in CUTS]
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "",
           "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: JA,IPAGothic,70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,6,1,2,120,120,60,1",
           "Style: KO,WenQuanYi Zen Hei,54,&H0000E6FF,&H0000E6FF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,1,2,120,120,0,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    t0 = 0.0
    for (c, spk, ja, ko), p in zip(CUTS, clips):
        d = dur(p)
        lines = ja.count("\\N") + 1
        ass.append(f"Dialogue: 0,{t(t0 + 0.1)},{t(t0 + d - 0.1)},JA,,0,0,0,,{ja}")
        ass.append(f"Dialogue: 0,{t(t0 + 0.1)},{t(t0 + d - 0.1)},KO,,0,0,{150 + 86 * (lines - 1)},,[{KO_NAME[spk]}] {ko}")  # 제15장 14
        t0 += d
    ap = os.path.join(OUT, "pilot.ass")
    open(ap, "w", encoding="utf-8").write("\n".join(ass) + "\n")
    inputs = sum([["-i", p] for p in clips], [])
    n = len(clips)
    fc = "".join(f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v{i}];[{i}:a]aresample=48000[a{i}];" for i in range(n))
    fc += "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];[v]ass={ap}[vo]"
    out = os.path.join(OUT, "시범-대사3컷-한국어자막.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc, "-map", "[vo]", "-map", "[a]", "-c:v", "libx264",
                    "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", out], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", out, "-vf", "scale=-2:480", "-c:v", "libx264", "-crf", "24", "-c:a", "aac",
                    "-b:a", "128k", out.replace(".mp4", "_480p.mp4")], check=True)
    print(out, f"{t0:.2f}초")


if __name__ == "__main__":
    main()
