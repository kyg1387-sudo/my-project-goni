#!/usr/bin/env python3
"""『みすぼらしい老人は、財閥会長だった』 대사 3컷 시범 한국어 자막 검수판(제10장 4·5, 로컬 무료).
입력: assets/auditions/beggar-pilot-omni/omni-<컷>.mp4  출력: productions/beggar-chairman-ja/pilot-ko-review.mp4
일본어 자막(아래, 70px) + [화자] 한국어 번역(위, 노란색). 글꼴: WenQuanYi Zen Hei(한·일 겸용).
"""
import os, subprocess, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
A = os.path.join(ROOT, "assets", "auditions", "beggar-pilot-omni")
OUT = os.path.join(ROOT, "productions", "beggar-chairman-ja", "pilot-ko-review.mp4")
CUTS = [("omni-S13i", "その子が、わしじゃよ。", "[회장] 그 아이가, 나요."),
        ("omni-S12f", "か、会長……ですって……？", "[지배인] 회, 회장님……이라고요……?"),
        ("omni-S11i", "おじいさんに、触らないでください！", "[치히로] 할아버지한테 손대지 마세요!")]
FONT = "WenQuanYi Zen Hei"


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def main():
    tmp = tempfile.mkdtemp(); parts = []
    for i, (cid, ja, ko) in enumerate(CUTS):
        src = os.path.join(A, cid + ".mp4"); d = dur(src)
        ass = os.path.join(tmp, f"{i}.ass")
        open(ass, "w", encoding="utf-8").write(
            "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: JA,{FONT},70,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,120,120,80,1\n"
            f"Style: KO,{FONT},58,&H0000F0FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,120,120,180,1\n\n"
            "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
            f"Dialogue: 0,0:00:00.10,0:00:{d - 0.05:05.2f},JA,,0,0,0,,{ja}\nDialogue: 0,0:00:00.10,0:00:{d - 0.05:05.2f},KO,,0,0,0,,{ko}\n")
        out = os.path.join(tmp, f"{i}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
                        f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,ass={ass},tpad=stop_mode=clone:stop_duration=0.8",
                        "-af", "apad=pad_dur=0.8", "-c:v", "libx264", "-crf", "20", "-c:a", "aac", "-ar", "44100", "-ac", "2", "-shortest", out], check=True)
        parts.append(out)
    lst = os.path.join(tmp, "l.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-crf", "22",
                    "-vf", "scale=-2:720", "-c:a", "aac", OUT], check=True)
    print(OUT, f"{dur(OUT):.1f}s")


if __name__ == "__main__":
    main()
