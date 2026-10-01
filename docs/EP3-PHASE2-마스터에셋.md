# EP3 「김씨와 폐지 할머니」 — PHASE 2 기준 마스터 에셋 고정

규격서 PHASE 2 산출물. 작성 2026-10-01. 상태: **PASS — 사용자 승인 2026-10-01 ("PHASE 2 PASS"), PHASE 2 Lock**

## 2-0. 사용자 확정 사항
- **김씨 얼굴 = 기존 AI 배우 유지** (EP1·EP2와 동일 인물, `assets/portraits/guard-kim-secret-cap2/kim-gold-1.png` 참조). 2026-10-01 사용자 결정("그대로 유지하는것이 좋지않으까?").
  → 인수인계 문서 `docs/EP3-캐릭터시트.md`의 "감독 본인 얼굴 카메오" 안은 **폐기**. 감독 사진 4장(`assets/portraits/kim-reference-*.jpg`)은 사용하지 않는다.
- 공통 스타일 프리셋(모든 프롬프트 공통 주입, 잠금):
  `Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, soft natural key light from upper-left, subtle warm rim light, no flat lighting`
  + 공통 네거티브: `gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers`

## 2-1. 캐릭터 마스터 시트 (Character Anchor) — Kill Gate 판정
시트 규격: 3x3 그리드(상단 정면·45도·측면 / 중단 전신 앞·뒤·옆 / 하단 3표정), 무텍스트.

| 인물 | 파일 | 생성 경로 | 검수 항목 | 판정 |
|---|---|---|---|---|
| 김씨 | `assets/portraits/ep3-cast/kim-sheet-1.png` | nano-banana/edit (ref: kim-gold-1.png) | 9패널 완비, 기존 배우 얼굴 일치, 명찰·모자·문자 없음, 손가락 정상 | **합격** |
| 폐지 할머니 | `assets/portraits/ep3-cast/grandma-sheet-1.png` | seedream v3 T2I | 9패널 완비, 두건·남색 누비점퍼·몸뻬 의상 고정, 3표정(중립·미소·근심), 문자 없음 | **합격** (경미: 45도 패널이 측면에 가까움 — 컷 생성 시 정면 패널 우선 참조) |
| 최사장 | `assets/portraits/ep3-choi/choi-sheet-1.png` | seedream v3 T2I | v1: 45도·측면·3표정 누락 → 보류. v2: 패널 간 머리 불일치(백발↔민머리) → 보류. v3: 머리 고정 프롬프트로 재생성 → 9패널 완비, 짧은 반백 머리·회색 조끼·무전기 전 패널 고정, 문자 없음 | **합격** (경미: 찌푸림 패널에 수염 기미 — 컷 생성 시 정면·중립 패널 우선 참조) |

보류본은 `_rejected/`에 보관(`ep3-cast/_rejected/grandma-sheet-v1.png`, `ep3-choi/_rejected/choi-sheet-v1.png`, `choi-sheet-v2.png`).
`assets/portraits/ep3-kim-test/`(배우/감독 비교용 2장)는 결정 완료 후 참고용으로만 보관.

### 캐릭터 프롬프트 잠금 (복장·헤어)
- 김씨: 기존 배우 얼굴 + `plain dark navy security guard uniform, pristine clean collar, no badge, no name tag, no cap`
- 할머니: `faded brown floral headscarf over mostly grey hair, thick plain navy quilted jacket, worn dark brown baggy work trousers (monpe), worn brown work gloves`
- 최사장: `short cropped salt-and-pepper grey hair, slightly receding hairline, no hat, grease-stained plain grey work vest over plain dark shirt, black work gloves, dark work trousers, worn radio on belt`

## 2-2. 로케이션 마스터 시트 (Location Anchor) — 판정
각 장소 2x2 시트(DAY / NIGHT / KEY1 / KEY2), 인물 배제, 35mm 표준 화각, 광원 upper-left, 주간 5600K / 야간 3200K. 셀 분리본 20장은 `assets/portraits/ep3-cast/cells/`.

| 장소 | 시트 | 셀 | 문자·간판 | 판정 |
|---|---|---|---|---|
| 경비실 | `loc-guard-booth-1.png` | day / night / key1 / key2 | 없음 | 합격 |
| 아파트 정문 | `loc-apt-gate-1.png` | day / night / key1 / key2 | 없음 | 합격 |
| 철거 현장 | `loc-demolition-1.png` | day / night / key1 / key2 | 없음 | 합격 |
| 밤 골목 | `loc-alley-night-1.png` | day / night / key1 / key2 | 없음 | 합격 |
| 고물상 | `loc-junkyard-1.png` | day / night / key1 / key2 | 없음 | 합격 |

## 2-3. PHASE 3에서의 참조 호출 규칙
- 모든 키프레임은 `캐릭터 시트 셀 + 로케이션 셀`을 멀티 레퍼런스로 결합해 생성(Image-to-Image). 텍스트만으로 인물 생성 금지.
- 시트 참조 ID 표기: `KIM@kim-sheet-1`, `GMA@grandma-sheet-1`, `CHOI@choi-sheet-1`, `LOC@<place>-<day|night|key1|key2>`.

## 2-4. 목소리 확정 (2026-10-01)
- 최사장 = Typecast 명주 `tc_656059fc4db338e38f77d0bc`, 할머니 = Typecast `tc_60ad0841061ee28740ec2e1c`, 김씨·내레이터 = ElevenLabs(시리즈 대장). 채택 클립과 재확정 타임라인은 `docs/EP3-PHASE1-대본동결-오디오앵커.md` 1-3 참조.
