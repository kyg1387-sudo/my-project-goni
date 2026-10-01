# EP3 「김씨와 폐지 할머니」 — PHASE 3 정밀 샷 리스트 & 프롬프트 설계 (Storyboard Lock)

규격서 PHASE 3 산출물. 작성 2026-10-01. 상태: **Storyboard Lock — 사용자 PASS 2026-10-01** (이후 변경은 사용자 재승인 필요)

원본 데이터: `scripts/storyboard/kim-cart-grandma.json` (이 문서는 `scripts/build_phase3_doc.py`로 생성). 타임코드는 PHASE 1 Lock 타임라인(24fps)과 PHASE 2 Lock 에셋을 그대로 참조한다.

## 3-0. 공통 규칙 (모든 컷에 동일 주입)

- 스타일 프리셋: `Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones`
- 네거티브: `gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag`
- 참조 호출: `KIM@<셀>` = 김씨 시트, `GMA@<셀>` = 할머니 시트, `CHOI@<셀>` = 최사장 시트, `LOC@<장소>-<day|night|key1|key2>` = 로케이션 셀. 셀 이름: front/45/side(상단), fullbody-front/back/side(중단), front-neutral/smile/tense·wary(하단), hands(중단 전신에서 손 크롭).
- 카메라 무빙은 규격 승인 목록만 사용: Static / Slow cinematic push-in(1.05~1.08) / Subtle handheld sway / Very slow lateral drift(보행 속도 동기). 인수인계본의 Dolly zoom(S15)·Side tracking·Follow shot은 위 승인 동작으로 치환했다.
- 컷 길이: fal Seedance 제약으로 5/10초 단위 생성 후, 편집에서 3~5초 시각적 환기 규칙(제4장)에 맞춰 분할·인서트한다.
- 말하는 씬 4초 초과(S02, S28, S30)는 **Talking face → B-roll → 리액션** 치팅을 필수 적용(아래 Edit Strategy).
- 헤드 턴 15~20° 이내, 표정은 키프레임에 50% 선반영, 비디오 단계에서는 미세 모션만 지시.

## 3-1. 샷 리스트 (규격 표)

