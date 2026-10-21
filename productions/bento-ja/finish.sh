#!/usr/bin/env bash
# bento 마무리 체인(로컬·무과금, 제12장 9 순서) — burn 결과 → 시간 점프 디졸브·시점 자막·회상 색 → 효과음·룸톤·−14 LUFS
# → 아웃트로(진행자 27초) + 엔드카드 → 최종 라우드니스 확인. 사용법: bash productions/bento-ja/finish.sh <작업폴더>
set -euo pipefail
W=${1:?작업 폴더}
cd "$(dirname "$0")/../.."
cat deliveries/bento-skit-final.mp4.part-0* > "$W/raw.mp4"
python3 productions/bento-ja/time_transitions.py "$W/raw.mp4" "$W/tt.mp4"
python3 productions/bento-ja/mix_sfx.py "$W/tt.mp4" "$W/mix.mp4"
OUTRO=out/bento-outro.mp4 ENDCARD=assets/brand/endcard-midam-ja.mp4 OUT_SIZE=1920x1080 \
  python3 scripts/append_outro.py "$W/mix.mp4" "$W/full.mp4"
ffmpeg -v error -y -i "$W/full.mp4" -c:v copy -af "loudnorm=I=-14:TP=-1.0:LRA=11" -c:a aac -b:a 256k "$W/bento-final.mp4"
ffmpeg -i "$W/bento-final.mp4" -af ebur128 -f null - 2>&1 | grep -E "I:|Peak" | tail -2
ffmpeg -i "$W/bento-final.mp4" -af silencedetect=n=-60dB:d=2 -f null - 2>&1 | grep -c silence_start || true
ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/bento-final.mp4"
