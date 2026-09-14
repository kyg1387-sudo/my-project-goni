#!/usr/bin/env python3
"""생성된 오디오 캐시(TTS lineNNN.mp3, 현장음 ambNN.wav)에서 외국어 섞임을 검사한다.

faster-whisper로 각 파일을 전사해 감지 언어와 들리는 내용을 보고한다.
- line*.mp3: 한국어(ko)가 아니거나, 전사 결과에 영어/한자 단어가 섞이면 플래그
- amb*.wav : 현장음에서 말소리(어떤 언어든)가 들리면 플래그
비용이 드는 재생성 전에 무료로 문제 파일을 특정하는 용도다.

사용법: python3 scripts/qa_language.py --audio-dir out/audio [--ass subs/<스킷>.ass]
결과: 표준 출력 + <audio-dir>/qa_language_report.txt
"""

import argparse
import glob
import os
import re


def parse_ass_lines(path):
    lines = []
    if not path or not os.path.exists(path):
        return lines
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw.startswith("Dialogue:"):
                continue
            fields = raw[len("Dialogue:"):].strip().split(",", 9)
            if len(fields) < 10:
                continue
            text = re.sub(r"\{[^}]*\}", "", fields[9]).replace("\\N", " ").strip()
            if text and fields[3] != "Caption":
                lines.append((fields[3], fields[4], text))
    return lines


def similarity(a, b):
    """공백 제거 후 2-gram 겹침 비율(0~1). 전사·대본 대조용 간이 척도."""
    a = re.sub(r"[\s.,?!…'\"『』—-]", "", a)
    b = re.sub(r"[\s.,?!…'\"『』—-]", "", b)
    if len(a) < 2 or len(b) < 2:
        return 1.0 if a == b else 0.0
    ga = {a[i:i + 2] for i in range(len(a) - 1)}
    gb = {b[i:i + 2] for i in range(len(b) - 1)}
    return len(ga & gb) / max(len(ga | gb), 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio-dir", default="out/audio")
    ap.add_argument("--ass", default="")
    ap.add_argument("--model", default="small")
    args = ap.parse_args()

    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    ass_lines = parse_ass_lines(args.ass)
    report, flagged = [], []

    def log(msg):
        print(msg, flush=True)
        report.append(msg)

    log("=== TTS 대사 파일 검사 (line*.mp3) ===")
    for p in sorted(glob.glob(os.path.join(args.audio_dir, "line*.mp3"))):
        name = os.path.basename(p)
        idx = int(name[4:7]) if name[4:7].isdigit() else 0
        segs, info = model.transcribe(p, beam_size=1, vad_filter=False)
        heard = " ".join(s.text.strip() for s in segs).strip()
        script = ass_lines[idx - 1][2] if 0 < idx <= len(ass_lines) else ""
        sim = similarity(heard, script) if script else -1
        latin = re.findall(r"[A-Za-z]{2,}", heard)
        hanzi = re.findall(r"[一-鿿]+", heard)
        problems = []
        if info.language != "ko":
            problems.append(f"감지언어={info.language}(p={info.language_probability:.2f})")
        if latin:
            problems.append(f"영문 감지: {' '.join(latin[:5])}")
        if hanzi:
            problems.append(f"한자/중국어 감지: {''.join(hanzi)[:20]}")
        if script and sim < 0.25:
            problems.append(f"대본과 불일치(유사도 {sim:.2f})")
        mark = "  <<< 문제" if problems else ""
        log(f"[{name}] lang={info.language} | 대본: {script[:24]} | 들림: {heard[:48]}"
            f" | {'; '.join(problems)}{mark}")
        if problems:
            flagged.append((name, problems))

    log("\n=== 현장음 파일 검사 (amb*.wav) — 말소리가 들리면 안 됨 ===")
    for p in sorted(glob.glob(os.path.join(args.audio_dir, "amb*.wav"))):
        name = os.path.basename(p)
        segs, info = model.transcribe(p, beam_size=1, vad_filter=True,
                                      vad_parameters={"min_silence_duration_ms": 300})
        heard = " ".join(s.text.strip() for s in segs).strip()
        # 짧은 잡음 오인식은 무시하고, 단어가 이어지는 경우만 말소리로 본다
        wordy = len(re.sub(r"[\s.,?!…-]", "", heard)) >= 6
        mark = "  <<< 말소리 감지" if wordy else ""
        log(f"[{name}] lang={info.language} | 들림: {heard[:60] or '(무음/비언어)'}{mark}")
        if wordy:
            flagged.append((name, [f"말소리: {heard[:40]}"]))

    log("\n=== 요약 ===")
    if flagged:
        log(f"문제 파일 {len(flagged)}개:")
        for name, problems in flagged:
            log(f"  {name}: {'; '.join(problems)}")
    else:
        log("문제 파일 없음")

    out = os.path.join(args.audio_dir, "qa_language_report.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"\n보고서 저장: {out}")


if __name__ == "__main__":
    main()