| Scene | 타임코드 & 듀레이션 | 오디오 파형 & 대사 | 샷 사이즈 & 렌즈 | 조명 설계 | 카메라 무빙 | 전환(Out) | 참조 에셋 |
|---|---|---|---|---|---|---|---|
| S01 | 00:00.00 ~ 00:10.00 (10s) | line001 김씨 Attack 00:02.00–00:04.09 (대사: 이 손잡이, 가죽끈 감긴 거 보이…)<br>line002 김씨 Attack 00:06.12–00:10.17 (대사: 이거 임자 되시는 분이 직접 감으…) | Medium close-up (two-shot) / 50mm lens | Overcast daylight 5600K from upper-left | Slow cinematic push-in (zoom 1.05) | Hard cut | KIM@front-neutral, CHOI@front-wary, LOC@junkyard-day |
| S02 | 00:10.00 ~ 00:20.00 (10s) | line002 김씨 Attack 00:06.12–00:10.17 (대사: 이거 임자 되시는 분이 직접 감으…) | Medium close-up (two-shot, Choi weighted) / 50mm lens | Overcast daylight 5600K from upper-left | Static, locked off | Hard cut (cold open → caption) | KIM@45-neutral, CHOI@front-wary, LOC@junkyard-day |
| S03 | 00:20.00 ~ 00:25.00 (5s) | 자막카드 Attack 00:20.22–00:24.22 (자막: 말이 없던 그가, 왜 고물상 앞을…) | Extreme close-up / 85mm prime lens | Overcast daylight 5600K from upper-left | Static, locked off | Dissolve 0.5s | LOC@junkyard-key1 |
| S04 | 00:25.00 ~ 00:30.00 (5s) | 자막카드 Attack 00:25.22–00:28.04 (자막: 김씨와 폐지 할머니) | Long shot / 35mm lens | Blue-hour dusk | Static, locked off | Hard cut | LOC@apt-gate-night |
| S05 | 00:30.00 ~ 00:35.00 (5s) | 자막카드 Attack 00:30.22–00:33.02 (자막: 사흘 전) | Long shot / 35mm lens | Late-afternoon golden hour | Static, locked off | Dissolve 0.5s (time rewind) | LOC@apt-gate-day |
| S06 | 00:35.00 ~ 00:45.00 (10s) | line003 내레이터 Attack 00:36.12–00:41.14 (내레: 이 골목의 리어카는, 유독 손잡이…)<br>line004 내레이터 Attack 00:41.21–00:48.13 (내레: 그 리어카는 이십 년 전, 할머니…) | Long shot / 35mm lens | Late-afternoon golden hour | Very slow lateral drift (follows subject at walking pace) | J-Cut 0.5s (cart creak leads) | GMA@fullbody-front, LOC@apt-gate-day |
| S07 | 00:45.00 ~ 00:55.00 (10s) | line004 내레이터 Attack 00:41.21–00:48.13 (내레: 그 리어카는 이십 년 전, 할머니…)<br>line005 내레이터 Attack 00:48.21–00:57.20 (내레: 손잡이에 감긴 가죽끈도, 삐걱이는…) | Medium shot / 50mm lens | Late-afternoon golden hour | Static, locked off | J-Cut 0.5s | GMA@45-neutral, LOC@apt-gate-day |
| S08 | 00:55.00 ~ 01:00.00 (5s) | line005 내레이터 Attack 00:48.21–00:57.20 (내레: 손잡이에 감긴 가죽끈도, 삐걱이는…)<br>line006 내레이터 Attack 00:58.03–01:03.23 (내레: 할머니에게 이 리어카는, 벌이가 …) | Close-up / 85mm prime lens | Late-afternoon golden hour | Static, locked off | Match cut (strap → hands on strap) | LOC@apt-gate-key1 |
| S09 | 01:00.00 ~ 01:05.00 (5s) | line006 내레이터 Attack 00:58.03–01:03.23 (내레: 할머니에게 이 리어카는, 벌이가 …)<br>line007 내레이터 Attack 01:04.06–01:13.00 (내레: 다른 건 아무리 험하게 다뤄도, …) | Close-up (hands) / 85mm prime lens | Late-afternoon golden hour | Slow cinematic push-in (zoom 1.05) | J-Cut 0.5s | GMA@hands, LOC@apt-gate-day |
| S10 | 01:05.00 ~ 01:10.00 (5s) | line007 내레이터 Attack 01:04.06–01:13.00 (내레: 다른 건 아무리 험하게 다뤄도, …) | Medium close-up / 50mm lens | Late-afternoon golden hour | Static, locked off | J-Cut 0.5s | KIM@front-neutral, LOC@guard-booth-day |
| S11 | 01:10.00 ~ 01:15.00 (5s) | line007 내레이터 Attack 01:04.06–01:13.00 (내레: 다른 건 아무리 험하게 다뤄도, …)<br>line008 내레이터 Attack 01:13.07–01:19.22 (내레: 경비 김씨는 매일 아침, 재활용 …) | Full shot (rear) / 35mm lens | Soft morning daylight through the booth window from upper-left | Static rear shot | J-Cut 0.5s (birds lead) | KIM@fullbody-back, LOC@guard-booth-day |
| S12 | 01:15.00 ~ 01:20.00 (5s) | line008 내레이터 Attack 01:13.07–01:19.22 (내레: 경비 김씨는 매일 아침, 재활용 …) | Long shot / 35mm lens | Soft natural daylight from upper-left | Static, locked off | Dissolve 0.5s | GMA@fullbody-side, LOC@apt-gate-day |
| S13 | 01:20.00 ~ 01:25.00 (5s) | line009 내레이터 Attack 01:20.05–01:22.19 (내레: 말 한마디 없이, 그저 그렇게.)<br>line010 내레이터 Attack 01:23.02–01:27.22 (내레: 그날 오후, 철거 트럭이 골목의 …) | Long shot / 24mm wide angle | Late-afternoon golden hour | Static, locked off | J-Cut 0.5s (truck idle leads) | GMA@fullbody-front, LOC@demolition-day |
| S14 | 01:25.00 ~ 01:30.00 (5s) | line010 내레이터 Attack 01:23.02–01:27.22 (내레: 그날 오후, 철거 트럭이 골목의 …)<br>line011 내레이터 Attack 01:28.10–01:31.10 (내레: 리어카도 함께, 고철더미인 줄 알…) | Long shot / 24mm wide angle | Late-afternoon golden hour | Slow cinematic push-in toward the truck (zoom 1.05) | Hard cut | LOC@demolition-key1 |
| S15 | 01:30.00 ~ 01:40.00 (10s) | line011 내레이터 Attack 01:28.10–01:31.10 (내레: 리어카도 함께, 고철더미인 줄 알…)<br>line012 할머니 Attack 01:31.17–01:32.20 (대사: …내 리어카…)<br>line013 내레이터 Attack 01:33.12–01:38.12 (내레: 말은 짧았지만, 그 말 안에 이십…)<br>line014 내레이터 Attack 01:38.19–01:45.15 (내레: 할머니는 그날 밤, 늦도록 혼자 …) | Medium close-up / 85mm prime lens | Late-afternoon golden hour | Slow cinematic push-in (zoom 1.08) — replaces dolly-zoom | Hold 0.8s → Dissolve 0.5s | GMA@front-tense, LOC@demolition-day |
| S16 | 01:40.00 ~ 01:45.00 (5s) | line014 내레이터 Attack 01:38.19–01:45.15 (내레: 할머니는 그날 밤, 늦도록 혼자 …) | Full shot, high angle / 35mm lens | Late-afternoon golden hour | Static, locked off | Dissolve 0.5s | GMA@fullbody-front, LOC@demolition-key2 |
| S17 | 01:45.00 ~ 01:55.00 (10s) | line014 내레이터 Attack 01:38.19–01:45.15 (내레: 할머니는 그날 밤, 늦도록 혼자 …)<br>line015 내레이터 Attack 01:45.23–01:50.15 (내레: 아무도, 리어카가 어디로 갔는지 …) | Long shot / 35mm lens | Low-key night | Subtle handheld sway | Dissolve 0.5s | GMA@fullbody-side, LOC@demolition-night |
| S18 | 01:55.00 ~ 02:05.00 (10s) | line016 내레이터 Attack 01:56.12–02:00.17 (내레: 그에게도, 아무도 모르는 이유가 …)<br>line017 내레이터 Attack 02:01.00–02:06.08 (내레: 그래서 그는, 아무도 시키지 않은…) | Medium close-up / 85mm prime lens | Low-key booth interior at night | Static, locked off | J-Cut 0.5s (clock tick leads) | KIM@front-neutral, LOC@guard-booth-night |
| S19 | 02:05.00 ~ 02:10.00 (5s) | line017 내레이터 Attack 02:01.00–02:06.08 (내레: 그래서 그는, 아무도 시키지 않은…)<br>line018 내레이터 Attack 02:06.15–02:12.01 (내레: 첫째 날 밤, 샅샅이 뒤진 골목엔…) | Full shot (rear follow) / 35mm lens | Low-key booth interior at night | Very slow push forward behind Kim | Dissolve 0.4s (night ambience bridge) | KIM@fullbody-back, LOC@guard-booth-night |
| S20 | 02:10.00 ~ 02:20.00 (10s) | line018 내레이터 Attack 02:06.15–02:12.01 (내레: 첫째 날 밤, 샅샅이 뒤진 골목엔…)<br>line019 내레이터 Attack 02:12.08–02:21.02 (내레: 비가 쏟아지던 둘째 날 밤, 우산…) | Long shot / 35mm lens | Low-key night | Very slow lateral drift | Dissolve 0.5s | KIM@fullbody-side, LOC@alley-night-night |
| S21 | 02:20.00 ~ 02:30.00 (10s) | line019 내레이터 Attack 02:12.08–02:21.02 (내레: 비가 쏟아지던 둘째 날 밤, 우산…)<br>line020 내레이터 Attack 02:21.10–02:28.13 (내레: 쉬어가던 밤, 그는 아내의 꽃무늬…)<br>line021 내레이터 Attack 02:28.21–02:37.01 (내레: 거기엔 이렇게 적혀 있었습니다 —…) | Full shot, high angle / 35mm lens | Night rain | Subtle handheld sway | Dissolve 0.5s | KIM@fullbody-front, LOC@alley-night-key1 |
| S22 | 02:30.00 ~ 02:40.00 (10s) | line021 내레이터 Attack 02:28.21–02:37.01 (내레: 거기엔 이렇게 적혀 있었습니다 —…)<br>line022 내레이터 Attack 02:37.09–02:47.00 (내레: 십 년 전, 아무도 그에게 말을 …) | Medium close-up / 85mm prime lens | Low-key booth interior at night | Slow cinematic push-in (zoom 1.05) | Match cut (hands → notebook) | KIM@front-neutral, LOC@guard-booth-night |
| S23 | 02:40.00 ~ 02:45.00 (5s) | line022 내레이터 Attack 02:37.09–02:47.00 (내레: 십 년 전, 아무도 그에게 말을 …) | Extreme close-up / 85mm prime lens | Low-key booth interior at night | Static, rack focus edge → writing | J-Cut 0.5s | LOC@guard-booth-key1 |
| S24 | 02:45.00 ~ 02:55.00 (10s) | line022 내레이터 Attack 02:37.09–02:47.00 (내레: 십 년 전, 아무도 그에게 말을 …)<br>line023 내레이터 Attack 02:47.07–02:51.20 (내레: 김씨는 그날을, 십 년이 지나도록…)<br>line024 내레이터 Attack 02:52.03–02:56.21 (내레: 다리가 저려올 때쯤에야, 셋째 날…) | Medium close-up / 85mm prime lens | Low-key booth interior at night | Static, locked off | Sepia dissolve 0.5s → flashback | KIM@front-neutral, LOC@guard-booth-night |
| S25 | 02:55.00 ~ 03:05.00 (10s) | line024 내레이터 Attack 02:52.03–02:56.21 (내레: 다리가 저려올 때쯤에야, 셋째 날…)<br>line025 내레이터 Attack 02:57.04–03:02.00 (내레: 철거 업체가 고철을 넘긴 곳 — …) | Close-up (feet/legs) / 85mm prime lens | Low-key night | Static, locked off | Dissolve 0.4s | KIM@fullbody-side, LOC@alley-night-night |
| S26 | 03:05.00 ~ 03:15.00 (10s) | line026 내레이터 Attack 03:06.12–03:11.12 (내레: 김씨는 그길로, 소문난 고물상들을…)<br>line027 내레이터 Attack 03:12.00–03:17.13 (내레: 세 번째 집, 마당 안쪽에 낯익은…) | Full shot / 35mm lens | Soft natural daylight from upper-left | Very slow lateral drift | J-Cut 0.5s (daytime street leads) | KIM@fullbody-front, LOC@junkyard-day |
| S27 | 03:15.00 ~ 03:20.00 (5s) | line027 내레이터 Attack 03:12.00–03:17.13 (내레: 세 번째 집, 마당 안쪽에 낯익은…) | Medium close-up / 85mm prime lens | Overcast daylight 5600K from upper-left | Slow cinematic push-in (zoom 1.06) | Hard cut | KIM@45-neutral, LOC@junkyard-key1 |
| S28 | 03:20.00 ~ 03:30.00 (10s) | line028 최사장 Attack 03:22.00–03:26.05 (대사: 이미 계근까지 끝난 물건입니다. …)<br>line029 내레이터 Attack 03:26.17–03:28.20 (내레: 김씨는, 물러서지 않았습니다.) | Medium close-up (two-shot, Choi speaking) / 50mm lens | Overcast daylight 5600K from upper-left | Static, locked off | Hard cut | CHOI@front-neutral, KIM@45-neutral, LOC@junkyard-day |
| S29 | 03:30.00 ~ 03:40.00 (10s) | line030 김씨 Attack 03:31.18–03:34.03 (대사: 이 손잡이, 가죽끈 감긴 거 보이…)<br>line031 김씨 Attack 03:36.06–03:40.11 (대사: 이거 임자 되시는 분이 직접 감으…) | Medium close-up / 85mm prime lens | Overcast daylight 5600K from upper-left | Slow cinematic push-in (zoom 1.05) | Match cut (hand on strap) | KIM@front-neutral, LOC@junkyard-day |
| S30 | 03:40.00 ~ 03:50.00 (10s) | line031 김씨 Attack 03:36.06–03:40.11 (대사: 이거 임자 되시는 분이 직접 감으…)<br>line032 내레이터 Attack 03:41.19–03:46.00 (내레: 최사장은 잠시, 자신의 어머니를 …)<br>line033 내레이터 Attack 03:46.12–03:51.18 (내레: 돌아가시기 전까지, 낡은 유모차를…) | Close-up (Choi reaction) / 85mm prime lens | Overcast daylight 5600K from upper-left | Slow cinematic push-in (zoom 1.05) | Hold 1s → Dissolve 0.5s | CHOI@front-neutral, LOC@junkyard-day |
| S31 | 03:50.00 ~ 04:00.00 (10s) | line033 내레이터 Attack 03:46.12–03:51.18 (내레: 돌아가시기 전까지, 낡은 유모차를…)<br>line034 최사장 Attack 03:55.08–03:57.13 (대사: …가져가십쇼. 값은 됐습니다.) | Medium close-up / 85mm prime lens | Overcast daylight 5600K from upper-left | Static, locked off | Hold 1s → Dissolve 0.5s → dawn | CHOI@front-smile, KIM@45-neutral, LOC@junkyard-day |
| S32 | 04:00.00 ~ 04:05.00 (5s) | line035 내레이터 Attack 04:01.12–04:06.22 (내레: 그는 밤늦도록, 자신의 몫으로 새…) | Medium close-up / 50mm lens | Low-key booth interior at night | Static, locked off | J-Cut 0.5s (metal clink leads) | KIM@45-neutral, LOC@guard-booth-night |
| S33 | 04:05.00 ~ 04:10.00 (5s) | line035 내레이터 Attack 04:01.12–04:06.22 (내레: 그는 밤늦도록, 자신의 몫으로 새…)<br>line036 내레이터 Attack 04:07.10–04:13.18 (내레: 거친 쇠손잡이에 시릴 손을 위해,…) | Close-up (hands) / 85mm prime lens | Low-key booth interior at night | Static, locked off | Dissolve 0.4s | KIM@hands, LOC@guard-booth-night |
| S34 | 04:10.00 ~ 04:20.00 (10s) | line036 내레이터 Attack 04:07.10–04:13.18 (내레: 거친 쇠손잡이에 시릴 손을 위해,…)<br>line037 내레이터 Attack 04:14.06–04:19.20 (내레: 그날 새벽, 아무도 없는 골목에 …) | Long shot (rear follow) / 35mm lens | Pre-dawn blue hour | Very slow push forward behind Kim | Hard cut → caption | KIM@fullbody-back, LOC@alley-night-key2 |
| S35 | 04:20.00 ~ 04:25.00 (5s) | 자막카드 Attack 04:20.22–04:23.02 (자막: 다음날 아침) | Long shot / 35mm lens | Pre-dawn blue hour | Static, locked off | Hard cut | LOC@demolition-key2 |
| S36 | 04:25.00 ~ 04:30.00 (5s) | line038 할머니 Attack 04:28.00–04:29.19 (대사: …영감이 감아준 건데…) | Medium shot / 50mm lens | Soft natural daylight from upper-left | Static, locked off | Dissolve 0.4s | GMA@front-tense, LOC@demolition-day |
| S37 | 04:30.00 ~ 04:40.00 (10s) | line039 내레이터 Attack 04:31.05–04:38.12 (내레: 말 한마디 건네지 않았지만, 두 …)<br>line040 내레이터 Attack 04:39.00–04:44.10 (내레: 빚을 갚는 데, 꼬박 십 년이 걸…) | Close-up (hands) / 85mm prime lens | Soft natural daylight from upper-left | Slow cinematic push-in (zoom 1.05) | Dissolve 0.4s | GMA@hands, LOC@demolition-day |
| S38 | 04:40.00 ~ 04:45.00 (5s) | line040 내레이터 Attack 04:39.00–04:44.10 (내레: 빚을 갚는 데, 꼬박 십 년이 걸…)<br>line041 내레이터 Attack 04:44.22–04:50.17 (내레: 고마움은 몰라도 된다고, 그는 그…) | Choker close-up / 85mm prime lens | Soft natural daylight from upper-left | Static, locked off | Sepia dissolve 0.5s → flashback | GMA@front-smile, LOC@demolition-day |
| S39 | 04:45.00 ~ 04:50.00 (5s) | line041 내레이터 Attack 04:44.22–04:50.17 (내레: 고마움은 몰라도 된다고, 그는 그…) | Medium shot (two-shot) / 50mm lens | Memory flashback: desaturated sepia grade | Static, locked off | Sepia dissolve 0.5s → present | GMA@fullbody-front, KIM@fullbody-front, LOC@alley-night-key1 |
| S40 | 04:50.00 ~ 04:55.00 (5s) | line041 내레이터 Attack 04:44.22–04:50.17 (내레: 고마움은 몰라도 된다고, 그는 그…)<br>line042 내레이터 Attack 04:51.05–04:56.01 (내레: 그날 이후, 할머니의 리어카는 다…) | Close-up / 85mm prime lens | Soft morning daylight through the booth window from upper-left | Static, locked off | Hard cut (bookend impact) | LOC@guard-booth-day |
| S41 | 04:55.00 ~ 05:00.00 (5s) | line042 내레이터 Attack 04:51.05–04:56.01 (내레: 그날 이후, 할머니의 리어카는 다…) | Medium close-up / 85mm prime lens | Soft morning daylight through the booth window from upper-left | Static, locked off | J-Cut 0.5s | KIM@front-smile, LOC@guard-booth-day |
| S42 | 05:00.00 ~ 05:05.00 (5s) | 무음 (앰비언스만) | Long shot / 35mm lens | Soft natural daylight from upper-left | Very slow lateral drift | Dissolve 0.5s | GMA@fullbody-side, LOC@apt-gate-day |
| S43 | 05:05.00 ~ 05:15.00 (10s) | 자막카드 Attack 05:05.22–05:10.16 (자막: 고마움은 몰라도 된다. 그 사람은…) | Long shot (rear) / 35mm lens | Blue-hour dusk | Static rear shot | Dissolve 0.5s → ending card | KIM@fullbody-back, LOC@guard-booth-night |
| S44 | 05:15.00 ~ 05:25.00 (10s) | 자막카드 Attack 05:15.22–05:20.13 (자막: 다음 이야기 — 성탄 전야, 그가…) | Medium shot / 35mm lens | Soft morning daylight through the booth window from upper-left | Static, locked off | Fade out | LOC@guard-booth-key2 |

