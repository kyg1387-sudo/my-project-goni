#!/usr/bin/env bash
# 『タワマンのボスママ』 마무리(무과금, 로컬): 전달 조각 → 본편 → 효과음 → 회의장 그레이딩 → 아웃트로·엔드카드 → 전수 검수 → 한국어 검수본·480p·28MB 분할
# 사용법: scripts/finish_tower.sh   (deliveries/tower-skit-final.mp4.part-* 가 최신 burn 결과여야 함)
set -euo pipefail
cd "$(dirname "$0")/.."
if ls deliveries/tower-skit-final.mp4.part-* >/dev/null 2>&1; then cat deliveries/tower-skit-final.mp4.part-* > out/tower-main-burn.mp4; fi   # 조각을 지운 뒤 재실행이면 out/ 의 burn 본 사용
# burn 이후에 고친 하드컷 컷은 완성본에서 바로 교체(무과금) — PATCH="S10a2 ..."
cp out/tower-main-burn.mp4 out/tower-main.mp4
for sid in ${PATCH:-}; do
  python3 scripts/patch_final_cut.py tower "$sid" out/tower-main.mp4 out/tower-main-p.mp4 productions/tower-bossmom-ja/qa/assembly/report.txt
  mv out/tower-main-p.mp4 out/tower-main.mp4
done
# 립싱크 클로즈업 배경을 같은 회의장 만석으로(수정 17)
python3 scripts/tower_bg_swap.py out/tower-main.mp4 out/tower-main-bg.mp4 productions/tower-bossmom-ja/qa/assembly/report.txt
mv out/tower-main-bg.mp4 out/tower-main.mp4
MAIN=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/tower-main.mp4)
python3 scripts/tower_sfx_mix.py out/tower-main.mp4 out/tower-main-sfx.mp4
python3 scripts/tower_grade.py out/tower-main-sfx.mp4 out/tower-main-graded.mp4 productions/tower-bossmom-ja/qa/assembly/report.txt
OUTRO=out/tower-outro.mp4 ENDCARD=assets/brand/endcard-midam-ja.mp4 OUT_SIZE=1920x1080 \
  python3 scripts/append_outro.py out/tower-main-graded.mp4 out/tower-final-ja.mp4
python3 scripts/qa_assembly.py out/tower-main.mp4 scripts/audio/tower.json scripts/storyboard/tower.json productions/tower-bossmom-ja/qa/assembly >/dev/null
python3 scripts/make_ko_review_tower.py out/tower-final-ja.mp4 out/tower-ko-review.mp4 "$MAIN"
rm -f deliveries/tower-ko-review.mp4*
split -b 28m -d out/tower-ko-review.mp4 deliveries/tower-ko-review.mp4.part-   # GitHub 100MB 한도
ffmpeg -v error -y -i out/tower-final-ja.mp4 -vf scale=854:480 -c:v libx264 -preset medium -crf 26 -c:a aac -b:a 96k -movflags +faststart deliveries/tower-final-ja-480p.mp4
rm -f deliveries/tower-final-ja.mp4.part-* deliveries/tower-skit-final.mp4.part-*
split -b 28m -d out/tower-final-ja.mp4 deliveries/tower-final-ja.mp4.part-
md5sum out/tower-final-ja.mp4 > deliveries/tower-final-ja.md5
ls -la deliveries | grep tower
