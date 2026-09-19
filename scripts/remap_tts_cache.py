#!/usr/bin/env python3
"""자막에서 TTS 줄을 삭제한 뒤, 캐시된 lineNNN.mp3 번호를 새 번호 체계로 옮긴다.

generate_audio.py는 TTS 캐시를 '무음 스타일 제외 후 줄 번호'로 저장하므로,
줄을 삭제하면 그 뒤 번호가 전부 당겨진다. 이 스크립트로 캐시 파일명을 함께
당겨 주면 삭제된 줄만 빼고 기존 TTS(그리고 그에 맞춘 립싱크)를 전부 재사용한다.

사용법: python3 scripts/remap_tts_cache.py <audio_dir> <삭제된 옛 줄 번호...>
예:     python3 scripts/remap_tts_cache.py out/audio 3 58

삽입 모드: --insert <새 번호 체계에서 삽입된 줄 번호...>
예:     python3 scripts/remap_tts_cache.py out/audio --insert 1 13 41
(내레이션 등 줄 추가 시 그 뒤 캐시 번호를 밀어 기존 TTS를 재사용한다.
 삽입된 번호 자리는 비워 두므로, 오버라이드나 새 TTS 생성으로 채운다.)
"""

import os
import sys


def insert_mode(audio_dir, inserted):
    olds = sorted((int(f[4:7]) for f in os.listdir(audio_dir)
                   if f.startswith("line") and f.endswith(".mp3") and f[4:7].isdigit()),
                  reverse=True)  # 뒤로 미는 이동이므로 내림차순 처리가 안전하다
    for old in olds:
        # 새 번호 = old + (old를 새 체계로 옮겼을 때 그보다 앞에 오는 삽입 수)
        new = old
        for k in sorted(inserted):
            if k <= new:
                new += 1
        if new == old:
            continue
        src = os.path.join(audio_dir, f"line{old:03d}.mp3")
        dst = os.path.join(audio_dir, f"line{new:03d}.mp3")
        if os.path.exists(dst):
            sys.exit(f"충돌: {dst} 이미 존재 — 중단")
        os.rename(src, dst)
        print(f"이동: line{old:03d}.mp3 → line{new:03d}.mp3")
    print("삽입 재매핑 완료")


def main():
    audio_dir = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "--insert":
        if not os.path.isdir(audio_dir):
            print(f"{audio_dir} 없음 — 건너뜀 (복원된 캐시가 없는 실행)")
            return
        insert_mode(audio_dir, sorted(int(a) for a in sys.argv[3:]))
        return
    removed = sorted(int(a) for a in sys.argv[2:])
    if not removed:
        sys.exit("삭제된 줄 번호를 하나 이상 지정하세요.")
    if not os.path.isdir(audio_dir):
        print(f"{audio_dir} 없음 — 건너뜀 (복원된 캐시가 없는 실행)")
        return

    for n in removed:
        p = os.path.join(audio_dir, f"line{n:03d}.mp3")
        if os.path.exists(p):
            os.remove(p)
            print(f"삭제: line{n:03d}.mp3 (자막에서 제거된 줄)")

    olds = sorted(int(f[4:7]) for f in os.listdir(audio_dir)
                  if f.startswith("line") and f.endswith(".mp3") and f[4:7].isdigit())
    for old in olds:  # 앞으로 당기는 이동이므로 오름차순 처리가 안전하다
        new = old - sum(1 for r in removed if r < old)
        if new == old:
            continue
        src = os.path.join(audio_dir, f"line{old:03d}.mp3")
        dst = os.path.join(audio_dir, f"line{new:03d}.mp3")
        if os.path.exists(dst):
            sys.exit(f"충돌: {dst} 이미 존재 — 중단")
        os.rename(src, dst)
        print(f"이동: line{old:03d}.mp3 → line{new:03d}.mp3")
    print("재매핑 완료")


if __name__ == "__main__":
    main()