## 3-2. 씬별 키프레임 & 모션 프롬프트 (제5장 템플릿)

### S01 (10s) — Medium close-up (two-shot)

```
[SCENE SPECIFICATION]
- Scene ID: S01
- Timecode: 00:00.00 - 00:10.00 (Duration: 10s)
- Audio Anchor: line001 김씨 Attack 00:02.00–00:04.09 (대사: 이 손잡이, 가죽끈 감긴 거 보이…) / line002 김씨 Attack 00:06.12–00:10.17 (대사: 이거 임자 되시는 분이 직접 감으…)
- Transition Out: Hard cut
- References: KIM@front-neutral, CHOI@front-wary, LOC@junkyard-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt standing firmly in front of Korean man in his 50s (reference: CHOI sheet), stocky build, short cropped salt-and-pepper hair, grease-stained plain grey work vest over plain dark shirt, black work gloves, worn radio on belt, blocking him; beside them the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle. Kim faces camera three-quarter, mouth slightly open mid-sentence.
(Expression, pre-baked 50%): Kim: firm, jaw set (tension 50%). Choi: wary frown.
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering
(Cinematography): 50mm lens, f/2.8, medium shot, natural perspective, soft background separation; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Overcast daylight 5600K from upper-left, bare bulbs as warm 3200K practicals, dramatic high-contrast shadows between paper bales, warm rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in (zoom 1.05)
- Character Motion: Micro chest breathing, single slow blink, lips move with the dialogue, max 5-degree head tilt. Choi perfectly still.
- Edit Strategy: 00:02.00~00:04.09 Talking face (line 1) → 00:04.09~00:04.20 Hold: lips closed, reaction beat only (no speech after audio ends)
```

### S02 (10s) — Medium close-up (two-shot, Choi weighted)

```
[SCENE SPECIFICATION]
- Scene ID: S02
- Timecode: 00:10.00 - 00:20.00 (Duration: 10s)
- Audio Anchor: line002 김씨 Attack 00:06.12–00:10.17 (대사: 이거 임자 되시는 분이 직접 감으…)
- Transition Out: Hard cut (cold open → caption)
- References: KIM@45-neutral, CHOI@front-wary, LOC@junkyard-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his 50s (reference: CHOI sheet), stocky build, short cropped salt-and-pepper hair, grease-stained plain grey work vest over plain dark shirt, black work gloves, worn radio on belt arms crossed, staring silently at Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt who is finishing a sentence; the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle handle visible at frame edge.
(Expression, pre-baked 50%): Choi: suspicious silence. Kim: steady resolve.
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering
(Cinematography): 50mm lens, f/2.8, medium shot, natural perspective, soft background separation; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Overcast daylight 5600K from upper-left, bare bulbs as warm 3200K practicals, dramatic high-contrast shadows between paper bales, warm rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Kim lips move with dialogue, Choi single slow blink only, no head turn.
- Edit Strategy: 00:06.12~00:08.12 Talking face (line 2) → 00:08.12~00:09.12 B-roll: ECU leather strap on handle (S03 keyframe) → 00:09.12~00:10.17 Reaction: Choi wary stare → 00:10.17~00:11.13 Hold: lips closed, reaction beat only (no speech after audio ends)
```

