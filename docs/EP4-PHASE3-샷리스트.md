# EP4 「김씨의 크리스마스」 — PHASE 3 정밀 샷 리스트 (일본어 기준판)

규격서 PHASE 3 산출물. `scripts/build_ep4_phase3.py` 자동 생성(손 수정 금지). 총 **05:01.20**, 54컷(대본 53 + S14b), 디졸브 10곳, 자막카드 8장(S07·S42 중복 카드 제거 — 사용자 승인 2026-10-04).

- 데이터: `scripts/storyboard/kim-christmas.json` · 장면 `scripts/scenes/kim-christmas.json` · 오디오 `scripts/audio/kim-christmas.json` · 자막 `subs/kim-christmas.ass`
- 대사 7장면(S09·S11·S26·S28·S30·S47·S50) = 가슴 위 단독 CU 정지 키프레임 → OmniHuman. S30은 S28 키프레임 재사용.
- 리액션 7컷(S02·S10·S19·S23·S27·S29·S45, S02는 S45 재사용) = 정지 푸시인, 립싱크 제외. S18(아이 편지 목소리)은 화면 밖 → 립싱크 제외.
- 일본어 글자 합성 장면(카메라 고정): S03 1801 plate, S07 停電予告, S18 child letter, S22 wife note, S37 1801 plate, S38 1801 plate, S42 お知らせ/完納, S43 管理事務所 plate

