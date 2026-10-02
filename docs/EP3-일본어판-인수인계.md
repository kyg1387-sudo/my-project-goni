# EP3 일본어 더빙판 인수인계 (2026-10-02, Fable 세션 → 다음 세션)

**읽는 법**: CLAUDE.md(제6장 포함)와 `docs/제작규격-보강-EP3실증.md`를 먼저 적용한다. 이 문서는 "어디까지 됐고, 다음에 무엇을 하는지"만 적는다.
**원칙**: 한 브랜치(`claude/zen-cori-8ren7o`)에 한 세션만. 유료 실행 전 비용 보고·승인. bot 커밋이 올라오면 `git pull --rebase`.

## 0. 한국어판 EP3 (완료, 업로드 대기)
- 최종본 `deliveries/kim-cart-grandma-final-outro.mp4.part-00/01` (합치면 306.2s), 쇼츠 5종 `assets/shorts/`, 썸네일 `assets/thumbnails/`, 업로드 가이드 `docs/업로드가이드-김씨와폐지할머니.md`.
- 한국어판 클립 Artifact: generate run **36971579705** (`kim-cart-grandma-skit-video`). 캐시(현장음·BGM·omni) Artifact: burn run **36966874332** (`kim-cart-grandma-skit-video-subbed`).

## 1. 일본어판 스킷 `kim-cart-grandma-ja` — 현재 상태
| 항목 | 상태 | 위치 |
|---|---|---|
| 각색 대본(시니어 드라마체) | 완료 | `docs/EP3-일본어대본.md` |
| 일본어 자막 .ass (재잠금 적용본) | 완료 | `subs/kim-cart-grandma-ja.ass` (재잠금 기준 원본: `subs/kim-cart-grandma-ja.base.ass`) |
| 일본어 음성 42줄 | 완료 | `assets/audio-overrides/kim-cart-grandma-ja/lineNNN.mp3` (원본 `_orig/`, 1.12배 적용본이 본 파일) |
| 목소리 | 확정 | 내레이터 EL `5n5gqmaQi9Ewevrz7bOS`, 김씨 EL `8vwSOQHQApfVx993mKf9` (eleven_multilingual_v2), 최사장 Typecast `tc_69a8e49d2e36ab42260be475` tonedown 1.2, 할머니 Typecast `tc_61d55a84b8c48f42d69b2399` sad 1.0 tempo 0.9 |
| 오디오 설정 | 완료 | `scripts/audio/kim-cart-grandma-ja.json` (scene_durations: S02 5, S15 5, S20 5, S28 10, S31 9; transitions; bgm 4구간; omnihuman_scenes [1,15,28,29,31,36]) |
| 타임라인 | 확정 294.2s | 재잠금 명령은 §3 |
| **조립(립싱크 6장면 + 믹스)** | **실행 중/완료 확인 필요** | burn run: skit=kim-cart-grandma-ja, source_skit=kim-cart-grandma, source_run_id=36971579705, resume_run_id=36966874332, invalidate=`omni*.mp4 omniframe*.png lip*.mp4 line*.mp3 seg*.wav`. 완료 시 bot 커밋 "완성 영상 추가 (kim-cart-grandma-ja)" → `deliveries/kim-cart-grandma-ja-skit-final.mp4(.part-*)` |
| 아웃트로 일본어 멘트 TTS | 실행 중 | audition_spec=outro-ja → `assets/auditions/outro-ja/outro_ja.mp3` |
| 아웃트로 입모양 재생성 | 미착수 | §4 |
| 일본어 엔드카드 | 완료 | `assets/brand/endcard-midam-ja.mp4` |
| 썸네일·메타데이터(일본어) | 완료 | `assets/thumbnails/ep3/*-JP.jpg`, `docs/EP3-업로드-최종.md` |

## 2. 다음 작업 순서
1. **조립 결과 수거·검수** (한도 소모 큼 → 최소판)
   ```
   git pull --rebase origin claude/zen-cori-8ren7o
   cat deliveries/kim-cart-grandma-ja-skit-final.mp4.part-* > /tmp/ja.mp4   # 분할이 아니면 그 파일 그대로
   ffprobe -show_entries format=duration /tmp/ja.mp4   # 294.2 ±0.1
   ```
   - 대사 6장면(S01·S15·S28·S29·S31·S36) 입 크롭 0.5초 간격 1장(헤드턴·번짐), 전환 콘택트시트 1장, 음량 윈도(무음 −60dB 이하 2초 금지).
   - **S29 헤드턴 재발 시**: 한국어판과 같은 로컬 패치(정지 리드 2.05s + 0.2s 디졸브, 세션 기록의 ffmpeg 필터) — 재생성보다 우선.
   - 자막 길이·음성 어긋남이 보이면 §3 재잠금 후 `lipsync=remix`가 아니라 **omni 재생성 필요**(대사 오프셋이 바뀌면). 내레이션만 바뀌면 remix(무과금).
