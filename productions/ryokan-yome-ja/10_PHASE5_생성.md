# #03 『老舗旅館の嫁』 PHASE 5 생성·교체 클립 기록

작성 2026-10-19. 규격 제7장 2·3·4·8, 제11장 7·8·25.

## 1. 무료 교체 클립 (build_ryokan_overrides.py, 70개, 0달러)
| 종류 | 수 | 구현 |
|---|---|---|
| still(정지) | 36 | 인물 컷 = 2.5D 시차(rembg 인물 마스크, dolly_in/truck/dolly_out 교차), 무인 컷 = 슬로 푸시인·팬 |
| omni(대사 정지 프레임) | 25 | 정지 → burn 단계 OmniHuman 음성 구동 |
| gfx | 7 | 합성 키프레임 + 상태 크로스페이드(S11c 4.8→3.1 5상태, S13h 카운트업 5상태) |
| card | 2 | S01f 타이틀 = 직전 야간 현관 블러 위 / S01g 「三か月前」 = 새벽 주방 첫 프레임 위 좌하단(제11장 20, 암전 0) |
QA(`qa_overrides_ryokan.py`): 70개 문제 0건(1차 S10d 손상 → 재생성). 시간축 샘플 시트 검수 완료.

## 2. 유료 i2v 생성 (generate-video.yml skit=ryokan)
- 대상 45컷: hero 18(kling v3 pro 1080p, 2테이크) + pro/lite 27. 예산 `budget_usd` 47.7(생성기 추산).
- 1차 실행 run 39187402781 (2026-10-19 01:53 UTC). 실행 중 S10b 키프레임 패치 오류(얼굴 뭉개짐)를 발견해 수정본을 푸시 → 완료 후 `resume_run_id` + `regen_scenes`로 S10b(장면 번호 확인)만 재생성(약 1.2달러).
- 후처리(`build_ryokan_overrides.py post <clips>`): S07g dutch5, S10b hand, S11f dutch7, S18e hand, S13g push(돌리줌 대체), S10a·S13a 시점 소자막, S03a·S18k 명판 추적(SignTracker).

### 1차 생성 결과(2026-10-19 03:28)
- 추산 38.16달러(45컷·히어로 36테이크). 장면 83(S13g) 생성 중 fal 잔액 소진(403) → 장면 93·94·100~104·109·112·114·115 미생성(15클립). 감독님 충전 후 `resume_run_id=39187402781 regen_scenes=57`로 나머지 11장면 + S10b 재생성(≈11.3달러) 실행.
- 1차 검수(1초 타일): 합격 다수. 메모 — S13g take2 채택(수화기 낙하, take1은 손이 떠 있음) · S14a take1 채택(take2 고개 숙임 부자연) · S10b 마이 양손 들기(키프레임 기인) → 재생성 대기 · 나머지 히어로는 두 테이크 모두 안정, 동작 큰 쪽 우선 선택 예정.

## 3. 다음
생성 완료 → export_files=QA 검수 시트 → 히어로 테이크 선택(TAKE) → post → burn-subtitles(OmniHuman·BGM·현장음) → 그레이딩·마스터링(효과음 25종 자동 믹스) → 한글 검수본.