### S03 (5s) — Extreme close-up

```
[SCENE SPECIFICATION]
- Scene ID: S03
- Timecode: 00:20.00 - 00:25.00 (Duration: 5s)
- Audio Anchor: 자막카드 Attack 00:20.22–00:24.22 (자막: 말이 없던 그가, 왜 고물상 앞을…)
- Transition Out: Dissolve 0.5s
- References: LOC@junkyard-key1

[KEYFRAME GENERATION PROMPT]
(Subject): The frayed brown leather strap wound around the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle handle, nothing else in focus, dark moody frame, no people.
(Expression, pre-baked 50%): —
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Overcast daylight 5600K from upper-left, bare bulbs as warm 3200K practicals, dramatic high-contrast shadows between paper bales, warm rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Almost imperceptible focus breathing, dust motes drifting.
```

### S04 (5s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S04
- Timecode: 00:25.00 - 00:30.00 (Duration: 5s)
- Audio Anchor: 자막카드 Attack 00:25.22–00:28.04 (자막: 김씨와 폐지 할머니)
- Transition Out: Hard cut
- References: LOC@apt-gate-night

[KEYFRAME GENERATION PROMPT]
(Subject): Empty sidewalk at dusk, no people, caption card space in lower third.
(Expression, pre-baked 50%): —
(Environment): sidewalk in front of an apartment-complex main gate (LOC apt-gate): flower bed and low wall, no signs, no lettering
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Blue-hour dusk, cool 4800K ambient with one warm practical lamp, low-key, soft rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Static plate, faint leaf movement only.
```

### S05 (5s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S05
- Timecode: 00:30.00 - 00:35.00 (Duration: 5s)
- Audio Anchor: 자막카드 Attack 00:30.22–00:33.02 (자막: 사흘 전)
- Transition Out: Dissolve 0.5s (time rewind)
- References: LOC@apt-gate-day

[KEYFRAME GENERATION PROMPT]
(Subject): Empty sidewalk in afternoon sun, no people.
(Expression, pre-baked 50%): —
(Environment): sidewalk in front of an apartment-complex main gate (LOC apt-gate): flower bed and low wall, no signs, no lettering
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Static plate, light breeze in the flower bed.
```

### S06 (10s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S06
- Timecode: 00:35.00 - 00:45.00 (Duration: 10s)
- Audio Anchor: line003 내레이터 Attack 00:36.12–00:41.14 (내레: 이 골목의 리어카는, 유독 손잡이…) / line004 내레이터 Attack 00:41.21–00:48.13 (내레: 그 리어카는 이십 년 전, 할머니…)
- Transition Out: J-Cut 0.5s (cart creak leads)
- References: GMA@fullbody-front, LOC@apt-gate-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves slowly pulling the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle along the sidewalk toward camera-left, afternoon sun on the handle.
(Expression, pre-baked 50%): Neutral, tired dignity.
(Environment): sidewalk in front of an apartment-complex main gate (LOC apt-gate): flower bed and low wall, no signs, no lettering
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Very slow lateral drift (follows subject at walking pace)
- Character Motion: Slow walk, cart wheel turns, gentle lateral camera drift matching her pace, no fast motion.
```

### S07 (10s) — Medium shot

```
[SCENE SPECIFICATION]
- Scene ID: S07
- Timecode: 00:45.00 - 00:55.00 (Duration: 10s)
- Audio Anchor: line004 내레이터 Attack 00:41.21–00:48.13 (내레: 그 리어카는 이십 년 전, 할머니…) / line005 내레이터 Attack 00:48.21–00:57.20 (내레: 손잡이에 감긴 가죽끈도, 삐걱이는…)
- Transition Out: J-Cut 0.5s
- References: GMA@45-neutral, LOC@apt-gate-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves bending to pick up a flattened cardboard box and placing it on the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle.
(Expression, pre-baked 50%): Neutral, focused on the work.
(Environment): sidewalk in front of an apartment-complex main gate (LOC apt-gate): flower bed and low wall, no signs, no lettering, alley corner
(Cinematography): 50mm lens, f/2.8, medium shot, natural perspective, soft background separation; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Slow bend and lift, cardboard sways, no rapid moves.
```

### S08 (5s) — Close-up

```
[SCENE SPECIFICATION]
- Scene ID: S08
- Timecode: 00:55.00 - 01:00.00 (Duration: 5s)
- Audio Anchor: line005 내레이터 Attack 00:48.21–00:57.20 (내레: 손잡이에 감긴 가죽끈도, 삐걱이는…) / line006 내레이터 Attack 00:58.03–01:03.23 (내레: 할머니에게 이 리어카는, 벌이가 …)
- Transition Out: Match cut (strap → hands on strap)
- References: LOC@apt-gate-key1

[KEYFRAME GENERATION PROMPT]
(Subject): The frayed brown leather strap on the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle handle, polished smooth by twenty years of hands, warm afternoon light raking across it.
(Expression, pre-baked 50%): —
(Environment): sidewalk in front of an apartment-complex main gate (LOC apt-gate): flower bed and low wall, no signs, no lettering
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Gentle focal adjustment only.
```

### S09 (5s) — Close-up (hands)

```
[SCENE SPECIFICATION]
- Scene ID: S09
- Timecode: 01:00.00 - 01:05.00 (Duration: 5s)
- Audio Anchor: line006 내레이터 Attack 00:58.03–01:03.23 (내레: 할머니에게 이 리어카는, 벌이가 …) / line007 내레이터 Attack 01:04.06–01:13.00 (내레: 다른 건 아무리 험하게 다뤄도, …)
- Transition Out: J-Cut 0.5s
- References: GMA@hands, LOC@apt-gate-day

[KEYFRAME GENERATION PROMPT]
(Subject): The gloved, wrinkled hands of Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves wiping the leather strap on the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle handle with a small rag, tender and careful.
(Expression, pre-baked 50%): —
(Environment): sidewalk in front of an apartment-complex main gate (LOC apt-gate): flower bed and low wall, no signs, no lettering
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in (zoom 1.05)
- Character Motion: Slow wiping motion of the hands, slight push-in.
```

### S10 (5s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S10
- Timecode: 01:05.00 - 01:10.00 (Duration: 5s)
- Audio Anchor: line007 내레이터 Attack 01:04.06–01:13.00 (내레: 다른 건 아무리 험하게 다뤄도, …)
- Transition Out: J-Cut 0.5s
- References: KIM@front-neutral, LOC@guard-booth-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt seen through the booth window glass, watching expressionlessly as the grandmother passes outside (she is a soft blurred figure beyond the glass).
(Expression, pre-baked 50%): Blank, unreadable, eyes following.
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing
(Cinematography): 50mm lens, f/2.8, medium shot, natural perspective, soft background separation; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Eyes track slowly left to right, single blink, micro breathing.
```

### S11 (5s) — Full shot (rear)

```
[SCENE SPECIFICATION]
- Scene ID: S11
- Timecode: 01:10.00 - 01:15.00 (Duration: 5s)
- Audio Anchor: line007 내레이터 Attack 01:04.06–01:13.00 (내레: 다른 건 아무리 험하게 다뤄도, …) / line008 내레이터 Attack 01:13.07–01:19.22 (내레: 경비 김씨는 매일 아침, 재활용 …)
- Transition Out: J-Cut 0.5s (birds lead)
- References: KIM@fullbody-back, LOC@guard-booth-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt from behind, quietly setting a neat stack of flattened cardboard boxes beside the flower bed outside the booth, early morning.
(Expression, pre-baked 50%): —
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, flower bed outside
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft morning daylight through the booth window from upper-left, 5600K, gentle contrast, dust motes in the light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static rear shot
- Character Motion: Slow bend, places the stack, begins to turn away (max 20°), no face turn to camera.
```