| 장면 | 타임코드 | 조립/생성 | 종류 | 샷 | 조명 | 카메라 | 전환 | 대사·카드 | 참조 |
|---|---|---|---|---|---|---|---|---|---|
| S01 | 00:00.00 - 00:06.00 | 6.00/10s | 재사용 | insert | cctv | static | Hard cut |  |  |
| S02 | 00:06.00 - 00:09.00 | 3.50/5s | 리액션(정지 푸시인) | cu | office | push | Dissolve 0.5s |  |  |
| S03 | 00:09.00 - 00:13.12 | 4.50/5s | 자막카드 | long | dawn_dark | static | Hard cut | 【無口なあの人が、なぜ明け方四時の廊下にいたのでしょうか】 | LOC@corridor-18f-night |
| S04 | 00:13.12 - 00:16.12 | 4.00/5s | 자막카드 | xlong | snow_night | static | Dissolve 1.0s | 【キムさんのクリスマス】 | LOC@apt-gate-winter-night |
| S05 | 00:16.12 - 00:24.00 | 7.49/10s | 내레이션 | long | snow_day | static | Hard cut | L1 / 【12月24日】 | LOC@apt-gate-winter-day, LOC@guard-booth-winter-day |
| S06 | 00:24.00 - 00:30.02 | 6.08/10s | 내레이션 | medium | snow_day | push | Hard cut | L2 | LOC@stairwell-day |
| S07 | 00:30.02 - 00:37.01 | 6.99/10s | 내레이션 | insert | corr_day | static | Hard cut | L3 | LOC@corridor-18f-day |
| S08 | 00:37.01 - 00:40.13 | 3.50/5s | 무언 | medium | booth_day | static | Hard cut |  | REN@fullbody-front, LOC@guard-booth-winter-day |
| S09 | 00:40.13 - 00:47.20 | 7.28/10s | 대사(OmniHuman) | cu | booth_day | static | Hard cut | L4 | REN@expr-curious, LOC@guard-booth-winter-day |
| S10 | 00:47.20 - 00:51.08 | 3.50/5s | 리액션(정지 푸시인) | cu | booth_day | push | Hard cut |  | KIMW@expr-neutral, LOC@guard-booth-winter-day |
| S11 | 00:51.08 - 00:58.19 | 7.44/10s | 대사(OmniHuman) | cu | snow_day | static | Hard cut | L5 | MOM@expr-neutral, LOC@guard-booth-winter-day |
| S12 | 00:58.19 - 01:02.21 | 4.10/5s | 내레이션 | insert | snow_day | static | Hard cut | L6 | MOM@fullbody-front, REN@fullbody-front |
| S13 | 01:02.21 - 01:10.20 | 8.74/10s | 내레이션 | medium | booth_day | static | Dissolve 0.8s | L7 | KIMW@side, LOC@guard-booth-winter-day |
| S14 | 01:10.20 - 01:20.20 | 10.00/10s | 내레이션 | medium | apt_night | static | Hard cut | L8, L9 | MOM@side, PROP@kettle, LOC@apt-1801-night |
| S14b | 01:20.20 - 01:23.00 | 3.00/5s | 무언 | insert | apt_night | static | Dissolve 0.8s |  | LOC@apt-1801-night |
| S15 | 01:23.00 - 01:28.22 | 5.90/10s | 내레이션 | long | snow_night | static | Hard cut | L10 / 【その夜】 | LOC@guard-booth-winter-night |
| S16 | 01:28.22 - 01:32.22 | 4.00/5s | 무언 | long | snow_night | static | Hard cut |  | REN@fullbody-front, LOC@guard-booth-winter-night |
| S17 | 01:32.22 - 01:41.03 | 8.20/10s | 내레이션 | medium | booth_night | static | Hard cut | L11 | KIMW@45, LOC@guard-booth-winter-v1-key1 |
| S18 | 01:41.03 - 01:48.18 | 7.65/10s | 편지 목소리 | ecu | booth_night | static | Hard cut | L12 |  |
| S19 | 01:48.18 - 01:52.06 | 3.50/5s | 리액션(정지 푸시인) | cu | booth_night | push | Hard cut |  | KIMW@expr-moved, LOC@guard-booth-winter-v1-key1 |
| S20 | 01:52.06 - 01:57.14 | 5.30/10s | 내레이션 | medium | booth_night | static | Hard cut | L13 | KIMW@front, LOC@guard-booth-winter-v1-key1 |
| S21 | 01:57.14 - 02:04.20 | 7.28/10s | 내레이션 | insert | booth_night | static | Hard cut | L14 | PROP@envelope-notebook |
| S22 | 02:04.20 - 02:14.20 | 10.00/10s | 내레이션 | ecu | booth_night | static | Hard cut | L15, L16 | PROP@envelope-notebook |
| S23 | 02:14.20 - 02:23.05 | 8.85/10s | 리액션(정지 푸시인) | cu | booth_night | push | Dissolve 0.5s | L17 | KIMW@expr-moved, LOC@guard-booth-winter-v1-key1 |
| S24 | 02:23.05 - 02:27.05 | 4.00/5s | 무언 | long | snow_dusk | static | Hard cut |  | KIMW@fullbody-side, GMA@front, CART@side, LOC@apt-gate-winter-day |
| S25 | 02:27.05 - 02:29.17 | 2.50/5s | 무언 | insert | office | static | Hard cut |  | LOC@mgmt-office-counter |
| S26 | 02:29.17 - 02:37.07 | 7.60/10s | 대사(OmniHuman) | cu | office | static | Hard cut | L18 | KIMW@front, LOC@mgmt-office-counter |
| S27 | 02:37.07 - 02:39.19 | 2.50/5s | 리액션(정지 푸시인) | cu | office | push | Hard cut |  | CLERK@expr-surprised, LOC@mgmt-office-counter |
| S28 | 02:39.19 - 02:46.11 | 6.66/10s | 대사(OmniHuman) | cu | office | static | Hard cut | L19 | KIMW@expr-neutral, LOC@mgmt-office-counter |
| S29 | 02:46.11 - 02:48.23 | 2.50/5s | 리액션(정지 푸시인) | cu | office | push | Hard cut |  | CLERK@expr-neutral, LOC@mgmt-office-counter |
| S30 | 02:48.23 - 02:54.07 | 5.85/10s | 대사(OmniHuman) | cu | office | static | Dissolve 0.5s | L20 | S28 keyframe reuse |
| S31 | 02:54.07 - 03:02.11 | 8.14/10s | 내레이션 | insert | booth_day | static | Hard cut | L21 | KIMW@front |
| S32 | 03:02.11 - 03:05.11 | 3.00/5s | 무언 | medium | booth_night | static | Hard cut |  | KIMW@45, PROP@tree, LOC@guard-booth-winter-v1-key1 |
| S33 | 03:05.11 - 03:12.08 | 6.89/10s | 내레이션 | ecu | booth_night | static | Hard cut | L22 | PROP@star |
| S34 | 03:12.08 - 03:18.10 | 7.08/10s | 내레이션 | insert | booth_night | static | Dissolve 1.0s | L23 | PROP@star, PROP@tree |
| S35 | 03:18.10 - 03:21.22 | 3.50/5s | 자막카드 | long | dawn_dark | static | Hard cut | 【午前4時】 | LOC@stairwell-night |
| S36 | 03:21.22 - 03:29.02 | 7.18/10s | 내레이션 | long | dawn_corr | push_fwd | Hard cut | L24 | KIMW@fullbody-back, PROP@tree, LOC@stairwell-key1 |
| S37 | 03:29.02 - 03:39.02 | 10.00/10s | 내레이션 | long | dawn_corr | static | Hard cut | L25, L26 | KIMW@fullbody-back, PROP@tree, LOC@corridor-18f-night |
| S38 | 03:39.02 - 03:42.14 | 3.50/5s | 무언 | insert | dawn_dark | static | Hard cut |  | PROP@tree, LOC@corridor-18f-night |
| S39 | 03:42.14 - 03:48.03 | 6.53/10s | 내레이션 | insert | dawn_dark | static | Dissolve 1.0s | L27 | LOC@corridor-18f-key2 |
| S40 | 03:48.03 - 03:54.09 | 6.24/10s | 내레이션 | xlong | morning | static | Hard cut | L28 / 【クリスマスの朝】 | LOC@apt-gate-winter-key2 |
| S41 | 03:54.09 - 03:58.09 | 4.00/5s | 무언 | medium | morning | static | Hard cut |  | MOM@expr-neutral, REN@expr-happy, PROP@tree, LOC@corridor-18f-day |
| S42 | 03:58.09 - 04:01.21 | 3.50/5s | 자막카드 | insert | morning | static | Hard cut |  | LOC@corridor-18f-day |
| S43 | 04:01.21 - 04:11.21 | 10.00/10s | 내레이션 | medium | office | static | Hard cut | L29, L30 | MOM@fullbody-back2, CLERK@front, LOC@mgmt-office-counter |
| S44 | 04:11.21 - 04:21.21 | 10.00/10s | 내레이션 | insert | cctv | static | Hard cut | L31, L32 | KIMW@fullbody-back, PROP@tree, LOC@corridor-18f-night |
| S45 | 04:21.21 - 04:27.01 | 5.66/10s | 리액션(정지 푸시인) | cu | office | push | Dissolve 0.5s |  | MOM@expr-tearful, LOC@mgmt-office-counter |
| S46 | 04:27.01 - 04:29.13 | 2.50/5s | 무언 | medium | booth_day | static | Hard cut |  | MOM@fullbody-front, LOC@guard-booth-winter-day |
| S47 | 04:29.13 - 04:37.18 | 8.20/10s | 대사(OmniHuman) | cu | booth_day | static | Hard cut | L33 | MOM@expr-tearful, LOC@guard-booth-winter-day |
| S48 | 04:37.18 - 04:40.06 | 2.50/5s | 무언 | medium | booth_day | static | Hard cut |  | MOM@side, LOC@guard-booth-winter-day |
| S49 | 04:40.06 - 04:42.18 | 2.50/5s | 무언 | insert | booth_day | static | Hard cut |  | PROP@kettle, LOC@guard-booth-winter-v1-key2 |
| S50 | 04:42.18 - 04:46.20 | 4.10/10s | 대사(OmniHuman) | cu | booth_day | static | Hard cut | L34 | KIMW@expr-smile, LOC@guard-booth-winter-day |
| S51 | 04:46.20 - 04:48.20 | 3.00/5s | 무언 | insert | booth_day | static | Dissolve 1.0s |  | LOC@guard-booth-winter-v1-key2 |
| S52 | 04:48.20 - 04:56.20 | 8.00/10s | 자막카드 | long | snow_night | pull | Hard cut | 【サンタは煙突からではなく、警備室からやって来る】 | LOC@guard-booth-winter-night |
| S53 | 04:56.20 - 05:01.20 | 5.00/5s | 자막카드 | medium | morning | static | Fade to black → outro | 【次回 ― あの人が、初めて出勤しなかった】 | LOC@guard-booth-winter-day |

## 오디오
- BGM 4구간: 0.0~80.0s 볼륨 0.42 · 81.5~141.0s 볼륨 0.4 · 142.0~235.5s 볼륨 0.38 · 236.5~끝s 볼륨 0.42 (구간 사이 숨 1.0~1.5초, −60dB 2초 무음 금지)
- 현장음(무인 컷만): S03, S04, S05, S06, S07, S15, S18, S22, S35, S38, S39, S40, S42, S49, S53
- 사람 있는 장면·대화 블록은 BGM만(제6장 4).
