# 『閉店間際の弁当屋』 PHASE 2 기준 마스터 에셋 Kill Gate (2026-10-20)

비용: 1차 39장(약 1.25달러) + 2차 17장(약 0.55달러) = **약 1.8달러**(C안 예산 안). 검수 시트 `PHASE2_검수/1~3`.

## 인물 8장 — 2차(seedream v4 1728x2304) 합격, 사용 금지 칸 지정

| 시트 | 판정 | 사용 칸 | 사용 금지 칸 · 후처리 |
|---|---|---|---|
| shuzo1996-v2 | ✅ | 정면·45°·측면·전신 3·중립 | 흉터가 뺨의 붉은 상처로 그려짐 → 키프레임은 **흉터 표식 폐기**(얼굴·각진 턱·짙은 눈썹으로 동일인), 눈물 칸 분홍 눈두덩 사용 금지 |
| shuzo2026-v2 | ✅ | 정면·45°·측면·전신 3·중립·울음 | **하단 가운데(눈물 미소) = 다른 사람(여성화·분홍 화장) 사용 금지**, 이마 붉은 흔적 무시 |
| sumie-v2 | ✅ | 전부 | 눈물 칸 젤 기미 → 눈물은 키프레임에서 제7장 5-1 문장으로 |
| takumi12-v2 | ✅ | 전부 | 눈물 칸 분홍 눈두덩 → 참고만 |
| takumi42-v2 | ✅ | 정면·45°·측면·전신 3·중립·고개 숙임 | **하단 가운데(눈물 미소) = 여성화·립스틱 사용 금지** |
| mio6-v2 | ✅ | 전부 | |
| hina8-v2 | ✅ | 전부 | 코트 소매 작은 로고 → 키프레임 Kill Gate에서 확인 |
| mio36-v2 | ✅ | 전부 | |

## 장소 22장

| 판 | 판정 |
|---|---|
| shop96-wide·ots·reverse·high·low·curtain·showcase, shop26-wide·ots·reverse·sticker, street-front, hospital, shokudo-wide·counter (1차) | ✅ |
| shop96-outside·street-shutter·street-rain·kitchen-wide (2차) | ✅ |
| street-apartment·kitchen-nail·mailbox (2차 + `kf_glyph_inpaint.py` 가짜 글자 제거·배경 흐림 → `*-v2-clean.png`) | ✅ |

## 소품 9장

| 판 | 판정 |
|---|---|
| noribento·karaage·sticker·letter·towel·frame·bag (1차), origami(2차, こまどり) | ✅ |
| coins(2차) | ⚠️ 2회 연속 4개 + 동전 무늬 가짜 글자 → **참고용만**. 동전 ECU는 키프레임에서 「얕은 심도, 둥근 구멍 동전 5개, 무늬 흐림」으로 만들고 개수는 Kill Gate에서 센다 |

## 주의(키프레임 생성기에 넣을 고정 문장)

- 인물 참조는 **정면 셀 크롭**만(사용 금지 칸 제외). 「tearful smile」 표현은 여성화·분홍 화장을 부르므로 쓰지 않고 「wet eyes, small closed-mouth smile」로.
- 修三 흉터 문구 삭제, 拓海 동일인 = 큰 쌍꺼풀 눈 + 약간 튀어나온 귀 + 가는 일자 눈썹.
- 가게 1996 정본 = shop96-wide(쇼케이스 왼쪽·계산대 오른쪽·주방 커튼 뒤·유리문 오른쪽 철길). 다른 구도 키프레임은 이 배치를 LOCATION LOCKED 문장으로 고정.
