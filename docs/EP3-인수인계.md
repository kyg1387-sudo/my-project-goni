# EP3 「김씨와 폐지 할머니」 인수인계 (다른 세션에서 이어서 작업할 때 먼저 읽을 것)

갱신 2026-10-01 · 제작 브랜치 **`claude/zen-cori-8ren7o`** (이 브랜치에서만 작업·푸시) ·
현재 상태: **PHASE 1·2 Lock 완료, 대사 8줄 목소리 최종 채택 완료(10-01 2차 재확정), PHASE 3 설계 완료 — 사용자 PASS 대기.
PHASE 4(키프레임 렌더링, 유료)는 아직 시작하지 않았다.**

> 이 문서의 2026-10-01 이전 판(브랜치 vigilant-davinci)은 "유료 단계 시작 전, 캐릭터 시트부터
> 시작, 김씨=감독 얼굴"이라 적혀 있었다 — 모두 **폐기**. 아래가 현재 사실이다.

## 1. 먼저 읽을 지침 (순서대로)

1. `CLAUDE.md` — 시네마틱 AI 영상 제작 표준 운영 규격서(PHASE 1~6). 모든 작업의 시스템 규칙.
2. `docs/EP3-PHASE1-대본동결-오디오앵커.md` — 동결 대본 + 실측 Lock 타임라인(48줄, 총 325초).
3. `docs/EP3-PHASE2-마스터에셋.md` — 캐릭터·로케이션 시트 판정표, 참조 ID 규칙, 공통 프리셋·네거티브.
4. `docs/EP3-PHASE3-샷리스트.md` — 44컷 샷 리스트 + 씬별 키프레임·모션 프롬프트
   (원본 데이터 `scripts/storyboard/kim-cart-grandma.json`, 생성기 `scripts/build_phase3_doc.py`).
5. 참고: `docs/아카이브-이전제작지침(CLAUDE.md-2026-10-01까지).md`(EP1~EP3 실증 교훈 ①~㉔),
   `docs/영화제작규칙집.md`, `docs/기획안-김씨시리즈.md`.

## 2. 확정된 결정 (다시 묻지 말 것)

- **김씨 얼굴 = 기존 AI 배우 유지** (EP1·EP2와 동일 인물, 참조 `assets/portraits/guard-kim-secret-cap2/kim-gold-1.png`).
  사용자 결정 2026-10-01. 감독 사진(`assets/portraits/kim-reference-studio.jpg` 등)은 보관만 하고 EP3에 쓰지 않는다.
  명찰·모자·문자 없는 민무늬 네이비 경비복으로 고정.
- **마스터 에셋(PHASE 2 Lock, 전부 합격)**: 김씨 `assets/portraits/ep3-cast/kim-sheet-1.png`,
  할머니 `assets/portraits/ep3-cast/grandma-sheet-1.png`, 최사장 `assets/portraits/ep3-choi/choi-sheet-1.png`,
  로케이션 5장(`ep3-cast/loc-*-1.png`) → 라벨 없는 셀 20장 `ep3-cast/cells/loc-<장소>-<day|night|key1|key2>.png`.
  참조 호출: `KIM@<셀>`, `GMA@<셀>`, `CHOI@<셀>`, `LOC@<장소>-<상태>`.
- **대본 동결(PHASE 1)**: 문장·쉼표까지 고정. 수정 금지. 자막 `subs/kim-cart-grandma.ass`,
  컷 길이 `scripts/scenes/kim-cart-grandma.json`(44컷, 5|10초, 합 325초), 오디오 `scripts/audio/kim-cart-grandma.json`.
- **BGM 2구간**: 36~106초 건조한 피아노 → 중간 **의도적 무음** → 220~319초 현악 상승(`bgm_segments`).
- **목소리**: 내레이터=ElevenLabs `5n5gqmaQi9Ewevrz7bOS`, 김씨=ElevenLabs `8vwSOQHQApfVx993mKf9`,
  최사장=Typecast 명주 `tc_656059fc4db338e38f77d0bc`(ssfm-v30), 할머니=Typecast `tc_60ad0841061ee28740ec2e1c`.
  오디오 설정의 MiniMax 값은 폴백일 뿐이다.
- 장르: 잔잔한 미담·힐링 드라마. 김씨는 언성을 높이지 않는다. 제목·썸네일에 지어낸 사실·"충격적 반전" 금지.

## 3. 지금 사용자가 결정해야 할 것

1. **PHASE 3 샷 리스트 PASS** — `docs/EP3-PHASE3-샷리스트.md`. PASS 전에는 PHASE 4 렌더링(유료) 금지.
   (목소리는 10-01 최종 채택 완료: 김씨 ElevenLabs 원본 1.2배속, 최사장 Typecast tonedown 템포 1.3,
   할머니 Typecast 스마트 감정 템포 1.1. 채택본 `assets/auditions/kim-cart-grandma-tts/line*.mp3`, 구판은 `_superseded/`.)

## 4. PASS 이후 순서 (규격서 그대로)

1. PHASE 4: 승인 시트 참조로 키프레임 스틸 44장 생성 → Kill Gate(외계어·손가락·눈동자) 검수.
   유료 실행 전 규모·비용을 사용자에게 먼저 알리고 승인받는다.
2. PHASE 5: 승인 키프레임만 image-to-video(텍스트→영상 금지), 대사 컷은 PHASE 1 오디오로 립싱크,
   4초 초과 발화는 컷어웨이 치팅(샷 리스트의 Edit Strategy에 이미 명시).
3. PHASE 6: 3중 사운드 레이어·J-Cut·얼굴 복구 → 제4장 체크리스트 전항 PASS → 완성본.
4. 완성 전달 시 글로벌 진출 가이드(일본어 자막 .srt, 언어별 제목·설명)와
   `docs/EP3-업로드메타데이터.md` 함께 제공.

## 5. 검증 메모 (2026-10-01, 무과금)

PHASE 3 샷 리스트를 Lock 타임라인·에셋과 대조: 대사 8줄의 화자-컷 일치 0건 불일치, 컷 길이 합 325초 일치,
LOC 셀 20개 전부 존재. S30(최사장 리액션 컷)에 김씨 대사 꼬리 1.3초가 걸치지만 Edit Strategy가
S29 앵글의 김씨 얼굴로 덮도록 명시돼 있어 규격 적합.

## 6. 비용 원칙 리마인드

유료 실행 전 규모를 먼저 알리고 승인받을 것. 재생성은 부분만. AI 실수로 인한 재생성은 무과금
경로(기존 클립 편집·캐시 재조합)부터 찾고, 불가피하면 실수 비용임을 밝히고 승인 후 실행.