### S12 (5s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S12
- Timecode: 01:15.00 - 01:20.00 (Duration: 5s)
- Audio Anchor: line008 내레이터 Attack 01:13.07–01:19.22 (내레: 경비 김씨는 매일 아침, 재활용 …)
- Transition Out: Dissolve 0.5s
- References: GMA@fullbody-side, LOC@apt-gate-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves discovering the stack of boxes by the flower bed and giving a small nod before loading them onto the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle, early morning.
(Expression, pre-baked 50%): Faint gratitude, small nod.
(Environment): sidewalk in front of an apartment-complex main gate (LOC apt-gate): flower bed and low wall, no signs, no lettering
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft natural daylight from upper-left, 5600K clean balanced tones, subtle warm rim light separating subject from background, gentle contrast
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Small nod, slow lift of the boxes.
```

### S13 (5s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S13
- Timecode: 01:20.00 - 01:25.00 (Duration: 5s)
- Audio Anchor: line009 내레이터 Attack 01:20.05–01:22.19 (내레: 말 한마디 없이, 그저 그렇게.) / line010 내레이터 Attack 01:23.02–01:27.22 (내레: 그날 오후, 철거 트럭이 골목의 …)
- Transition Out: J-Cut 0.5s (truck idle leads)
- References: GMA@fullbody-front, LOC@demolition-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves parking the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle beside the rubble wall and walking away from it to collect paper, late afternoon dust haze.
(Expression, pre-baked 50%): Neutral.
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around
(Cinematography): 24mm wide angle, deep focus, imposing perspective, sharp architectural lines; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Slow walk away from the cart, dust drifting.
```

### S14 (5s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S14
- Timecode: 01:25.00 - 01:30.00 (Duration: 5s)
- Audio Anchor: line010 내레이터 Attack 01:23.02–01:27.22 (내레: 그날 오후, 철거 트럭이 골목의 …) / line011 내레이터 Attack 01:28.10–01:31.10 (내레: 리어카도 함께, 고철더미인 줄 알…)
- Transition Out: Hard cut
- References: LOC@demolition-key1

[KEYFRAME GENERATION PROMPT]
(Subject): Demolition workers (backs to camera, faceless, no text on vests) loading rubble into a truck; the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle sits among the scrap in the background about to be loaded. No readable text anywhere.
(Expression, pre-baked 50%): —
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around
(Cinematography): 24mm wide angle, deep focus, imposing perspective, sharp architectural lines; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in toward the truck (zoom 1.05)
- Character Motion: Slow push-in, workers move slowly, truck exhaust drifts.
```

### S15 (10s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S15
- Timecode: 01:30.00 - 01:40.00 (Duration: 10s)
- Audio Anchor: line011 내레이터 Attack 01:28.10–01:31.10 (내레: 리어카도 함께, 고철더미인 줄 알…) / line012 할머니 Attack 01:31.17–01:32.20 (대사: …내 리어카…) / line013 내레이터 Attack 01:33.12–01:38.12 (내레: 말은 짧았지만, 그 말 안에 이십…) / line014 내레이터 Attack 01:38.19–01:45.15 (내레: 할머니는 그날 밤, 늦도록 혼자 …)
- Transition Out: Hold 0.8s → Dissolve 0.5s
- References: GMA@front-tense, LOC@demolition-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves holding an armful of paper, frozen, staring at the empty spot where the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle stood, lips just parted.
(Expression, pre-baked 50%): Shock held at 50%: wide eyes, parted lips (keyframe carries the emotion).
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in (zoom 1.08) — replaces dolly-zoom
- Character Motion: Only a slow push-in, one slow blink, lips form the short line, no head turn.
- Edit Strategy: 01:31.17~01:32.20 Talking face (line 15) then hold on frozen face; narration lines 16–17 over this and S16 → 01:32.20~01:33.05 Hold: lips closed, reaction beat only (no speech after audio ends)
```

### S16 (5s) — Full shot, high angle

```
[SCENE SPECIFICATION]
- Scene ID: S16
- Timecode: 01:40.00 - 01:45.00 (Duration: 5s)
- Audio Anchor: line014 내레이터 Attack 01:38.19–01:45.15 (내레: 할머니는 그날 밤, 늦도록 혼자 …)
- Transition Out: Dissolve 0.5s
- References: GMA@fullbody-front, LOC@demolition-key2

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves sunk to her knees on the dusty ground, one empty gloved hand pressed to the earth, seen from a high angle.
(Expression, pre-baked 50%): Collapse, head bowed.
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Late-afternoon golden hour, key from upper-left, 4500K warm amber, long soft shadows, warm rim light on hair and shoulders
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Micro trembling of the hand, dust settling, nothing else.
```

### S17 (10s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S17
- Timecode: 01:45.00 - 01:55.00 (Duration: 10s)
- Audio Anchor: line014 내레이터 Attack 01:38.19–01:45.15 (내레: 할머니는 그날 밤, 늦도록 혼자 …) / line015 내레이터 Attack 01:45.23–01:50.15 (내레: 아무도, 리어카가 어디로 갔는지 …)
- Transition Out: Dissolve 0.5s
- References: GMA@fullbody-side, LOC@demolition-night

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves alone at night, small in the frame, wandering slowly along the fence of the demolition lot looking for the cart.
(Expression, pre-baked 50%): Exhausted.
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around, night
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key night, single warm sodium street lamp as key from upper-left, 3200K tungsten feel, deep cinematic shadows, thin mist catching the light, Chiaroscuro
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Subtle handheld sway
- Character Motion: Slow walk, subtle handheld sway, mist drifting.
```

### S18 (10s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S18
- Timecode: 01:55.00 - 02:05.00 (Duration: 10s)
- Audio Anchor: line016 내레이터 Attack 01:56.12–02:00.17 (내레: 그에게도, 아무도 모르는 이유가 …) / line017 내레이터 Attack 02:01.00–02:06.08 (내레: 그래서 그는, 아무도 시키지 않은…)
- Transition Out: J-Cut 0.5s (clock tick leads)
- References: KIM@front-neutral, LOC@guard-booth-night

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt inside the booth at night, halfway through putting on his jacket, paused, looking out the window at the empty spot where the grandmother usually passes.
(Expression, pre-baked 50%): Still, something decided behind the eyes.
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, night
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key booth interior at night, warm desk lamp key from upper-left 3200K, cool CCTV monitor glow as fill from the right, Chiaroscuro, rim light on the shoulder
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Single slow blink, micro breathing, eyes settle on the window.
```

### S19 (5s) — Full shot (rear follow)

```
[SCENE SPECIFICATION]
- Scene ID: S19
- Timecode: 02:05.00 - 02:10.00 (Duration: 5s)
- Audio Anchor: line017 내레이터 Attack 02:01.00–02:06.08 (내레: 그래서 그는, 아무도 시키지 않은…) / line018 내레이터 Attack 02:06.15–02:12.01 (내레: 첫째 날 밤, 샅샅이 뒤진 골목엔…)
- Transition Out: Dissolve 0.4s (night ambience bridge)
- References: KIM@fullbody-back, LOC@guard-booth-night

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt from behind at shoulder height, opening the booth door and stepping out into the night, flashlight in hand.
(Expression, pre-baked 50%): —
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, doorway to the dark
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key booth interior at night, warm desk lamp key from upper-left 3200K, cool CCTV monitor glow as fill from the right, Chiaroscuro, rim light on the shoulder
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Very slow push forward behind Kim
- Character Motion: Door opens slowly, he steps through, camera drifts forward slightly.
```

### S20 (10s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S20
- Timecode: 02:10.00 - 02:20.00 (Duration: 10s)
- Audio Anchor: line018 내레이터 Attack 02:06.15–02:12.01 (내레: 첫째 날 밤, 샅샅이 뒤진 골목엔…) / line019 내레이터 Attack 02:12.08–02:21.02 (내레: 비가 쏟아지던 둘째 날 밤, 우산…)
- Transition Out: Dissolve 0.5s
- References: KIM@fullbody-side, LOC@alley-night-night

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt walking slowly along the dark alley sweeping a flashlight beam over stacked paper bundles.
(Expression, pre-baked 50%): Searching.
(Environment): dark neighbourhood alley at night (LOC alley-night): one sodium street lamp, stacked paper bundles, old shutter doors, thin night mist
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key night, single warm sodium street lamp as key from upper-left, 3200K tungsten feel, deep cinematic shadows, thin mist catching the light, Chiaroscuro
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Very slow lateral drift
- Character Motion: Slow walk, flashlight beam sweeps slowly, mist.
```

### S21 (10s) — Full shot, high angle

```
[SCENE SPECIFICATION]
- Scene ID: S21
- Timecode: 02:20.00 - 02:30.00 (Duration: 10s)
- Audio Anchor: line019 내레이터 Attack 02:12.08–02:21.02 (내레: 비가 쏟아지던 둘째 날 밤, 우산…) / line020 내레이터 Attack 02:21.10–02:28.13 (내레: 쉬어가던 밤, 그는 아내의 꽃무늬…) / line021 내레이터 Attack 02:28.21–02:37.01 (내레: 거기엔 이렇게 적혀 있었습니다 —…)
- Transition Out: Dissolve 0.5s
- References: KIM@fullbody-front, LOC@alley-night-key1

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt soaked, no umbrella, standing in heavy rain in the alley, shoulders slumped, looking down the empty street.
(Expression, pre-baked 50%): Weary.
(Environment): dark neighbourhood alley at night (LOC alley-night): one sodium street lamp, stacked paper bundles, old shutter doors, thin night mist, pouring rain
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Night rain, single street lamp key from upper-left 3200K, wet reflective ground, backlit rain streaks, deep shadows
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Subtle handheld sway
- Character Motion: Rain falls, he stands nearly still, slow exhale, subtle sway.
```

### S22 (10s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S22
- Timecode: 02:30.00 - 02:40.00 (Duration: 10s)
- Audio Anchor: line021 내레이터 Attack 02:28.21–02:37.01 (내레: 거기엔 이렇게 적혀 있었습니다 —…) / line022 내레이터 Attack 02:37.09–02:47.00 (내레: 십 년 전, 아무도 그에게 말을 …)
- Transition Out: Match cut (hands → notebook)
- References: KIM@front-neutral, LOC@guard-booth-night

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt at the booth desk at night, taking an old floral-patterned notebook from the drawer and opening it gently.
(Expression, pre-baked 50%): Quiet longing.
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, night
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key booth interior at night, warm desk lamp key from upper-left 3200K, cool CCTV monitor glow as fill from the right, Chiaroscuro, rim light on the shoulder
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in (zoom 1.05)
- Character Motion: Hands open the notebook slowly, eyes lower, single blink.
```

