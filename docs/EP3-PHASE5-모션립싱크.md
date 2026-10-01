# EP3 「김씨와 폐지 할머니」 — PHASE 5 제어된 모션 & 정밀 립싱크

규격서 PHASE 5 산출물. 작성 2026-10-01. 상태: **파일럿 3클립 완료(2합격·1재생성) — 본 실행(41클립) 승인 대기**

## 5-0. 준비된 것 (무료)
- `scripts/generate_video.py`: 장면에 `image`(승인 키프레임)가 있으면 **Image-to-Video**(fal Seedance 1.0 lite i2v, 720p, 5/10초)로 생성. Text-to-Video 경로는 쓰지 않는다.
- `scripts/build_ep3_phase5_scenes.py` → `scripts/scenes/kim-cart-grandma.json`: 44장면 = PHASE 4 키프레임 + PHASE 3 카메라·모션 지시(승인 목록만: 정지·슬로 푸시인·미세 핸드헬드·보행 드리프트). 이전 텍스트→영상 파일은 `scripts/scenes/_archive/`.
- `scripts/audio/kim-cart-grandma.json`: `scene_durations`(조립 정규화), `lipsync_skip_scenes=[2,30,37]`(화자가 화면 밖인 리액션·손 컷).

## 5-1. 실행 순서
1. `generate-video.yml` (skit=kim-cart-grandma): 44클립 생성 → Artifact `kim-cart-grandma-skit-video`, 검수 프레임 `assets/qa/kim-cart-grandma/`.
2. 클립 검수(모션 왜곡·얼굴 녹음 Kill Gate) → 불합격은 `regen_scenes`로 부분 재생성(합격분 재사용).
3. `burn-subtitles.yml` (add_audio=true, lipsync=true): PHASE 1 확정 TTS(`assets/audio-overrides/kim-cart-grandma/`로 복사) + 자막 + 립싱크(S01·S15·S28·S29·S31·S36) + 현장음 + BGM 믹싱 → 완성본.

## 5-2. 컷어웨이 치팅 (규격 5-4) 적용 방식
- 4초 초과 대사는 장면 분할로 이미 교차 편집됨: 김씨 line002 → S01(말하는 얼굴) → S02(최사장 리액션, 립싱크 제외) → S03(가죽끈 B-roll). 김씨 line034 → S29(말하는 얼굴) → S30(최사장 리액션). 할머니 line042 → S36 → S37(손 클로즈업).
- 립싱크 결과에서 치아·구강 왜곡이 보이는 구간은 PHASE 6 조립 때 B-roll 인서트(S03·S08 계열)로 가린다.

## 5-3. 규모·예상 비용 (실행 전 보고)
| 항목 | 수량 | 단가(추정) | 소계 |
|---|---|---|---|
| Image-to-Video 44클립(325초, 720p) | 325초 | 초당 약 $0.036 | 약 $12 |
| 립싱크 6장면(sync-lipsync, 약 60초) | 60초 | 초당 약 $0.05~0.07 | 약 $3~4 |
| 현장음(앰비언스) 44장면 | 44 | 소액 | 약 $1 |
| 불합격 재생성 여유(약 20%) | | | 약 $3 |
| **합계** | | | **약 $19~20 (3만 원 안팎)** |
단가는 fal 요금표 기준 추정치이며 실행 로그·fal 대시보드에서 실제 금액을 확인한다.

## 5-4. 파일럿 결과 (2026-10-01, S01·S03·S06, 25초)
| 클립 | 판정 | 비고 |
|---|---|---|
| S01 대치 투샷 10s | 합격 | 0/3/6/9초 얼굴·의상 동일, 김씨 입 자연 개폐(립싱크 전), 모션 왜곡 없음 |
| S03 가죽끈 ECU 5s | 불합격 | 1초대에 손이 들어와 손잡이를 잡음(무인 컷 위반) → 무인 컷 프롬프트에 "사람·손 진입 금지" 명시 후 본 실행에서 재생성 |
| S06 할머니 보행 10s | 합격 | 보행 속도 드리프트 자연, 두건·의상 유지. 경미: 후반 배경에 차량 진입 |
- 합격 2클립 중 S01만 `assets/video-overrides/kim-cart-grandma/scene01.mp4`로 재사용. S06 파일럿 클립은 손잡이 없는 구 키프레임으로 만든 것이라 폐기(리어카 통일 후 본 실행에서 재생성).
- 생성 규격 실측: 1248x704, 24fps, 10.04초/5.04초 (조립 시 1280x720·계획 길이로 정규화).
