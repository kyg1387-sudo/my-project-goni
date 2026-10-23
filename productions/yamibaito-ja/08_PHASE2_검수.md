# 『時給5万円の罠』 PHASE 2 Kill Gate 검수 (2026-10-24)

1차 24장(약 1.1달러) → 합격 16 · 불합격 8(재생성 r2 약 0.4달러). 검수 시트: `PHASE2_검수/인물시트_6장.jpg`·`진행자_6장.jpg`·`장소소품_12장.jpg`·`얼굴확대_420.jpg`.

| 항목 | 판정 | 근거 | 조치 |
|---|---|---|---|
| kenta-work | ✅ 기준 얼굴 | 실사·표정 3칸 정상(우측 눈물 줄기는 사용 금지 칸) | 정면 셀 → `yamibaito-faces/kenta-face.png` |
| kenta-conv | ❌ | 조끼 명찰 패치, 얼굴이 work보다 둥글어 동일인 약함, 눈물 줄기 | 기준 얼굴 refs 재생성 |
| kenta-hoodie | ❌ | 눈물 칸에 **귀걸이(후프)**, 눈물 줄기 | 기준 얼굴 refs 재생성 |
| otoko | ❌ | **하단 표정 행 3칸 애니 화풍**(제19장 5 재발), 가슴 패치 | 정면 셀 refs + 실사 강제 재생성 |
| yuto | ❌ | 눈썹 「끊김」 표식이 **검은 선**으로 그려짐(제19장 5 ② 흉터 교훈과 동일), 작업복 명도가 kenta와 같아 작업실에서 변별 약함 | 표식 삭제·차콜 작업복으로 재생성 |
| tencho-1 / tencho-2 | ✅ tencho-2 채택 | 감독님 사진 대비 머리 볼륨·얼굴형 유사, 안경 전 칸 유지 | 정면 셀 → `tencho-face.png`, tencho-1 미사용 |
| host 6장 | ✅ | 얼굴 동일, 긴 생머리·딥네이비 재킷·골드 체인, 손 정상 | 아웃트로 키프레임 |
| loc-conbini | ❌ | 상품 라벨·벽 포스터 가짜 글자 다수 | 무지 포장·게시물 없음으로 재생성 |
| loc-corridor | ❌ | 게시판 종이 글자, 비상구 표지 픽토그램 | 게시판 제거·무지 녹색 판 |
| loc-payphone | ❌ | 편의점 간판 가짜 가타카나·진열 상품 글자 | 무지 발광 간판·불투명 창 |
| prop-bankbooks | ❌ | 통장 표지 로고·카드 글자 | 무지 표지·무지 카드 |
| loc-factory-ext | ✅ | 굴뚝·쇠창살·철문, 글자 없음(문 옆 작은 종이는 키프레임 흐림) | |
| loc-room / loc-park / loc-stairs / loc-street-van(검은 HiAce, 헤드라이트 OFF) / loc-van-inside(우핸들 확인) / loc-workroom(통장 더미·CCTV) / prop-phones | ✅ | 고증 항목 통과(차 내부 스티커 글자는 키프레임 흐림) | |

규격 반영: 제20장 8(인물 표식은 눈썹 결손도 금지 — 머리·귀·얼굴형만), 제19장 5 재확인(seedream v4라도 「표정 행」은 애니로 빠질 수 있다 → refs + 「EVERY panel REAL PHOTOGRAPH」).

## 2차(r2, 8장 약 0.4달러) — 2026-10-24 → PHASE 2 🔒 Lock

| 항목 | 판정 | 비고 |
|---|---|---|
| kenta-conv-v2 | ✅ | 기준 얼굴과 동일인, 귀걸이 0. 조끼 가슴의 작은 흰 패치는 키프레임에서 「plain vest, no badge」 + 필요 시 인페인트 |
| kenta-hoodie-v2 | ✅ | 동일인, 장신구 0 |
| otoko-v2 | ✅ | 9칸 전부 실사, 동일인 |
| yuto-v2 | ✅ | 차콜 작업복(健太 라이트그레이와 변별), 눈썹 정상. 우하단 눈물 줄기 칸은 사용 금지 |
| loc-conbini-v2 | ✅(조건) | 중앙 선반 무지 상자, 좌측 상품·포스터 잔존 → 키프레임은 카운터 뒤 보케 + `kf_glyph_blur` |
| loc-corridor-v2 | ✅ | 비상구 무지 녹색 판, 좌측 작은 게시판 1개는 흐림 |
| loc-payphone-v2 | ✅(조건) | 간판 무지 발광 ✓, 녹색 공중전화 ✓. 키패드 판·기둥 스티커 작은 글자 → 흐림, 창 너머 상품은 보케 |
| prop-bankbooks-v2 | ✅ | 무지 표지·무지 카드 |

**최종 채택 시트**: kenta-work-1(기준 얼굴)·kenta-conv-v2-1·kenta-hoodie-v2-1·otoko-v2-1·yuto-v2-1·tencho-2 / host 6장 / loc: conbini-v2·room·street-van·van-inside·factory-ext·workroom·corridor-v2·stairs·payphone-v2·park / prop: phones·bankbooks-v2. PHASE 2 지출 약 1.5달러(1차 1.1 + r2 0.4).
