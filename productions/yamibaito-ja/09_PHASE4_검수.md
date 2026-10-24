# 『時給5万円の罠』 PHASE 4 키프레임 Kill Gate 기록 (2026-10-24)

> 판정 기준: 제4장 + 제19장 7 ⑤(얼굴 일관성·눈물 질감·가짜 글자·소품 고증·시선·구도). 합격판은 `assets/portraits/yamibaito-kf-ok/`에 모은다.

## 1. 립싱크 3컷 시범 (pilot → r2 → r3, 14장 0.42달러)

| 컷 | 결과 | 비고 |
|---|---|---|
| S02f | 합격 r2-1 | 명찰 cv2 인페인트. 1차: 눈물(네거티브 오검출)·귀걸이·명찰 |
| S05h | 합격 r2-2 | 손전등·시선 왼쪽 |
| S09g | 합격 r3-1 | 카메오 사진 1장만 참조(시트 참조 시 백발) + 명찰 인페인트 |

## 2. 립싱크 전체 a (10장 0.30달러) — 합격 2 · 재생성 8(r4)

| 컷 | 판정 | 결함 → 조치 |
|---|---|---|
| S03f | 합격 | — |
| S09k | 합격 | 흰머리 조금 있으나 사진 범위 |
| S02bh | 재생성 | 원경·정면 응시 → 단독 CU 구도 문장(SPEAKER CLOSE)·GAZE LOCKED |
| S05f | 재생성 | 원경 → 같음 |
| S06n | 재생성 | 悠斗 귀걸이·정면 응시 → 「plain bare earlobes」·GAZE |
| S07h | 재생성 | 정면 응시·健太 소매 패치 |
| S07j | 재생성 | 눈물 양 뺨 줄기(고인 눈물이어야) → 생성기 TEARS_POOL(「NOT running」 감지)·_DRY |
| S09i | 재생성 | 店長 백발 재발 → JET-BLACK·합격판 S09g 참조 |
| S10j | 재생성 | 눈물 줄기·귀걸이·정면 |
| S11b | 재생성 | 눈물 줄기·정면 |

## 3. b1 (69장 2.07달러) — 합격 49 · 재생성 20(r5) · 인페인트 5

| 결함 패턴 | 컷 | 조치 |
|---|---|---|
| 「폰 화면 단독」에 사람(외국인 남성)이 생김 | S02b·S02ba·S02g·S03b | top-down 무인 문장 + t2i |
| 단독 CU가 원경·어안·전신 | S02be·S05g·S05i·S06e | face cu는 장소 참조 제거 + FACE_CU 구도 문장(생성기 기본) |
| 같은 인물 2명 | S02bf·S04a·S05b | PEOPLE LOCKED(「appears only ONCE」, 생성기 기본) |
| 군중 수 부족(1명) | S04i·S05c·S06b·S06e2 | 「exactly FOUR / a DOZEN」 수치 고정 |
| 소품 변형 | S04h(렌즈 물체)·S05b(구멍 뚫린 가면)·S04j(안대 벗음)·S02d(얼굴 노출) | 문장 고정 |
| 가짜 글자 | S06c(통장 한자)·H4(타이틀 배경에 남자 얼굴) | 「plain pastel booklets, blank」·「NO PEOPLE」 |
| 작은 명찰·로고 | S01d·S02c·S02e·S02l·S03l(TOYOTA) | cv2 인페인트(무료) |

합격(49): H0·H1·H2a·H2b·S01a·S01b·S01c·S01d·S02a·S02bb·S02bc·S02bd·S02bg·S02bi·S02bj·S02c·S02e·S02h·S02i·S02j·S02k·S02l·S03a·S03c·S03d·S03e·S03g·S03h·S03i·S03j·S03k·S03l·S03m·S04b·S04c·S04d·S04e·S04f·S04g·S05a·S05e·S05j·S05k·S05k2·S06a·S06d·S06f·S06g·S06h

## 4. 립싱크 r4 (16장 0.48달러) — 합격 6 · 재생성 2(S10j·S11b → r7, 눈물 문장 전부 제거 DRY_ONLY)

합격: S02bh-1·S05f-1·S06n-2·S07h-2·S07j-1·S09i-1(흑발 성공). 불합격: S10j(두 테이크 모두 뺨 줄기)·S11b(-1 배경에 健太 2명, -2 줄기).

## 5. b2 (69장 2.07달러) — 합격 56 · 재생성 13(r7) · 인페인트 6

| 결함 패턴 | 컷 | 조치 |
|---|---|---|
| 인서트에 얼굴·몸이 들어옴 | S06i·S07k | INSERT_HARD(「cut at the forearms」)를 프롬프트 맨 앞(생성기 기본) |
| 정면 응시 | S06o2·S07i2·S11l | FACE_CU에 「NEVER into the lens」 기본 추가 |
| 같은 인물 2명 | S07k2 | PEOPLE LOCKED |
| 통장·책 가짜 글자 | S06k·S06l | 「plain pastel booklets, BLANK」 |
| 애니 화풍 손 | S07i | REAL PHOTOGRAPH 문장 맨 앞 |
| 전신·어안 | S07o·S11l | FACE_CU |
| 무인 컷에 사람 | S08l(외국인 남성)·S11k(다리) | NO PEOPLE 강조 |
| 키패드가 작음 | S09b | MACRO 70% |
| 작은 명찰·귀걸이·배경 포스터 | S06k2·S06m·S08m·S10h·S10k·S11e | cv2 인페인트·흐림 |

합격판 116장 → `assets/portraits/yamibaito-kf-ok/`. 남은 재생성: r5 20컷(33장) 실행 중, r7 15컷(24장) 대기.
