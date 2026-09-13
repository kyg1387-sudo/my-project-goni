# AI 드라마 영화 제작 파이프라인

이 저장소는 AI 생성 영상으로 한국 드라마(가로 16:9 롱폼, 5~15분)를 만드는 파이프라인이다.
새 작품을 만들 때는 아래 규칙을 기본으로 적용한다.

## 제작 원칙 (품질 기준)

1. **화자-화면 일치**: 대사가 나오는 동안 화면에는 반드시 그 대사를 말하는 인물이
   나와야 한다. 한 장면(클립)에는 한 화자의 대사만 배치한다.
2. **드라마 형식**: 해설 내레이션을 쓰지 않는다. 배경 설명은 인물 대화로 풀고,
   시간·장소 경과는 소리 없는 화면 자막 카드(Caption 스타일)로 표시한다.
   회상 보이스오버(예: 고인의 유언)만 예외적으로 허용한다.
3. **한국어 전용**: TTS는 language_boost=Korean, 장면 프롬프트에 "한국어로 말하는
   입 모양, 영어 없음"을 명시한다. 현장음 negative_prompt로 말소리·영어를 차단한다.
4. **립싱크**: 대사 장면 프롬프트에는 "정면 상반신, 입을 자연스럽게 움직이며"를
   명시하고, 고개 숙임·인사 같은 동작 장면에는 대사를 넣지 않는다(무언 Action 장면).
5. **인물 일관성**: 등장인물 외형은 고정 문구(상수)로 정의해 모든 장면 프롬프트에
   동일하게 반복한다.

## 파일 구조

- `scripts/build_full_assets.py` — 대본(SECTIONS) → 장면/자막/오디오 설정 3종 생성기.
  새 작품은 이 파일의 SECTIONS 구조(beat 정렬 방식)를 복사해 만든다.
  실행하면 화자-장면 정렬이 자동 계산된다. 생성 후 반드시 정렬 검증을 돌릴 것.
- `scripts/scenes/<작품>.json` — 장면 프롬프트. 항목은 `{"prompt", "duration": 5|10}`.
- `subs/<작품>.ass` — 자막. 스타일: 화자별 색상 + Naration(보이스오버) + Caption(무음 카드).
- `scripts/audio/<작품>.json` — 목소리·감정·현장음·BGM 설정.
  `narration_styles`=립싱크 제외, `silent_styles`=TTS 제외(화면 전용).
- `scripts/generate_video.py` — 장면별 클립 생성 (Ark Seedance / fal.ai 폴백,
  장면별 5/10초, out/sceneNN.mp4가 이미 있으면 재사용 = 이어하기).
- `scripts/generate_audio.py` — TTS·립싱크·현장음·BGM 생성 후 믹싱.

## 제작 순서 (GitHub Actions)

1. `콩트 영상 생성` (generate-video.yml): inputs `skit=<작품>`.
   실패 시 같은 워크플로를 `resume_run_id=<실패한 run id>`로 재실행하면
   이미 생성된 장면을 재사용한다.
2. `콩트 영상 자막 입히기` (burn-subtitles.yml): inputs
   `skit=<작품>, source_run_id=<1번 run id>, add_audio=true, lipsync=true, commit_output=true`.
   중간 실패 시 `resume_run_id`로 TTS/립싱크 산출물을 복원해 이어한다.
3. 완성 영상은 브랜치 `deliveries/`에 커밋된다. 100MB 초과 시 90MB 조각으로
   분할되며 `cat <이름>.part-* > <이름>.mp4`로 복원한다.

API 키는 GitHub Secrets(FAL_API_KEY, ARK_API_KEY)에만 둔다. 코드/채팅에 넣지 말 것.

## 검증 (생성 자산 커밋 전 필수)

- 자막의 모든 대사 줄이, 그 시간대 장면 프롬프트의 화자와 일치하는지 초 단위로 검사
  (이 세션들에서 쓰는 검증 스크립트: 장면 경계·화자·MUTE 여부 확인, 불일치 0건이어야 함).
- emotion_overrides 인덱스는 silent_styles 제외 후의 TTS 줄 번호 기준이다.