2. **아웃트로 일본어판** (§4) → 3. **결합·전달** (§5) → 4. 업로드 가이드(일본 채널)는 `docs/EP3-업로드-최종.md`의 다국어 절 + 일본어 메타.

## 3. 타임라인 재잠금 명령 (수정이 생기면)
```
cp subs/kim-cart-grandma-ja.base.ass subs/kim-cart-grandma-ja.ass     # 반드시 기준본에서 시작(이중 압축 방지)
python3 scripts/retime_transitions.py --skit kim-cart-grandma-ja --narration-tempo 1.12 --gap 0.5 --tail 1.0 \
  --trim 2=5,15=5,20=5,28=10,31=9 \
  --anchor "1=1@0.8,2=1@4.4,15=15@1.7,18=20,19=21,20=22,21=23,22=24,24=25,26=26,27=27,31=28@3.0,33=29@1.0,34=29@4.9,37=35@0.3,38=36@0.8,41=41" --apply
```
- 대사 줄의 장면 내 오프셋이 바뀌면 해당 장면 omni 재생성(invalidate omniNN.mp4 omniframeNN.png).
- 기준본(.base.ass)은 "01402eb 잠금 타이밍 + 일본어 음성 실제 길이"로 만든 것. 음성을 다시 만들면 `durations.json`을 갱신하고 base를 다시 생성해야 한다(세션 기록 스크립트 참조).

## 4. 아웃트로 일본어판 만드는 법 (약 1달러)
1. `assets/auditions/outro-ja/outro_ja.mp3` 확인(길이 L초).
2. 미니 스킷 `outro-ja`: `ffmpeg -ss 0.2 -i assets/auditions/outro-host/OUTRO-SCENE.mp4 -frames:v 1 assets/portraits/outro-host.png` 로 진행자 정지 프레임 추출 →
   `scripts/scenes/outro-ja.json` {ratio 16:9, durations [ceil(L)+1], scenes [{prompt:"static, subtle breathing", image:"assets/portraits/outro-host.png", duration: ceil(L)+1}]},
   `assets/video-overrides/outro-ja/scene01.mp4` = `still_pushin_clip.py assets/portraits/outro-host.png ... (ceil(L)+1)`,
   `scripts/audio/outro-ja.json` = kim-cart-grandma-ja.json 복사 후 scene_durations [ceil(L)+1], transitions [0], omnihuman_scenes [1], lipsync_skip_scenes [], ambience_prompts [""], bgm_segments [],
   `subs/outro-ja.ass` = 스타일은 ja.ass 복사, Dialogue 1줄(Host 스타일=Kim 스타일 복제, 0.3s~0.3+L) 텍스트 = 멘트, 자막은 표시해도 됨.
   `assets/audio-overrides/outro-ja/line001.mp3` = outro_ja.mp3 복사.
3. generate-video.yml skit=outro-ja (오버라이드 적용, fal 호출 없음) → burn-subtitles.yml skit=outro-ja, source_run_id=<위 run>, add_audio=true, lipsync=true.
4. 결과 `deliveries/outro-ja-skit-final.mp4`를 `assets/auditions/outro-host/OUTRO-SCENE-ja.mp4`로 복사.

## 5. 결합·전달
- `scripts/append_outro.py`의 `outro`/`endcard` 경로를 일본어 파일로 바꾼 사본(또는 인자화)으로 실행: 본편 1.0s 페이드아웃 → 검은 화면 0.8s → 일본어 아웃트로 → 0.6s 크로스페이드 → `assets/brand/endcard-midam-ja.mp4`.
- 전달: 480p 미리보기(≤30MB) + 원본 28MB 분할 4조각. 저장소에는 90MB 분할로 `deliveries/kim-cart-grandma-ja-final-outro.mp4.part-*`.
- 비용 대장 `docs/시리즈-제작비용.md`에 일본어판 행 추가(예상 fal 약 5달러).

## 6. 알려진 주의점
- 조립 시 `source_skit`이 없으면 Artifact 이름 불일치로 클립을 못 찾는다(워크플로 입력 필수).
- 일본어 음성 1.12배는 `_orig/`에서 atempo로 만든 것. 더 느리게 원하면 §3 명령의 tempo만 바꾸고 재잠금 → 대사 오프셋 변화 확인 → 필요 시 omni 재생성.
- Typecast 할머니 음성 line012 길이 1.9s: S15 창(5s) 안.
