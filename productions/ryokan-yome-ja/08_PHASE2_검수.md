# #03 『老舗旅館の嫁』 PHASE 2 마스터 에셋 검수 (Kill Gate)

작성 2026-10-19. 기준: 제2장 1(글자·기호 0%), 제11장 1·2·18, 제12장 교훈 4~7. 시트 파일 `assets/portraits/ryokan-cast/`.

## 1. 인물 시트 (고니감독님 승인 2026-10-18)
| 시트 | 판정 | 사용 셀 | 비고 |
|---|---|---|---|
| wakana-fix-1 | ✅ 기준 | 정면(하단 좌)·45도 없음(전신 측면으로 대체) | 점 2개 — 식별자 문장은 「small beauty marks below the left eye」. 의상 A(사무에+앞치마) |
| wakana-b | ⏳ 3차 | — | 1·2차: 참조 시트의 의상(앞치마)을 그대로 따라감 → 3차는 얼굴 크롭만 참조(`cells/wakana-front.png`) |
| tomiko-fix-1 | ✅ 기준 | 상단 3셀(정면·45도·측면, 안경), 하단 좌(미소) | 엄격·애원 셀은 안경 누락 → 정면 셀 + 표정 문장(제11장 1) |
| mai-sheet-1 | ✅ | 상단 좌(정면)·전신 3·하단 3 | 비웃음 셀이 웃음으로 생성 → 정면 + 「sneer」 문장 |
| takayuki-sheet-1 | ✅ | 전신 정면·측면, 하단 3 | 45도 셀 없음(전신 측면으로 대체) |
| sakurai-sheet-1 | ✅ | 상단 3, 하단 3 | 기모노 밑단 소형 문양 → 키프레임 문장 「plain, no pattern」 |

## 2. 로케이션·앵글·소품 시트
| 시트 | 판정 | 사용 셀 | 불합격 사유·대응 |
|---|---|---|---|
| loc-tsukimiso-genkan | ✅ 부분 | DAY-WIDE / CORRIDOR END / COUNTER CLOSE | NIGHT 셀 카운터 위 글자 종이 → 미사용(야간 현관 컷 없음) |
| loc-tsukimiso-zashiki | ✅ | 4셀 전부 | 족자 무지 ✅ |
| loc-tsukimiso-kitchen (2차) | ✅ 부분 | KITCHEN-DAWN / CUTTING BOARD / OFFICE-NIGHT | 1차 벽보 글자·격자 붕괴 → 2차 합격 3셀(흰 상자 선반 셀 미사용) |
| loc-couple-room (2차) | ⚠ 부분 | WINDOW / LAMP CLOSE | 벽보·노렌 가문·바닥 휴대폰 반복 → 어두운 장면이라 2셀로 충분, 키프레임은 「bare walls」 선행 |
| loc-hanaikada-genkan (2차) | ✅ | DAY-WIDE / LOBBY SOFAS / BUS BAY / FRONT DESK | 프런트 셀 벽 소형 종이 1장(보케로 처리) |
| loc-hanaikada-office (2차) | ❌ 3차 | — | 2차가 **일러스트풍** + 노렌 가문 + 벽보 → 실사 선언문 선두·노렌 금지로 3차 |
| loc-taipei-office | ✅ 부분 | DESK FROM BEHIND / PHONE CLOSE / WINDOW | WIDE 셀에 노렌·벽보 → 미사용 |
| loc-back-alley | ✅ 부분 | NIGHT-WIDE / GATE / TAXI END | HIGH ANGLE 셀에 노렌 → 미사용(부감은 글로만, 제11장 3) |
| angle-tsukimiso-genkan (2차) | ✅ 부분 | REVERSE / THROUGH DOORWAY | HIGH(노렌 가문)·LOW(벽보) 미사용 |
| angle-hanaikada-office (2차) | ✅ 부분 | REVERSE / HIGH ANGLE / LOW ANGLE | THROUGH DOORWAY 셀 노렌 가문 → 미사용 |
| props-sheet | ✅ | 4셀 전부 | 파일 펼침 = 회색 줄 + 빨간 띠(글자 없음) ✅ |

## 3. 교훈 (제12장·03실증에 저장)
- 생성 모델은 「noren」 단어만 있으면 **원형 가문(家紋)**을 그린다(5/7 시트). 노렌이 필요한 현관 외에는 프롬프트에 「NO noren, NO hanging curtain」을 선두에, 현관은 「plain solid indigo, NO circular crest」를 선두에 둔다. 키프레임에서도 동일.
- 일본 실내 시트는 **벽보(종이 공지)**를 기본으로 그린다 → WALL RULE(「every wall is completely bare」) 선두 문장 필수. 그래도 남으면 셀 단위로 버리고 합격 셀만 쓴다(장소 시트는 4셀 중 2~3셀이면 충분).
- refs 참조 시트에 의상이 있으면 **의상까지 복제**된다(wakana-b 2회 실증) → 의상이 다른 변형 시트는 얼굴만 크롭한 셀을 refs로 쓴다.
- 장소 시트도 실사 선언문(REAL PHOTOGRAPH ONLY) 없이는 일러스트풍이 나올 수 있다(hanaikada-office 2차).
