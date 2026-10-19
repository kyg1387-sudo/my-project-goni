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

### 2차(이어하기, run 39200684622, 2026-10-19 05:11)
- 미생성 11장면 생성 완료(≈9달러). 검수: S15a·S15b·S16e·S17a·S17c·S17d·S18e·S18h·S18j·S18k 합격. **S17b 불합격**(택시가 카메라 쪽으로 다가와 지나감 — 설계는 멀어지는 후미등) → 동작 문장에 「already driving AWAY, rear facing us, never toward the camera」 보강.
- **S10b는 재생성되지 않음**: `regen_scenes`가 `scene57.mp4`만 지우고 `scene57_take1/2.mp4`는 Artifact에서 복원돼 「기존 파일 재사용」. → S10b를 1테이크(SINGLE_TAKE)로 바꿔 3차 실행(regen 57 102, ≈1.5달러). 교훈 14로 저장.
- 히어로 테이크 확정(TAKE): S13g 2 · S07k 2 · S06a 2 · S13j 2 · 나머지 take1.

### 3차(run 39203842279) + 후처리 반영(run 39205707879, 무과금)
- S10b(1테이크)·S17b 재생성 합격(S17b 후미등 멀어짐 ✓). 후처리 12컷 → `regen_scenes`로 소스 Artifact 갱신(제11장 25).
- burn 실행: run `burn-subtitles` source_run_id=39205707879, add_audio·lipsync=true (OmniHuman 25컷 130초 ≈ 20.8달러 + BGM 4구간·현장음 7컷 소액).

## 3. PHASE 6 마무리(로컬, 무과금)
- burn 결과 9:31.08, OmniHuman 25컷 전부 생성 확인(「재사용」 0). `qa_assembly` 장면 경계 115개 정상, 무음 1곳(394~399s) → 마스터링 드론+룸톤.
- 시청자 검증(11_시청자검증.md) 즉시 수정: 머리 2.0초 트림, 34.4~36.3초 컷 → 본편 9:27.
- 체인: 그레이딩(4조각 병렬 55분) → 트림 → 마스터링(효과음 25종·드론·룸톤·−14 LUFS) → 아웃트로(진행자 5줄: 062·063 재사용 + 080·081 신규 OmniHuman ≈2.1달러 + 065) → 엔드카드 → 한글 검수본 → 480p 미리보기 + 28MB 분할.

## 4. 다음
생성 완료 → export_files=QA 검수 시트 → 히어로 테이크 선택(TAKE) → post → burn-subtitles(OmniHuman·BGM·현장음) → 그레이딩·마스터링(효과음 25종 자동 믹스) → 한글 검수본.