### S23 (5s) — Extreme close-up

```
[SCENE SPECIFICATION]
- Scene ID: S23
- Timecode: 02:40.00 - 02:45.00 (Duration: 5s)
- Audio Anchor: line022 내레이터 Attack 02:37.09–02:47.00 (내레: 십 년 전, 아무도 그에게 말을 …)
- Transition Out: J-Cut 0.5s
- References: LOC@guard-booth-key1

[KEYFRAME GENERATION PROMPT]
(Subject): Open page of an old floral notebook under a desk lamp; handwriting is present but rendered as soft illegible ink strokes, out of focus, no readable letters.
(Expression, pre-baked 50%): —
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key booth interior at night, warm desk lamp key from upper-left 3200K, cool CCTV monitor glow as fill from the right, Chiaroscuro, rim light on the shoulder
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, rack focus edge → writing
- Character Motion: Slow rack focus only.
```

### S24 (10s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S24
- Timecode: 02:45.00 - 02:55.00 (Duration: 10s)
- Audio Anchor: line022 내레이터 Attack 02:37.09–02:47.00 (내레: 십 년 전, 아무도 그에게 말을 …) / line023 내레이터 Attack 02:47.07–02:51.20 (내레: 김씨는 그날을, 십 년이 지나도록…) / line024 내레이터 Attack 02:52.03–02:56.21 (내레: 다리가 저려올 때쯤에야, 셋째 날…)
- Transition Out: Sepia dissolve 0.5s → flashback
- References: KIM@front-neutral, LOC@guard-booth-night

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt at the booth window at night, opening a thermos lid and drinking, gazing far away.
(Expression, pre-baked 50%): Tired, remembering.
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, night
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key booth interior at night, warm desk lamp key from upper-left 3200K, cool CCTV monitor glow as fill from the right, Chiaroscuro, rim light on the shoulder
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Slow sip, gaze fixed far, micro breathing.
```

### S25 (10s) — Close-up (feet/legs)

```
[SCENE SPECIFICATION]
- Scene ID: S25
- Timecode: 02:55.00 - 03:05.00 (Duration: 10s)
- Audio Anchor: line024 내레이터 Attack 02:52.03–02:56.21 (내레: 다리가 저려올 때쯤에야, 셋째 날…) / line025 내레이터 Attack 02:57.04–03:02.00 (내레: 철거 업체가 고철을 넘긴 곳 — …)
- Transition Out: Dissolve 0.4s
- References: KIM@fullbody-side, LOC@alley-night-night

[KEYFRAME GENERATION PROMPT]
(Subject): Close-up of the tired legs and shoes of Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt dragging slightly on the wet alley pavement at night.
(Expression, pre-baked 50%): —
(Environment): dark neighbourhood alley at night (LOC alley-night): one sodium street lamp, stacked paper bundles, old shutter doors, thin night mist
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key night, single warm sodium street lamp as key from upper-left, 3200K tungsten feel, deep cinematic shadows, thin mist catching the light, Chiaroscuro
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Slow heavy steps, slight limp.
```

### S26 (10s) — Full shot

```
[SCENE SPECIFICATION]
- Scene ID: S26
- Timecode: 03:05.00 - 03:15.00 (Duration: 10s)
- Audio Anchor: line026 내레이터 Attack 03:06.12–03:11.12 (내레: 김씨는 그길로, 소문난 고물상들을…) / line027 내레이터 Attack 03:12.00–03:17.13 (내레: 세 번째 집, 마당 안쪽에 낯익은…)
- Transition Out: J-Cut 0.5s (daytime street leads)
- References: KIM@fullbody-front, LOC@junkyard-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt walking along a daytime street lined with scrap handcarts at the entrance of the scrap-dealer district, looking around.
(Expression, pre-baked 50%): Alert.
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering street entrance
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft natural daylight from upper-left, 5600K clean balanced tones, subtle warm rim light separating subject from background, gentle contrast
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Very slow lateral drift
- Character Motion: Slow walk, head turns limited to 15°, camera drifts.
```

### S27 (5s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S27
- Timecode: 03:15.00 - 03:20.00 (Duration: 5s)
- Audio Anchor: line027 내레이터 Attack 03:12.00–03:17.13 (내레: 세 번째 집, 마당 안쪽에 낯익은…)
- Transition Out: Hard cut
- References: KIM@45-neutral, LOC@junkyard-key1

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt stopped at the scrapyard gate, eyes locking onto a familiar handle deep inside the yard.
(Expression, pre-baked 50%): Recognition at 50%: eyes narrow, breath held.
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Overcast daylight 5600K from upper-left, bare bulbs as warm 3200K practicals, dramatic high-contrast shadows between paper bales, warm rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in (zoom 1.06)
- Character Motion: Push-in on the eyes, single blink, no head turn.
```

### S28 (10s) — Medium close-up (two-shot, Choi speaking)

```
[SCENE SPECIFICATION]
- Scene ID: S28
- Timecode: 03:20.00 - 03:30.00 (Duration: 10s)
- Audio Anchor: line028 최사장 Attack 03:22.00–03:26.05 (대사: 이미 계근까지 끝난 물건입니다. …) / line029 내레이터 Attack 03:26.17–03:28.20 (내레: 김씨는, 물러서지 않았습니다.)
- Transition Out: Hard cut
- References: CHOI@front-neutral, KIM@45-neutral, LOC@junkyard-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his 50s (reference: CHOI sheet), stocky build, short cropped salt-and-pepper hair, grease-stained plain grey work vest over plain dark shirt, black work gloves, worn radio on belt speaking briskly to Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt, gesturing at the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle beside them in the scrapyard.
(Expression, pre-baked 50%): Choi: businesslike. Kim: silent, firm.
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering
(Cinematography): 50mm lens, f/2.8, medium shot, natural perspective, soft background separation; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Overcast daylight 5600K from upper-left, bare bulbs as warm 3200K practicals, dramatic high-contrast shadows between paper bales, warm rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Choi lips move with dialogue, small hand gesture, Kim still.
- Edit Strategy: 03:22.00~03:24.00 Talking face Choi (line 31) → 03:24.00~03:25.00 B-roll: rusty scale / paper bales → 03:25.00~03:26.05 Reaction: Kim unmoved
```

