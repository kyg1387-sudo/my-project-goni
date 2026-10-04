# EP4 「김씨의 크리스마스」 — PHASE 2 기준 마스터 에셋 고정

규격서 PHASE 2 산출물. 작성 2026-10-04. 상태: **Kill Gate 검수 완료 — 사용자 승인 대기**
스펙 `scripts/portraits/ep4-cast.json`(generate-video.yml portraits_spec=ep4-cast), 출력 `assets/portraits/ep4-cast/`, 셀 `assets/portraits/ep4-cast/cells/`(분할기 `scripts/split_sheet_cells.py`, 무과금).
검수용 인물 셀 모음: `docs/EP4-PHASE2-인물셀-검수.png`.

## 2-0. 공통 프리셋·네거티브 (EP3와 동일, 잠금)
`Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, soft natural key light from upper-left, subtle warm rim light, no flat lighting`
네거티브: `gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers`

## 2-1. 캐릭터 시트 Kill Gate

| 인물 | 파일 | 차수 | 판정 | 비고 |
|---|---|---|---|---|
| 김씨(겨울) | `kim-winter-sheet-1.png` | 2차 | **합격** | 1차: 9칸 중 5칸 재킷 누락(EP3 시트 전체를 참조해 복사) → 얼굴 셀(`ep3-cast/cells/kim-front.png`)만 참조로 재생성. EP3 얼굴과 일치, 9칸 모두 짙은 감색 패딩. 경미: 보풀·낡음이 약함 → 키프레임 문장으로 보강 |
| 엄마 | `mom-sheet-1.png` + `mom-expr-sheet-1.png` | 2차 + 표정 시트 | **합격(조건)** | 1차: 안경(직원과 겹침)·칸마다 얼굴 다름. 2차: 상단·중단 6칸 합격, 하단 표정 줄이 다른 얼굴 → 사용 안 함(`cells/_unused/`). 정면 셀 참조 표정 시트(중립·감사 미소·울먹임) 별도 생성 → 얼굴 일치. 경미: 코트 깃 작은 핀 |
| 아이(렌) | `hajun-sheet-1.png` | 2차 | **합격** | 1차: 6칸(뒷모습·45도 누락). 2차 9칸, 얼굴·의상 일치. 정면 얼굴은 표정·전신 셀 사용 |
| 관리소 직원 | `clerk-sheet-1.png` | 1차 | **합격** | 3번째 표정 칸(렌즈 붉은 색·손가락 침입) 불량 → 사용 안 함. 엄마와 머리·안경·의상 3가지 차별 |

참조 호출 표기: `KIMW@<셀>`(김씨 겨울), `MOM@<셀>`, `REN@<셀>`, `CLERK@<셀>`, `PROP@<셀>`, `LOC@<장소>-<day|night|key1|key2>`. EP3 자산은 `GMA@`(할머니 카메오), `CART@`(리어카).

## 2-2. 소품 시트
| 시트 | 판정 | 비고 |
|---|---|---|
| `props-xmas-sheet-1.png` (트리·털실 별·봉투+꽃무늬 수첩·주전자) | **합격** | 경미: 수첩 표지 라벨에 미세 자국 → 수첩 클로즈업은 EP3 S22 크롭과 함께 참조, 라벨 부분 프레임 밖. 주전자 받침이 캠핑 버너형 → 경비실 장면은 경비실 셀(석유난로)을 우선 |

## 2-3. 로케이션 시트 (2x2: day / night / key1 / key2)
| 장소 | 판정 | 비고 |
|---|---|---|
| 18층 복도 `loc-corridor-18f` | 합격 | 호수 없음. 경미: 도어록 키패드 무늬 → 얕은 심도로 흐림 |
| 1801호 거실 `loc-apt-1801` | 합격 | 경미: 낮 셀 좌상단 액자 → 그 구석 프레임 밖 |
| 관리사무소 `loc-mgmt-office` | **합격(로컬 보정)** | 2회 생성 모두 벽 게시물 외계어 → 재생성 대신 창구 셀의 게시물을 로컬로 지우고 유리창 안을 흐림 처리한 `cells/loc-mgmt-office-key1-clean.png`를 참조로 사용(무과금) |
| 계단실·우편함 `loc-stairwell` | 합격 | |
| 겨울 경비실 `loc-guard-booth-winter` | 합격(조합) | 2차: 낮 셀 컬러 복구. 사진 안 라벨 글자는 셀 하단 10% 크롭으로 제거. 밤 난로 컷은 1차(`cells/loc-guard-booth-winter-v1-key1/key2.png`) 사용 |
| 겨울 정문 `loc-apt-gate-winter` | 합격 | key1(성에 낀 경비실 창)·key2(새벽 단지) 활용 |

## 2-4. 생성 집계 (fal)
- 1차 11장 + 재생성 5장 + 엄마 표정 시트 1장 = **17장**(약 0.7달러). 잔액 49.65(시트 16장 후 캡처, 충전 약 20 포함).
- 셀 분할·게시물 제거·라벨 크롭은 로컬(무과금).

## 2-5. 다음 (PHASE 3, 무료)
PHASE 1 Lock 타임라인(05:01.20)과 이 에셋으로 샷 리스트 `scripts/storyboard/kim-christmas.json`, 장면·오디오 설정, 자막 `subs/kim-christmas.ass`를 만든다. 대사 7장면은 가슴 위 단독 CU(손 없음) 키프레임, 리액션 6컷은 정지 푸시인, 디졸브 10곳.
