# 인수인계 — 일본판 『明日から来なくていい』 (ashita-kara-ja)

갱신: 2026-10-11. 다른 세션(모델 무관)이 이어받기 위한 문서.
읽는 순서: `CLAUDE.md`(최신 규격서, 제0~9장) → `productions/ashita-kara-ja/00_script_ja.md` → `productions/ashita-kara-ja/10_수정요청목록.md`.
호칭: 사용자는 「고니감독님」.

## 1. 현재 위치

**PHASE 1 진행 중.** 대본 v1.1 동결(82줄) → 오디션 26샘플·캐스트 확정 → 본녹음 81줄(언어 검사 통과, 6줄 재녹음) → 실측 Lock 9:38.6으로 기준 미달 → **보강안 10줄(`productions/ashita-kara-ja/13_Lock보강안.md`) 고니감독님 승인 대기**. 달러 지출 0(Typecast 크레딧만).
브랜치 `claude/happy-volta-9w5oxb`. 최신 제작 도구·워크플로·규격서는 `claude/sweet-galileo-xbd5iu`(버들잎·EP4 일본판 제작 브랜치)에서 **파일 단위로** 가져왔다(제9장 6항, 미디어·글꼴 제외).

## 2. 이전 작업과의 관계 (중요)

이 브랜치의 첫 작업(2026-10-11 오전)은 옛 main 기준 규칙으로 만든 텍스트→영상 자산(장면 72개·10초 블록·MiniMax·sync-lipsync)이었다.
최신 규격서와 충돌(텍스트→영상 금지, OmniHuman만 사용, 제0장 구간 공식)해서 **전부 삭제**했고, 그때 만든 일본어 번역은 v1 대본의 바탕으로만 썼다.

## 3. 다음 단계 (보강안 승인 후: 대본 10줄 삽입·v1.2 표시 → 추가 10줄은 별도 스펙으로 녹음해 기존 번호 유지 → `remap_tts_cache.py`로 시간 순 번호 통합 → `build_lock.py` 재계산 → Lock 승인 → 아래 4번부터)

1. 고니감독님 대본 승인 → `00_script_ja.md` 상태를 🔒 동결로 바꾼다(이후 문장·쉼표 수정 금지).
2. 오디션: `generate-video.yml` 실행, 입력 `audition_spec=ashita-voices` (Typecast 크레딧, 달러 0). 샘플은 `assets/auditions/ashita-voices/`에 커밋된다 → `qa_audio_dir=assets/auditions/ashita-voices, qa_lang=ja, qa_model=large-v3`로 언어 검사(무료) → 고니감독님 청취로 배역 확정 → `04_목소리추천.md`.
3. 본녹음 81줄(가나 변형은 대본 5장) → 언어 검사 → `build_lock.py`(버들잎 것을 복사)로 실측 Lock 타임라인 → 9:40 이상·광고 3:30/7:00 확인 → 승인.
4. PHASE 2 시트(인물 5·장소 6·소품 3, 약 0.6~1.2달러) — 실행 전 규모 보고.
5. 그 뒤는 버들잎 `01_제작지침-김씨실증반영.md` 2장의 순서를 따른다(PHASE 3 생성기 `build_yanagi_phase3.py` 복사·수정 등).

## 4. 아직 안 가져온 것

- `scripts/fonts/*.ttf`(2~9MB, 일본어 글자 합성용) — PHASE 4 전에 `git checkout origin/claude/sweet-galileo-xbd5iu -- scripts/fonts`로 가져온다.
- 엔드카드·진행자 초상 등 `assets/`의 채널 공용 자산 — PHASE 6 전에 필요한 파일만 가져온다.