### S29 (10s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S29
- Timecode: 03:30.00 - 03:40.00 (Duration: 10s)
- Audio Anchor: line030 김씨 Attack 03:31.18–03:34.03 (대사: 이 손잡이, 가죽끈 감긴 거 보이…) / line031 김씨 Attack 03:36.06–03:40.11 (대사: 이거 임자 되시는 분이 직접 감으…)
- Transition Out: Match cut (hand on strap)
- References: KIM@front-neutral, LOC@junkyard-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt's rough hand slowly resting on the leather strap of the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle handle, his face resolute above it.
(Expression, pre-baked 50%): Firm resolve.
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Overcast daylight 5600K from upper-left, bare bulbs as warm 3200K practicals, dramatic high-contrast shadows between paper bales, warm rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in (zoom 1.05)
- Character Motion: Hand settles on the strap, lips move with the line, single blink.
- Edit Strategy: 03:31.18~03:34.03 Talking face (line 33) → 03:34.03~03:34.14 Hold: lips closed, reaction beat only (no speech after audio ends)
```

### S30 (10s) — Close-up (Choi reaction)

```
[SCENE SPECIFICATION]
- Scene ID: S30
- Timecode: 03:40.00 - 03:50.00 (Duration: 10s)
- Audio Anchor: line031 김씨 Attack 03:36.06–03:40.11 (대사: 이거 임자 되시는 분이 직접 감으…) / line032 내레이터 Attack 03:41.19–03:46.00 (내레: 최사장은 잠시, 자신의 어머니를 …) / line033 내레이터 Attack 03:46.12–03:51.18 (내레: 돌아가시기 전까지, 낡은 유모차를…)
- Transition Out: Hold 1s → Dissolve 0.5s
- References: CHOI@front-neutral, LOC@junkyard-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his 50s (reference: CHOI sheet), stocky build, short cropped salt-and-pepper hair, grease-stained plain grey work vest over plain dark shirt, black work gloves, worn radio on belt arms crossed, listening, his hard expression beginning to soften; Kim is a soft out-of-focus shape at frame edge.
(Expression, pre-baked 50%): Softening (keyframe at 50%: brow relaxing).
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Overcast daylight 5600K from upper-left, bare bulbs as warm 3200K practicals, dramatic high-contrast shadows between paper bales, warm rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in (zoom 1.05)
- Character Motion: Slow push-in, one blink, jaw loosens slightly, no head turn.
- Edit Strategy: 03:36.06~03:38.06 Talking face Kim (line 34, from S29 angle) → 03:38.06~03:39.06 B-roll: strap ECU → 03:39.06~03:40.11 Reaction: Choi softening (this keyframe) → 03:40.11~03:41.07 Hold: lips closed, reaction beat only (no speech after audio ends)
```

### S31 (10s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S31
- Timecode: 03:50.00 - 04:00.00 (Duration: 10s)
- Audio Anchor: line033 내레이터 Attack 03:46.12–03:51.18 (내레: 돌아가시기 전까지, 낡은 유모차를…) / line034 최사장 Attack 03:55.08–03:57.13 (대사: …가져가십쇼. 값은 됐습니다.)
- Transition Out: Hold 1s → Dissolve 0.5s → dawn
- References: CHOI@front-smile, KIM@45-neutral, LOC@junkyard-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his 50s (reference: CHOI sheet), stocky build, short cropped salt-and-pepper hair, grease-stained plain grey work vest over plain dark shirt, black work gloves, worn radio on belt with a softened face, giving a small dismissive wave of the hand toward Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt and the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle.
(Expression, pre-baked 50%): Gruff warmth, faint smile.
(Environment): scrapyard yard (LOC junkyard): compressed paper bales, rusty scale, bare bulbs hanging overhead, one old truck, blank corrugated metal wall with no lettering
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Overcast daylight 5600K from upper-left, bare bulbs as warm 3200K practicals, dramatic high-contrast shadows between paper bales, warm rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Lips move with the short line, one small hand wave, single blink.
- Edit Strategy: 03:55.08~03:57.13 Talking face Choi (line 37) → 03:57.13~03:58.15 Hold: lips closed, reaction beat only (no speech after audio ends)
```

### S32 (5s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S32
- Timecode: 04:00.00 - 04:05.00 (Duration: 5s)
- Audio Anchor: line035 내레이터 Attack 04:01.12–04:06.22 (내레: 그는 밤늦도록, 자신의 몫으로 새…)
- Transition Out: J-Cut 0.5s (metal clink leads)
- References: KIM@45-neutral, LOC@guard-booth-night

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt late at night beside the booth, flashlight held in his mouth, fitting a new wheel onto the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle.
(Expression, pre-baked 50%): Absorbed.
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, exterior at night
(Cinematography): 50mm lens, f/2.8, medium shot, natural perspective, soft background separation; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key booth interior at night, warm desk lamp key from upper-left 3200K, cool CCTV monitor glow as fill from the right, Chiaroscuro, rim light on the shoulder
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Hands work slowly on the wheel, flashlight beam jitters slightly.
```

### S33 (5s) — Close-up (hands)

```
[SCENE SPECIFICATION]
- Scene ID: S33
- Timecode: 04:05.00 - 04:10.00 (Duration: 5s)
- Audio Anchor: line035 내레이터 Attack 04:01.12–04:06.22 (내레: 그는 밤늦도록, 자신의 몫으로 새…) / line036 내레이터 Attack 04:07.10–04:13.18 (내레: 거친 쇠손잡이에 시릴 손을 위해,…)
- Transition Out: Dissolve 0.4s
- References: KIM@hands, LOC@guard-booth-night

[KEYFRAME GENERATION PROMPT]
(Subject): The rough hands of Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt carefully wrapping one old navy work glove over the frayed leather strap of the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle handle.
(Expression, pre-baked 50%): —
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, night
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Low-key booth interior at night, warm desk lamp key from upper-left 3200K, cool CCTV monitor glow as fill from the right, Chiaroscuro, rim light on the shoulder
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Slow wrapping motion only.
```

### S34 (10s) — Long shot (rear follow)

```
[SCENE SPECIFICATION]
- Scene ID: S34
- Timecode: 04:10.00 - 04:20.00 (Duration: 10s)
- Audio Anchor: line036 내레이터 Attack 04:07.10–04:13.18 (내레: 거친 쇠손잡이에 시릴 손을 위해,…) / line037 내레이터 Attack 04:14.06–04:19.20 (내레: 그날 새벽, 아무도 없는 골목에 …)
- Transition Out: Hard cut → caption
- References: KIM@fullbody-back, LOC@alley-night-key2

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt from behind pushing the repaired rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle alone through the pre-dawn alley mist and setting it quietly in the grandmother's usual spot.
(Expression, pre-baked 50%): —
(Environment): dark neighbourhood alley at night (LOC alley-night): one sodium street lamp, stacked paper bundles, old shutter doors, thin night mist, pre-dawn
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Pre-dawn blue hour, 4000K cool ambient with faint warm horizon, mist, low-key, soft rim from a single lamp
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Very slow push forward behind Kim
- Character Motion: Slow push of the cart, sets it down, walks away, camera drifts forward.
```

### S35 (5s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S35
- Timecode: 04:20.00 - 04:25.00 (Duration: 5s)
- Audio Anchor: 자막카드 Attack 04:20.22–04:23.02 (자막: 다음날 아침)
- Transition Out: Hard cut
- References: LOC@demolition-key2

[KEYFRAME GENERATION PROMPT]
(Subject): Empty alley near the demolition lot in early-morning mist, the repaired rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle standing alone, no people.
(Expression, pre-baked 50%): —
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around, morning mist
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Pre-dawn blue hour, 4000K cool ambient with faint warm horizon, mist, low-key, soft rim from a single lamp
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Mist drifts, nothing else.
```

### S36 (5s) — Medium shot

```
[SCENE SPECIFICATION]
- Scene ID: S36
- Timecode: 04:25.00 - 04:30.00 (Duration: 5s)
- Audio Anchor: line038 할머니 Attack 04:28.00–04:29.19 (대사: …영감이 감아준 건데…)
- Transition Out: Dissolve 0.4s
- References: GMA@front-tense, LOC@demolition-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves stopping in her tracks, startled, then stepping toward the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle she thought was lost.
(Expression, pre-baked 50%): Startled, disbelief.
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around, early morning
(Cinematography): 50mm lens, f/2.8, medium shot, natural perspective, soft background separation; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft natural daylight from upper-left, 5600K clean balanced tones, subtle warm rim light separating subject from background, gentle contrast
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Two slow steps forward, hand rising toward the handle, lips form the short line.
- Edit Strategy: 04:28.00~04:29.19 Talking face (line 42) → 04:29.19~04:30.17 Hold: lips closed, reaction beat only (no speech after audio ends)
```

### S37 (10s) — Close-up (hands)

```
[SCENE SPECIFICATION]
- Scene ID: S37
- Timecode: 04:30.00 - 04:40.00 (Duration: 10s)
- Audio Anchor: line039 내레이터 Attack 04:31.05–04:38.12 (내레: 말 한마디 건네지 않았지만, 두 …) / line040 내레이터 Attack 04:39.00–04:44.10 (내레: 빚을 갚는 데, 꼬박 십 년이 걸…)
- Transition Out: Dissolve 0.4s
- References: GMA@hands, LOC@demolition-day

[KEYFRAME GENERATION PROMPT]
(Subject): The two gloved hands of Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves cupping and stroking the glove-wrapped leather strap on the rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle handle.
(Expression, pre-baked 50%): —
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft natural daylight from upper-left, 5600K clean balanced tones, subtle warm rim light separating subject from background, gentle contrast
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Slow cinematic push-in (zoom 1.05)
- Character Motion: Hands tremble gently, slow push-in.
```

