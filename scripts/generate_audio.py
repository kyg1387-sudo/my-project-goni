#!/usr/bin/env python3
"""자막(.ass) 타이밍에 맞춰 대사 TTS·배경음악을 생성하고, 선택적으로 립싱크까지 해서 영상에 입힌다.

fal.ai의 TTS(MiniMax speech), 음악 생성(Lyria 2), 립싱크(sync-lipsync 등) 모델을 사용한다.
자막 파일의 각 Dialogue 줄에서 시작 시각·화자(Style/Name)·텍스트를 읽어 화자별 목소리로
음성을 만들고, 자막이 뜨는 시점에 맞춰 배치한 뒤 배경음악을 낮은 볼륨으로 깔아 믹싱한다.

--lipsync 모드에서는 장면 클립별로 그 장면에 나오는 대사(내레이션 제외)만 잘라
립싱크 모델로 입 모양을 재합성한 뒤, 장면들을 다시 이어붙이고 자막을 입힌 영상 위에
최종 오디오를 믹싱한다. 입 모양과 최종 오디오가 같은 배치 계획을 쓰므로 싱크가 맞는다.

사용법:
    export FAL_API_KEY=...
    # 기본 (자막 입힌 영상에 오디오만)
    python3 scripts/generate_audio.py \
        --ass subs/<스킷>.ass --config scripts/audio/<스킷>.json \
        --video out/<스킷>-skit-subbed.mp4 --out out/<스킷>-skit-final.mp4
    # 립싱크 포함 (장면 클립에서 재조립; fal-client 필요: pip install fal-client)
    python3 scripts/generate_audio.py \
        --ass subs/<스킷>.ass --config scripts/audio/<스킷>.json \
        --video out/<스킷>-skit-subbed.mp4 --out out/<스킷>-skit-final.mp4 \
        --lipsync --scenes-dir out

ffmpeg/ffprobe가 PATH에 있어야 한다. BGM 생성에 실패하면 경고만 남기고 계속 진행한다.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_video import http_json, download  # noqa: E402

WORK_DIR = None  # main에서 out/audio 로 설정

MAX_TEMPO = 1.35  # 대사가 자막 슬롯보다 길 때 허용하는 최대 배속 (피치 유지)
GAP = 0.05        # 연속 대사 사이 최소 간격(초)


def download_retry(url, path, attempts=3):
    """일시적 네트워크 오류(불완전 수신 등)에 대비해 다운로드를 재시도한다."""
    for attempt in range(1, attempts + 1):
        try:
            download(url, path)
            return True
        except Exception as e:
            print(f"  다운로드 실패 ({attempt}/{attempts}): {e}")
            if attempt < attempts:
                time.sleep(2 * attempt)
    return False


# ---------- fal.ai 큐 공통 ----------

def fal_run(model, payload, key, label, timeout_s=600):
    """fal 큐에 작업을 넣고 완료까지 기다려 결과 dict를 돌려준다. 실패 시 None."""
    headers = {"Authorization": f"Key {key}"}
    status, task = http_json(f"https://queue.fal.run/{model}", payload, headers)
    if status != 200:
        print(f"  [{label}] 작업 생성 실패 (HTTP {status}): {task}")
        return None
    status_url, result_url = task["status_url"], task["response_url"]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        time.sleep(3)
        _, info = http_json(status_url, headers=headers)
        state = info.get("status")
        if state == "COMPLETED":
            _, result = http_json(result_url, headers=headers)
            return result
        if state in ("FAILED", "CANCELLED", "ERROR"):
            print(f"  [{label}] 생성 실패: {info}")
            return None
    print(f"  [{label}] 시간 초과")
    return None


def find_media_url(obj, exts):
    """응답 구조가 모델마다 달라, 해당 확장자의 첫 URL을 재귀로 찾는다."""
    if isinstance(obj, str):
        if obj.startswith("http") and re.search(rf"\.({exts})(\?|$)", obj):
            return obj
        return None
    if isinstance(obj, dict):
        for k in ("video", "audio", "audio_url", "video_url", "audio_file", "url"):
            if k in obj:
                found = find_media_url(obj[k], exts)
                if found:
                    return found
        for v in obj.values():
            found = find_media_url(v, exts)
            if found:
                return found
    if isinstance(obj, list):
        for v in obj:
            found = find_media_url(v, exts)
            if found:
                return found
    return None


def find_audio_url(obj):
    return find_media_url(obj, "mp3|wav|m4a|ogg|flac")


def find_video_url(obj):
    return find_media_url(obj, "mp4|mov|webm")


def fal_upload(path, key):
    """fal 저장소에 파일을 올리고 URL을 돌려준다. (pip install fal-client 필요)"""
    os.environ.setdefault("FAL_KEY", key)
    import fal_client
    return fal_client.upload_file(path)


# ---------- 자막 파싱 ----------

def parse_time(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_ass(path):
    """(start초, end초, style, name, text) 목록을 돌려준다."""
    lines = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw.startswith("Dialogue:"):
                continue
            fields = raw[len("Dialogue:"):].strip().split(",", 9)
            if len(fields) < 10:
                continue
            start, end, style, name = fields[1], fields[2], fields[3], fields[4]
            text = re.sub(r"\{[^}]*\}", "", fields[9]).replace("\\N", " ").strip()
            if text:
                lines.append((parse_time(start), parse_time(end), style, name, text))
    return lines


# ---------- TTS / BGM ----------

def cached(path):
    """이어하기: 이전 실행에서 만들어진 산출물이 있으면 재사용한다."""
    return os.path.exists(path) and os.path.getsize(path) > 1000


def tts_line(cfg, key, index, voice, text, emotion=None):
    path = os.path.join(WORK_DIR, f"line{index:03d}.mp3")
    if cached(path):
        print(f"  [tts {index:03d}] 기존 파일 재사용")
        return path
    speed = float(cfg.get("speed_overrides", {}).get(str(index), cfg.get("speed", 1.05)))
    voice_setting = {"voice_id": voice, "speed": speed}
    if emotion and emotion != "neutral":
        voice_setting["emotion"] = emotion
    payload = {
        "text": text,
        "voice_setting": voice_setting,
        "language_boost": cfg.get("language_boost", "Korean"),
    }
    result = fal_run(cfg["tts_model"], payload, key, f"tts {index:03d}")
    if result is None:
        return None
    url = find_audio_url(result)
    if not url:
        print(f"  [tts {index:03d}] 응답에서 오디오 URL을 못 찾음: {result}")
        return None
    return path if download_retry(url, path) else None


def make_bgm(cfg, key):
    path = os.path.join(WORK_DIR, "bgm.audio")
    if cached(path):
        print("  [bgm] 기존 파일 재사용")
        return path
    model = cfg.get("bgm_model")
    prompt = cfg.get("bgm_prompt")
    if not model or not prompt:
        return None
    result = fal_run(model, {"prompt": prompt}, key, "bgm")
    if result is None:
        return None
    url = find_audio_url(result)
    if not url:
        print(f"  [bgm] 응답에서 오디오 URL을 못 찾음: {result}")
        return None
    path = os.path.join(WORK_DIR, "bgm.audio")
    return path if download_retry(url, path) else None


# ---------- 배치 계획 ----------

def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def plan_placement(clips, total):
    """겹치지 않는 배치 [(실제 시작, 배속, style, 파일)]을 계산한다.

    각 대사는 자막 슬롯(다음 대사 시작까지)보다 길면 MAX_TEMPO까지 배속해
    슬롯에 맞추고, 그래도 길면 다음 대사를 앞 대사가 끝난 뒤로 밀어
    절대 겹치지 않게 한다. 여유가 생기면 다시 자막 타이밍으로 복귀한다.
    """
    placed, prev_end = [], 0.0
    for k, (start, style, path) in enumerate(clips):
        dur = probe_duration(path)
        next_start = clips[k + 1][0] if k + 1 < len(clips) else total
        slot = max(next_start - start - GAP, 0.5)
        tempo = min(max(dur / slot, 1.0), MAX_TEMPO)
        actual = max(start, prev_end + GAP)
        placed.append((actual, tempo, style, path))
        prev_end = actual + dur / tempo
        if tempo > 1.0 or actual > start + 0.01:
            print(f"  배치 조정 [{k + 1:03d}]: 시작 {start:.2f}→{actual:.2f}s, "
                  f"배속 x{tempo:.2f} (길이 {dur:.2f}s, 슬롯 {slot:.2f}s)")
    return placed


# ---------- 오디오 렌더링 / 믹싱 ----------

def render_track(placed, total, out_wav):
    """배치된 클립들을 무음 바탕 위에 얹어 total초 길이 wav로 렌더링한다."""
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-t", f"{total:.3f}",
           "-i", "anullsrc=r=44100:cl=stereo"]
    for _, _, _, path in placed:
        cmd += ["-i", path]
    parts, mix_inputs = [], ["[0:a]"]
    for k, (start, tempo, _style, _path) in enumerate(placed):
        ms = int(round(start * 1000))
        chain = f"[{k + 1}:a]"
        if tempo > 1.0:
            chain += f"atempo={tempo:.4f},"
        parts.append(chain + f"adelay={ms}:all=1[d{k}]")
        mix_inputs.append(f"[d{k}]")
    parts.append("".join(mix_inputs)
                 + f"amix=inputs={len(mix_inputs)}:duration=first:normalize=0[aout]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[aout]", out_wav]
    subprocess.run(cmd, check=True, capture_output=True)
    return out_wav


def mix(video, placed, bgm, bgm_volume, out_path, ambience=None, ambience_volume=0.4):
    """배치된 대사·현장음·BGM을 영상 오디오 트랙으로 믹싱해 out_path에 저장."""
    ambience = ambience or []
    duration = probe_duration(video)
    cmd = ["ffmpeg", "-y", "-i", video]
    for _, _, _, path in placed:
        cmd += ["-i", path]
    for _, path in ambience:
        cmd += ["-i", path]
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", bgm]

    parts, mix_inputs = [], []
    for k, (start, tempo, _style, _path) in enumerate(placed):
        ms = int(round(start * 1000))
        chain = f"[{k + 1}:a]"
        if tempo > 1.0:
            chain += f"atempo={tempo:.4f},"
        parts.append(chain + f"adelay={ms}:all=1[d{k}]")
        mix_inputs.append(f"[d{k}]")
    base = len(placed) + 1
    for k, (start, _path) in enumerate(ambience):
        ms = int(round(start * 1000))
        parts.append(f"[{base + k}:a]volume={ambience_volume},adelay={ms}:all=1[amb{k}]")
        mix_inputs.append(f"[amb{k}]")
    if bgm:
        parts.append(
            f"[{base + len(ambience)}:a]atrim=0:{duration:.3f},"
            f"afade=t=out:st={max(duration - 2, 0):.3f}:d=2,volume={bgm_volume}[bg]")
        mix_inputs.append("[bg]")
    parts.append(
        "".join(mix_inputs)
        + f"amix=inputs={len(mix_inputs)}:duration=longest:normalize=0,"
        + f"atrim=0:{duration:.3f}[aout]")

    script = os.path.join(WORK_DIR, "filter.txt")
    with open(script, "w") as f:
        f.write(";\n".join(parts))
    cmd += ["-filter_complex_script", script,
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out_path]
    subprocess.run(cmd, check=True)


# ---------- 립싱크 ----------

def omnihuman_scene(cfg, key, scene_path, audio_path, index):
    """오디오 구동 생성(OmniHuman류): 장면 첫 프레임 + 대사 오디오로 입 모양이
    정확히 맞는 클립을 새로 생성한다. 실패 시 None(기존 립싱크로 폴백)."""
    path = os.path.join(WORK_DIR, f"omni{index:02d}.mp4")
    if cached(path):
        print(f"  [omnihuman {index:02d}] 기존 파일 재사용")
        return path
    frame = os.path.join(WORK_DIR, f"omniframe{index:02d}.png")
    subprocess.run(["ffmpeg", "-y", "-ss", "0.2", "-i", scene_path,
                    "-frames:v", "1", frame], check=True, capture_output=True)
    img_url = fal_upload(frame, key)
    a_url = fal_upload(audio_path, key)
    models = cfg.get("omnihuman_models",
                     ["fal-ai/bytedance/omnihuman/v1.5", "fal-ai/bytedance/omnihuman"])
    for model in models:
        payload = {"image_url": img_url, "audio_url": a_url}
        result = fal_run(model, payload, key, f"omnihuman {index:02d} ({model})",
                         timeout_s=1800)
        if result:
            url = find_video_url(result)
            if url and download_retry(url, path):
                return path
    return None


def lipsync_scene(cfg, key, v_url, audio_path, index):
    """장면 클립의 입 모양을 대사 오디오에 맞게 재합성한 클립 경로를 돌려준다. 실패 시 None."""
    path = os.path.join(WORK_DIR, f"lip{index:02d}.mp4")
    if cached(path):
        print(f"  [lipsync {index:02d}] 기존 파일 재사용")
        return path
    a_url = fal_upload(audio_path, key)
    for model in cfg.get("lipsync_models", ["fal-ai/sync-lipsync", "fal-ai/latentsync"]):
        payload = {"video_url": v_url, "audio_url": a_url}
        if "sync-lipsync" in model:
            payload["sync_mode"] = "cut_off"
        result = fal_run(model, payload, key, f"lipsync {index:02d} ({model})", timeout_s=1200)
        if result:
            url = find_video_url(result)
            if not url:
                print(f"  [lipsync {index:02d}] 응답에서 영상 URL을 못 찾음: {result}")
                continue
            if download_retry(url, path):
                return path
    return None


AMB_NEGATIVE = ("music, melody, song, speech, talking, dialogue, voice, narration, "
                "crowd murmur, whispering, mumbling, human voice, vocal sounds, "
                "English words, Chinese words, singing, laughing")

_amb_lock = __import__("threading").Lock()


def ambience_group_clip(cfg, key, v_url, prompt):
    """같은 프롬프트(=같은 장소)의 장면들은 현장음 생성 1회를 공유한다.

    말소리 섞임 사고 이후: 장면마다 따로 만들면 비용도 크고 품질 편차도 커서,
    프롬프트 해시로 캐시(ambg-XXXX.media)해 그룹당 한 번만 생성한다.
    """
    import hashlib
    tag = hashlib.md5(prompt.encode()).hexdigest()[:8]
    raw = os.path.join(WORK_DIR, f"ambg-{tag}.media")
    with _amb_lock:  # 같은 그룹 동시 생성 방지
        if cached(raw):
            return raw
        result = fal_run(cfg["ambience_model"], {
            "video_url": v_url,
            "prompt": prompt,
            "negative_prompt": AMB_NEGATIVE,
            "duration": 30,
        }, key, f"ambience group {tag}")
        if result is None:
            return None
        url = find_video_url(result) or find_audio_url(result)
        if not url:
            print(f"  [ambience {tag}] 응답에서 미디어 URL을 못 찾음: {result}")
            return None
        return raw if download_retry(url, raw) else None


def ambience_scene(cfg, key, v_url, index, duration):
    """장면에 깔 현장음 wav 경로를 돌려준다(그룹 클립에서 잘라냄). 실패 시 None."""
    wav = os.path.join(WORK_DIR, f"amb{index:02d}.wav")
    if cached(wav):
        print(f"  [ambience {index:02d}] 기존 파일 재사용")
        return wav
    if not cfg.get("ambience_model"):
        return None
    prompts = cfg.get("ambience_prompts", [])
    prompt = prompts[index - 1] if index - 1 < len(prompts) else "realistic ambient sound"
    if not prompt.strip():
        # 빈 프롬프트 = 현장음 없이 감(생성 모델이 말소리를 계속 섞는 구간용)
        print(f"  [ambience {index:02d}] 현장음 없음(의도적 생략)")
        return None
    raw = ambience_group_clip(cfg, key, v_url, prompt)
    if not raw:
        return None
    # 장면마다 그룹 클립의 다른 구간을 써서 티 나는 반복을 피한다
    total = probe_duration(raw)
    offset = 0.0
    if total > duration + 0.5:
        offset = (index * 3.1) % max(total - duration - 0.2, 0.1)
    subprocess.run(["ffmpeg", "-y", "-i", raw, "-vn",
                    "-af", f"atrim={offset:.3f}:{offset + duration:.3f},asetpts=PTS-STARTPTS",
                    wav], check=True, capture_output=True)
    return wav


def rebuild_with_lipsync(cfg, key, scenes_dir, ass_path, placed_dialogue, work_video):
    """장면별 대사 구간 립싱크·현장음 생성 후 재조립하고 자막을 입힌 영상을 돌려준다.

    (재조립된 영상 경로, [(시작초, 현장음 wav)]) 를 돌려준다.
    """
    scenes = sorted(glob.glob(os.path.join(scenes_dir, "scene*.mp4")))
    if not scenes:
        sys.exit(f"장면 클립을 찾을 수 없습니다: {scenes_dir}/scene*.mp4")
    # 계획 길이가 있으면 그 길이로 장면을 정확히 잘라 쓴다. 생성 클립이 몇 프레임씩
    # 길 때 생기는 누적 오차(자막·음성이 장면보다 앞서는 현상)를 없애기 위함이다.
    planned = cfg.get("scene_durations")
    if planned and len(planned) != len(scenes):
        print(f"경고: scene_durations {len(planned)}개 != 장면 {len(scenes)}개 — 실측 길이 사용")
        planned = None
    durations = [float(d) for d in planned] if planned else [probe_duration(s) for s in scenes]
    bounds, t = [], 0.0
    for d in durations:
        bounds.append((t, t + d))
        t += d
    total = t
    print(f"장면 {len(scenes)}개, 총 {total:.2f}초" + (" (계획 길이로 정규화)" if planned else ""))

    # 대사(내레이션 제외)만 담긴 전체 트랙
    dial_wav = render_track(placed_dialogue, total, os.path.join(WORK_DIR, "dialogue.wav"))

    # 립싱크 왜곡(얼굴 깨짐)이 반복되는 장면은 립싱크를 건너뛰고 원본 얼굴을 유지한다
    skip_lipsync = set(int(n) for n in cfg.get("lipsync_skip_scenes", []))

    def process_scene(item):
        """한 장면의 현장음 생성과 립싱크. (최종 장면 경로, 현장음 항목|None)을 돌려준다."""
        i, scene, t0, t1 = item
        v_url = fal_upload(scene, key)

        amb = ambience_scene(cfg, key, v_url, i, t1 - t0)  # 실패해도 계속
        amb_item = (t0, amb) if amb else None
        if not amb:
            print(f"  [scene {i:02d}] 현장음 없음")

        has_dialogue = any(
            start < t1 and (start + probe_duration(p) / tempo) > t0
            for start, tempo, _s, p in placed_dialogue)
        if not has_dialogue:
            print(f"[scene {i:02d}] 대사 없음 — 립싱크 생략")
            return scene, amb_item
        if i in skip_lipsync:
            print(f"[scene {i:02d}] 립싱크 제외 지정 — 원본 유지")
            return scene, amb_item
        seg = os.path.join(WORK_DIR, f"seg{i:02d}.wav")
        subprocess.run(["ffmpeg", "-y", "-i", dial_wav,
                        "-af", f"atrim={t0:.3f}:{t1:.3f},asetpts=PTS-STARTPTS", seg],
                       check=True, capture_output=True)
        if i in set(int(n) for n in cfg.get("omnihuman_scenes", [])):
            print(f"[scene {i:02d}] 오디오 구동 생성(omnihuman) 중... ({t0:.1f}~{t1:.1f}s)")
            omni = omnihuman_scene(cfg, key, scene, seg, i)
            if omni:
                return omni, amb_item
            print(f"  [scene {i:02d}] omnihuman 실패 — 기존 립싱크로 폴백")
        print(f"[scene {i:02d}] 립싱크 중... ({t0:.1f}~{t1:.1f}s)")
        lip = lipsync_scene(cfg, key, v_url, seg, i)
        if not lip:
            print(f"  [scene {i:02d}] 립싱크 실패 — 원본 유지")
        return (lip or scene), amb_item

    jobs = [(i, scene, t0, t1)
            for i, (scene, (t0, t1)) in enumerate(zip(scenes, bounds), start=1)]
    with ThreadPoolExecutor(max_workers=int(cfg.get("scene_workers", 4))) as pool:
        results = list(pool.map(process_scene, jobs))
    final_scenes = [r[0] for r in results]
    ambience = [r[1] for r in results if r[1]]

    # 재조립(해상도/프레임레이트 정규화) + 자막 입히기
    cmd = ["ffmpeg", "-y"]
    for s in final_scenes:
        cmd += ["-i", s]
    parts = []
    for k in range(len(final_scenes)):
        d = durations[k]
        # tpad로 짧은 클립은 마지막 프레임을 늘리고, trim으로 계획 길이에 정확히 맞춘다
        parts.append(f"[{k}:v]scale=1280:720:force_original_aspect_ratio=decrease,"
                     f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1,"
                     f"tpad=stop_mode=clone:stop_duration=15,trim=duration={d:.3f},"
                     f"setpts=PTS-STARTPTS[v{k}]")
    parts.append("".join(f"[v{k}]" for k in range(len(final_scenes)))
                 + f"concat=n={len(final_scenes)}:v=1:a=0[vc]")
    parts.append(f"[vc]ass={ass_path}[vo]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[vo]", "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", work_video]
    subprocess.run(cmd, check=True)
    return work_video, ambience


def main():
    global WORK_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--ass", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lipsync", action="store_true")
    ap.add_argument("--remix-video",
                    help="무과금 재믹스: 이전 완성본 영상의 비디오 트랙을 그대로 쓰고 "
                         "(립싱크·omnihuman 결과가 이미 구워져 있음) 캐시된 오디오만 재조합")
    ap.add_argument("--scenes-dir", default="out")
    args = ap.parse_args()

    key = os.environ.get("FAL_API_KEY")
    if not key:
        sys.exit("FAL_API_KEY 환경 변수가 필요합니다. (키를 코드나 채팅에 넣지 마세요)")

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    WORK_DIR = os.path.join(os.path.dirname(args.out) or ".", "audio")
    os.makedirs(WORK_DIR, exist_ok=True)

    lines = parse_ass(args.ass)
    silent = set(cfg.get("silent_styles", []))
    if silent:
        lines = [l for l in lines if l[2] not in silent]
    print(f"자막 {len(lines)}줄 파싱됨 (화면 전용 스타일 {sorted(silent)} 제외)")

    def make_tts(item):
        i, (start, _end, style, name, text) = item
        voice = (cfg.get("name_voices", {}).get(name)
                 or cfg.get("style_voices", {}).get(style)
                 or cfg["default_voice"])
        emotion = (cfg.get("emotion_overrides", {}).get(str(i))
                   or cfg.get("style_emotions", {}).get(style))
        print(f"[{i:03d}/{len(lines)}] {start:7.2f}s {voice}/{emotion or 'neutral'}: {text[:30]}")
        path = tts_line(cfg, key, i, voice, text, emotion)
        if not path:  # 한 번 재시도
            print(f"  [tts {i:03d}] 재시도")
            path = tts_line(cfg, key, i, voice, text, emotion)
        if not path:
            raise RuntimeError(f"[tts {i:03d}] 생성 실패 — 위 로그를 확인하세요.")
        return (start, style, path)

    with ThreadPoolExecutor(max_workers=int(cfg.get("tts_workers", 4))) as pool:
        clips = list(pool.map(make_tts, enumerate(lines, start=1)))

    total = probe_duration(args.video)
    # 내레이션 등 파일 끝에 추가된 줄이 있어도 시간순으로 배치한다
    # (TTS 줄 번호·캐시 파일명은 파일 순서 기준 그대로 유지)
    placed = plan_placement(sorted(clips, key=lambda c: c[0]), total)

    video, ambience = args.video, []
    if args.remix_video:
        # 재믹스: 이전 완성본의 영상 트랙 + 캐시 오디오(line*.mp3, amb*.wav,
        # bgm.audio)만 다시 조합한다. remix_patch에 지정된 장면만 예외적으로
        # omnihuman을 다시 만들어 해당 구간의 영상을 갈아끼운다(그 외 유료 호출 없음).
        video = args.remix_video
        # 재믹스는 장면 클립이 없어도 되므로 계획 길이표(scene_durations)를 그대로 쓴다
        planned = cfg.get("scene_durations")
        durations = ([float(d) for d in planned] if planned
                     else [probe_duration(s) for s in
                           sorted(glob.glob(os.path.join(args.scenes_dir, "scene*.mp4")))])
        bounds, t = [], 0.0
        for i, d in enumerate(durations, start=1):
            bounds.append((t, t + d))
            p = os.path.join(WORK_DIR, f"amb{i:02d}.wav")
            if cached(p):
                ambience.append((t, p))
            t += d
        print(f"재믹스 모드: 영상 {video}, 캐시 현장음 {len(ambience)}개 재사용")

        # 장면 교정 패치: {"장면번호": "소스 클립 이름"} — 그 장면 구간만
        # 소스 클립+대사 오디오로 omnihuman 재생성 후 영상에 이어붙인다.
        patches = {int(k): v for k, v in (cfg.get("remix_patch") or {}).items()}
        if patches:
            narration = set(cfg.get("narration_styles", ["Naration"]))
            placed_dialogue = [p for p in placed if p[2] not in narration]
            dial_wav = render_track(placed_dialogue, total,
                                    os.path.join(WORK_DIR, "dialogue.wav"))
            patch_segs = []
            for i in sorted(patches):
                t0, t1 = bounds[i - 1]
                d = t1 - t0
                seg = os.path.join(WORK_DIR, f"seg{i:02d}.wav")
                subprocess.run(["ffmpeg", "-y", "-i", dial_wav, "-af",
                                f"atrim={t0:.3f}:{t1:.3f},asetpts=PTS-STARTPTS", seg],
                               check=True, capture_output=True)
                src = os.path.join(args.scenes_dir, f"{patches[i]}.mp4")
                print(f"[remix patch {i:02d}] {patches[i]} + 대사({t0:.1f}~{t1:.1f}s) → omnihuman")
                clip = omnihuman_scene(cfg, key, src, seg, i)
                if not clip:
                    sys.exit(f"[remix patch {i:02d}] omnihuman 생성 실패")
                patched = os.path.join(WORK_DIR, f"patched{i:02d}.mp4")
                subprocess.run(["ffmpeg", "-y", "-i", clip, "-vf",
                                (f"scale=1280:720:force_original_aspect_ratio=decrease,"
                                 f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1,"
                                 f"tpad=stop_mode=clone:stop_duration=15,"
                                 f"trim=duration={d:.3f},setpts=PTS+{t0:.3f}/TB,"
                                 f"ass={args.ass},setpts=PTS-STARTPTS"),
                                "-an", "-c:v", "libx264", "-preset", "medium",
                                "-crf", "18", patched], check=True)
                patch_segs.append((t0, t1, patched))
            # 기본 영상에서 패치 구간만 잘라내고 새 클립으로 이어붙인다
            cmd = ["ffmpeg", "-y", "-i", video]
            for _, _, p in patch_segs:
                cmd += ["-i", p]
            n_base = len(patch_segs) + 1
            parts = [f"[0:v]split={n_base}" + "".join(f"[s{k}]" for k in range(n_base))]
            labels, cur = [], 0.0
            for k, (t0, t1, _p) in enumerate(patch_segs):
                parts.append(f"[s{k}]trim={cur:.3f}:{t0:.3f},setpts=PTS-STARTPTS[b{k}]")
                labels += [f"[b{k}]", f"[{k + 1}:v]"]
                cur = t1
            parts.append(f"[s{n_base - 1}]trim=start={cur:.3f},setpts=PTS-STARTPTS[b{n_base - 1}]")
            labels.append(f"[b{n_base - 1}]")
            parts.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[vs]")
            spliced = os.path.join(WORK_DIR, "remix-spliced.mp4")
            subprocess.run(cmd + ["-filter_complex", ";".join(parts), "-map", "[vs]",
                                  "-an", "-c:v", "libx264", "-preset", "medium",
                                  "-crf", "18", spliced], check=True)
            video = spliced
            print(f"장면 패치 {len(patch_segs)}개 반영 → {video}")
    elif args.lipsync:
        narration = set(cfg.get("narration_styles", ["Naration"]))
        placed_dialogue = [p for p in placed if p[2] not in narration]
        print(f"립싱크 대상 대사 {len(placed_dialogue)}줄 (내레이션 {len(placed) - len(placed_dialogue)}줄 제외)")
        video, ambience = rebuild_with_lipsync(cfg, key, args.scenes_dir, args.ass,
                                               placed_dialogue,
                                               os.path.join(WORK_DIR, "rebuilt.mp4"))

    print("배경음악 생성 중...")
    bgm = make_bgm(cfg, key)
    if not bgm:
        print("경고: 배경음악 생성 실패 — 대사만으로 계속 진행합니다.")

    print("믹싱 중...")
    mix(video, placed, bgm, float(cfg.get("bgm_volume", 0.22)), args.out,
        ambience, float(cfg.get("ambience_volume", 0.4)))
    print(f"완료 → {args.out}")


if __name__ == "__main__":
    main()