### S38 (5s) — Choker close-up

```
[SCENE SPECIFICATION]
- Scene ID: S38
- Timecode: 04:40.00 - 04:45.00 (Duration: 5s)
- Audio Anchor: line040 내레이터 Attack 04:39.00–04:44.10 (내레: 빚을 갚는 데, 꼬박 십 년이 걸…) / line041 내레이터 Attack 04:44.22–04:50.17 (내레: 고마움은 몰라도 된다고, 그는 그…)
- Transition Out: Sepia dissolve 0.5s → flashback
- References: GMA@front-smile, LOC@demolition-day

[KEYFRAME GENERATION PROMPT]
(Subject): The face of Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves, eyes brimming with tears, a faint smile.
(Expression, pre-baked 50%): Tearful smile at 50% (keyframe).
(Environment): redevelopment demolition lot (LOC demolition): collapsed wall rubble, faint dust haze, safety fence, blank white sign with no lettering, no people around
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft natural daylight from upper-left, 5600K clean balanced tones, subtle warm rim light separating subject from background, gentle contrast
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Single slow blink, one tear line, micro breathing, no head turn.
```

### S39 (5s) — Medium shot (two-shot)

```
[SCENE SPECIFICATION]
- Scene ID: S39
- Timecode: 04:45.00 - 04:50.00 (Duration: 5s)
- Audio Anchor: line041 내레이터 Attack 04:44.22–04:50.17 (내레: 고마움은 몰라도 된다고, 그는 그…)
- Transition Out: Sepia dissolve 0.5s → present
- References: GMA@fullbody-front, KIM@fullbody-front, LOC@alley-night-key1

[KEYFRAME GENERATION PROMPT]
(Subject): Flashback ten years ago: snowy dark alley, Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves silently handing a steaming boiled corn to Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt, both ten years younger, sepia memory grade.
(Expression, pre-baked 50%): Wordless kindness.
(Environment): dark neighbourhood alley at night (LOC alley-night): one sodium street lamp, stacked paper bundles, old shutter doors, thin night mist, snowfall
(Cinematography): 50mm lens, f/2.8, medium shot, natural perspective, soft background separation; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Memory flashback: desaturated sepia grade, soft diffused snowy light, 3200K warm feel, gentle halation, fine grain
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Snow falls slowly, her hand extends, his hand receives, nothing else.
```

### S40 (5s) — Close-up

```
[SCENE SPECIFICATION]
- Scene ID: S40
- Timecode: 04:50.00 - 04:55.00 (Duration: 5s)
- Audio Anchor: line041 내레이터 Attack 04:44.22–04:50.17 (내레: 고마움은 몰라도 된다고, 그는 그…) / line042 내레이터 Attack 04:51.05–04:56.01 (내레: 그날 이후, 할머니의 리어카는 다…)
- Transition Out: Hard cut (bookend impact)
- References: LOC@guard-booth-day

[KEYFRAME GENERATION PROMPT]
(Subject): A small plastic bag with steaming boiled corn resting on the booth windowsill in early-morning sunlight, no people.
(Expression, pre-baked 50%): —
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, windowsill
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft morning daylight through the booth window from upper-left, 5600K, gentle contrast, dust motes in the light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Steam rises slowly, dust motes.
```

### S41 (5s) — Medium close-up

```
[SCENE SPECIFICATION]
- Scene ID: S41
- Timecode: 04:55.00 - 05:00.00 (Duration: 5s)
- Audio Anchor: line042 내레이터 Attack 04:51.05–04:56.01 (내레: 그날 이후, 할머니의 리어카는 다…)
- Transition Out: J-Cut 0.5s
- References: KIM@front-smile, LOC@guard-booth-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt discovering the corn bag on the windowsill, lifting it in one hand, a faint smile.
(Expression, pre-baked 50%): Faint smile at 50% (keyframe).
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing
(Cinematography): 85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft optical bokeh, cinematic portrait; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft morning daylight through the booth window from upper-left, 5600K, gentle contrast, dust motes in the light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Lifts the bag slowly, smile deepens by a hair, single blink.
```

### S42 (5s) — Long shot

```
[SCENE SPECIFICATION]
- Scene ID: S42
- Timecode: 05:00.00 - 05:05.00 (Duration: 5s)
- Audio Anchor: 무음 (앰비언스만)
- Transition Out: Dissolve 0.5s
- References: GMA@fullbody-side, LOC@apt-gate-day

[KEYFRAME GENERATION PROMPT]
(Subject): Korean woman in her late 70s (reference: GRANDMA sheet), thin stooped frame, deeply wrinkled gentle face, faded brown floral headscarf over grey hair, thick plain navy quilted jacket, worn dark-brown baggy monpe trousers, worn brown work gloves pulling the repaired rusted paper-collecting handcart (rear-car) with an old frayed brown leather strap wound around its handle along the sunny morning sidewalk with a steadier stride.
(Expression, pre-baked 50%): Quiet strength.
(Environment): sidewalk in front of an apartment-complex main gate (LOC apt-gate): flower bed and low wall, no signs, no lettering
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft natural daylight from upper-left, 5600K clean balanced tones, subtle warm rim light separating subject from background, gentle contrast
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Very slow lateral drift
- Character Motion: Slow steady walk, cart rolls smoothly, camera drifts.
```

### S43 (10s) — Long shot (rear)

```
[SCENE SPECIFICATION]
- Scene ID: S43
- Timecode: 05:05.00 - 05:15.00 (Duration: 10s)
- Audio Anchor: 자막카드 Attack 05:05.22–05:10.16 (자막: 고마움은 몰라도 된다. 그 사람은…)
- Transition Out: Dissolve 0.5s → ending card
- References: KIM@fullbody-back, LOC@guard-booth-night

[KEYFRAME GENERATION PROMPT]
(Subject): Korean man in his early 60s (reference: KIM sheet), round face, short neat salt-and-pepper crew cut, plain dark navy security-guard uniform with pristine clean collar, no badge, no name tag, no cap, worn radio on belt from behind standing at the booth doorway at dusk, quietly watching the complex, caption card space in lower third.
(Expression, pre-baked 50%): —
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, dusk
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Blue-hour dusk, cool 4800K ambient with one warm practical lamp, low-key, soft rim light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static rear shot
- Character Motion: Micro breathing, nothing else.
```

### S44 (10s) — Medium shot

```
[SCENE SPECIFICATION]
- Scene ID: S44
- Timecode: 05:15.00 - 05:25.00 (Duration: 10s)
- Audio Anchor: 자막카드 Attack 05:15.22–05:20.13 (자막: 다음 이야기 — 성탄 전야, 그가…)
- Transition Out: Fade out
- References: LOC@guard-booth-key2

[KEYFRAME GENERATION PROMPT]
(Subject): Booth windowsill with a small Christmas tree ornament just visible, winter teaser, no people, caption card space.
(Expression, pre-baked 50%): —
(Environment): small apartment security booth interior (LOC guard-booth): narrow desk with old black-and-white CCTV monitors and a thermos, window onto the flower bed, blank smooth duty board on the wall with no writing, winter
(Cinematography): 35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, rule of thirds; Photorealistic live-action, Arri Alexa cinematic color grade, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, late-autumn Korean neighbourhood tones
(Lighting): Soft morning daylight through the booth window from upper-left, 5600K, gentle contrast, dust motes in the light
(Negative Prompt): gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography, text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps, symbols on collar, bad anatomy, deformed eyes, extra fingers, cap, hat, badge, nametag

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video (approved keyframe only)
- Camera Motion: Static, locked off
- Character Motion: Static plate, faint light flicker on the ornament.
```

## 3-3. PHASE 4·5 실행 계획 (PASS 후)

- PHASE 4 키프레임: 장면당 1장, `fal-ai/nano-banana/edit`에 캐릭터 시트+로케이션 셀을 멀티 참조로 넣어 생성. 스펙은 `scripts/build_ep3_keyframes.py`가 이 Lock 데이터에서 자동 생성(`scripts/portraits/ep3-keyframes.json` 44장, 파일럿 `ep3-keyframes-pilot.json` 3장). 실행은 `generate-video.yml portraits_spec=…` → `assets/portraits/<spec>/sNN-1.png`. Kill Gate(외계어·손가락·눈동자·그리드 출력) 통과분만 Lock, 불합격은 `portraits_regen_ids`로 부분 재생성.
- PHASE 5 모션: `generate_video.py`에 키프레임 입력(Image-to-Video, Seedance image-to-video) 모드를 추가해 승인 키프레임만 변환. Text-to-Video 사용 금지.
- 비용 보고: PHASE 4·5 각각 실행 전에 장면 수·예상 비용을 보고하고 승인을 받는다.
