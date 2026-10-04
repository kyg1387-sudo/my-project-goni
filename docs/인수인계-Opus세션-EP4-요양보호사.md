# 인수인계: Opus 5.5 세션 → EP4 「김씨의 크리스마스」 + 요양보호사(수천억 상속자) 편

작성 2026-10-03 (Fable 세션, 한도 88% 시점). Fable 한도 재설정 10-06(화) 20:00까지 Opus 세션이 이 문서로 작업을 이어받는다.

## 0. 먼저 읽을 것 (순서대로, 전부)
1. `CLAUDE.md` — 제1~6장 전부. **제6장(EP3 실증 보강 규격)이 EP4부터 적용되는 핵심 규칙**이다.
2. `docs/제작규격-보강-EP3실증.md` — 제6장의 근거·도구·실패 사례.
3. `docs/EP3-인수인계.md`, `docs/EP3-일본어판-인수인계.md` — 워크플로 호출법·캐시·run ID·패치 절차의 실례.
4. `docs/시리즈-제작비용.md` — 비용 대장. **유료 실행 전 규모·비용 보고 → 사용자 승인** 후 실행.
5. `docs/기획안-김씨시리즈.md` — EP4~EP6 줄거리(아래 §3에 EP4 요약).
6. 참고: `docs/EP3-PHASE1~5*.md`(단계별 산출물 예시), `docs/영화제작규칙집.md`(Seedance 프롬프트 문법), 스킬 `goni-skill`.

## 1. 운영 원칙 (위반 금지)
- **한 브랜치 한 세션.** Opus 세션은 자기 브랜치에서만 작업한다. 시작은 `origin/claude/zen-cori-8ren7o`(EP3 전 산출물·규격 포함, 최신)에서 분기:
  `git fetch origin claude/zen-cori-8ren7o && git checkout -B <opus-branch> origin/claude/zen-cori-8ren7o`.
  Fable이 복귀하면 Opus 브랜치를 가져와 이어간다(Opus 브랜치 이름을 이 문서 §6에 기록할 것).
- API 키는 GitHub Secrets에만. 코드·채팅·문서에 쓰지 않는다.
- 유료(fal·ElevenLabs·Typecast) 실행 전 장면 수·예상 달러를 보고하고 승인받는다. fal 잔액은 사용자가 캡처로 알려준다(2026-10-03 기준 30.18달러).
- bot 커밋(워크플로 "완성 영상 추가")이 올라오면 `git pull --rebase` 후 작업.
- 수정 요청은 번호 목록으로 관리하고 매 보고에 상태(완료/진행/대기)를 갱신한다.
- 전달: 파일 전송 한도 약 30MB → 480p 미리보기 + 원본 28MB 분할(`split -b 28m -d`). 저장소 deliveries는 90MB 분할.
- 사용자 지적은 0.25~0.5초 간격 크롭 시트로 재현해 원인을 기록한 뒤 고친다.

## 2. 파이프라인 요약 (PHASE 1~6, CLAUDE.md 제1장)
| 단계 | 산출물 | 도구/워크플로 | 비용 |
|---|---|---|---|
| 1 대본 동결·오디오 앵커 | `docs/대본-EPn.md`, `subs/<skit>.ass`, TTS 42~48줄 | `burn-subtitles.yml`(add_audio) 또는 오디션 `generate-video.yml` audition_spec | TTS 글자수 |
| 2 마스터 에셋 | 캐릭터 시트(정면·45도·측면·전신·표정3) + 셀, 로케이션 시트 | `generate-video.yml` portraits_spec (`scripts/portraits/*.json`) | 시트당 약 0.1~0.2 |
| 3 샷 리스트 | `scripts/storyboard/<skit>.json`, `scripts/scenes/<skit>.json`, `scripts/audio/<skit>.json` | 로컬 작성 | 0 |
| 4 키프레임 | `assets/portraits/<ep>-keyframes/sNN-1.png` + Kill Gate 검수 | portraits_spec (i2i, 시트 셀 참조) | 장당 약 0.05~0.1 |
| 5 모션·립싱크 | i2v 클립(Seedance lite), omnihuman 대사 장면 | `generate-video.yml`(skit) → `burn-subtitles.yml`(lipsync=true) | 클립 0.3~0.5, omni 장면 약 0.4 |
| 6 마스터링 | 현장음(mmaudio)·BGM(lyria2)·믹스·아웃트로·엔드카드 | burn 내부 + `scripts/append_outro.py` | BGM 구간당 소액 |

EP3 실측: 한국어판 약 37달러(44장면), 일본어 더빙판 약 5달러. EP4 예산도 같은 규모로 잡는다.

## 3. EP4 「김씨의 크리스마스」 — 착수 상태: **기획만 확정, 대본 미작성**
줄거리(기획안): 성탄 전야, 관리비 미납으로 전기가 끊길 위기인 1801호 모자 가정. 아이 "산타는 우리 집을 모르나 봐". 김씨가 월급 봉투를 연다. 성탄 아침 현관 앞 작은 트리와 장난감, 관리사무소 "미납금 완납" 통지. 아이 엄마가 CCTV를 돌려보다 눈물. 엔딩 「산타는 굴뚝이 아니라, 경비실에서 온다」.

작업 순서(EP3과 동일):
1. 대본 `docs/대본-EP4-김씨의크리스마스.md` — 5분 내외, 44장면 전후, 내레이션 1.2배속 기준. EP3 톤연출표(`docs/톤연출표-EP3-김씨와폐지할머니.md`) 양식으로 톤표 작성. **사용자 승인 후 동결.**
2. 시트: 김씨는 **시리즈 공통 시트 재사용**(`assets/portraits/ep3-cast/kim-sheet-1.png`, 셀 `cells/kim-front.png`, `kim-expr-neutral.png`). 신규 인물(아이 엄마·아이·관리사무소 직원)만 생성. 주연·조연은 머리·수염·의상 명도 중 2가지 이상 다르게(제6장 2).
   로케이션: 경비실·아파트 정문은 `ep3-cast/cells/loc-guard-booth-*.png`, `loc-apt-gate-*.png` 재사용(야간 셀 있음). 신규: 1801호 현관·거실, 관리사무소.
3. 목소리: 김씨 ElevenLabs `8vwSOQHQApfVx993mKf9`, 내레이터·아웃트로 ElevenLabs `5n5gqmaQi9Ewevrz7bOS`. 아이 엄마·아이는 오디션(`scripts/auditions/*.json` 양식, `audition_spec`) 후 사용자 선택.
4. 스킷 id 제안: `kim-christmas`. 설정 파일은 `scripts/scenes/kim-cart-grandma.json`, `scripts/audio/kim-cart-grandma.json`, `scripts/storyboard/kim-cart-grandma.json`을 복사해 수정.
5. 엔딩은 시리즈 공통: `scripts/append_outro.py`(기본 OUTRO/ENDCARD = 한국어 아웃트로·엔드카드). 일본어판은 `OUTRO=assets/auditions/outro-host/OUTRO-SCENE-ja.mp4 ENDCARD=assets/brand/endcard-midam-ja.mp4`.
6. 썸네일·쇼츠·업로드 가이드는 EP3 산출물(`assets/thumbnails/ep3/`, `assets/shorts/ep3/`, `docs/업로드가이드-김씨와폐지할머니.md`, `docs/EP3-日本語版-アップロード.md`)을 양식으로.

## 4. 요양보호사(수천억 상속자) 편 — 착수 상태: **Sonnet 브랜치에 조립본까지 있음, 립싱크 결함 재작업 중**
- 브랜치 `claude/busy-mayer-0zm6hj`(head 3ce5d8d, 206파일 변경). 스킷 id **`참교육사이다`**, 인물 회장·서미령 등, 음성 파일 예 `seohoejang_2_s06.mp3`.
- 최근 커밋 흐름: 완성 영상 추가 → 서미령 립싱크 패치 → 회장 얼굴 일그러짐 수정(4:01 부근, 머리 움직임 중 립싱크 아티팩트) → burn에 `scenes_from_repo` 옵션 추가(slice_source 드리프트 버그 우회) → "11개 장면 립싱크 재작업(균등분할 드리프트 버그 수정 후)".
- 즉 그 세션은 **영상 위 립싱크 덧씌우기(lip 모드)** 방식이었고, CLAUDE.md 제6장 1(대사 장면은 정지 키프레임 → 음성 구동 OmniHuman)과 다르다. 반복되는 일그러짐의 근본 원인이 이것이므로, 결함 장면은 제6장 방식(omnihuman_scenes 지정 + 가슴 위 CU 키프레임)으로 재생성하는 것을 1순위로 검토한다.
- 그 브랜치의 워크플로 변경(`scenes_from_repo`)이 `claude/zen-cori-8ren7o`의 `source_skit` 변경과 충돌할 수 있다 → 두 브랜치의 `.github/workflows/burn-subtitles.yml`을 비교해 병합한다.
- 조사 명령:
  `git fetch origin claude/busy-mayer-0zm6hj && git log --oneline origin/claude/busy-mayer-0zm6hj -20 && git diff --stat origin/main...origin/claude/busy-mayer-0zm6hj`.
- 사용자에게 **오류 내용과 어디까지 됐는지**를 먼저 물어 진단서를 작성한 뒤 이어간다(사용자가 "브랜치·오류 전달" 예정).
- 그 산출물이 CLAUDE.md 제6장 기준(대사 장면 음성 구동, 인물 대조, 여운, 사운드)을 지키지 않았으면 해당 단계부터 다시 한다. 이미 생성된 클립은 캐시(Artifact run ID)로 재사용해 비용을 아낀다.
- 이 편은 김씨 시리즈가 아니므로 시트·목소리를 새로 만든다(채널 공통 엔딩만 재사용).

## 5. 자주 걸리는 함정 (EP3에서 실제로 겪은 것)
- burn 워크플로에서 클립을 다른 스킷과 공유하면 `source_skit` 입력 필수(Artifact 이름 불일치). 단일 장면 스킷은 concat 목록을 basename으로.
- `bgmNN.audio`(BGM 구간 파일)는 Artifact에 저장되지 않는다 → `lipsync=remix`로 재조합하면 BGM 4곡이 전부 새로 생성된다(승인된 음악이 바뀜). 오디오 소수정은 로컬 ffmpeg로 처리하는 편이 안전.
- 음성 구동 립싱크(OmniHuman)가 첫 2초 또는 꼬리에서 헤드턴을 만들면 정지 클립으로 교체(`still_pushin_clip.py`, xfade에는 `settb=1/24` 필요).
- 재잠금 `retime_transitions.py`는 **반드시 원본/기준 .ass에서 다시 시작**(이중 압축 방지). 옵션 `--gap 0.5 --tail 1.0 --narration-tempo 1.2 --trim --anchor`.
- −60dB 이하 2초 무음 금지: 대사가 일찍 끝나는 장면은 BGM 구간 경계를 확인(일본어판 S31 사례). 검수는 `silencedetect=n=-60dB:d=1.5`.
- "quiet/tense" 현장음 프롬프트는 웅얼거림(외국어 음성)을 만든다 → 사람 있는 장면 현장음 ''.
- libass는 일본어 자막 자동 줄바꿈을 못 한다 → 쇼츠 등 재자막 시 `\N` 수동 삽입(19자 기준, 구두점에서 분리).
- faster-whisper 로컬 다운로드 불가(프록시) → 언어 검사는 `qa-language.yml`.
- 파일 전송은 30MB 한도. Windows 합치기는 `copy /b` (다운로드 폴더로 cd 후).
- 표정 교체는 편집(edit)이 아니라 시트 표정 셀 참조 또는 신규 생성으로(편집은 원본과 거의 같게 나옴).

## 6. Opus 세션이 채울 칸
- Opus 브랜치 이름: `claude/nice-tesla-izknnf` (2026-10-03, `origin/claude/zen-cori-8ren7o` 8db20cc에서 분기)
- EP4 대본 v3 **승인·동결 2026-10-03** — `docs/대본-EP4-김씨의크리스마스.md`, `docs/톤연출표-EP4-김씨의크리스마스.md`, 시트 스펙 `scripts/portraits/ep4-cast.json`(미실행). 보이스 스펙 `scripts/auditions/kim-christmas-tts.json`(30줄)·`kim-christmas-voices.json`·`kim-christmas-child.json`
- EP4 오디오 진행(2026-10-03): **일본어 기준 제작으로 결정**(사용자). 일본어 내레이터 26+김씨 4줄 `assets/auditions/kim-christmas-ja-tts/`(읽기 위험 11줄 가나 입력 재생성, 구판 `_superseded/`), 엄마 후보 4·아이(+2/+3반음) `assets/auditions/kim-christmas-ja-voices/` → **사용자 청취·선택 대기**. 한국어판 30줄 `assets/auditions/kim-christmas-tts/`(한국어판용 보관).
  언어 검사: `generate-video.yml`에 `qa_model`·`qa_lang` 입력 추가(일본어는 large-v3·ja). EP3-JA 승인본도 같은 수준으로 오인식됨 → EL 내레이터·김씨의 일본어는 한국어 억양이 기준선. 일본어 원어민 내레이터 교체안은 사용자 판단 대기.
  ElevenLabs API 키에 voices_read 권한 없음(도서관 검색·이름 조회 불가, ID 직접 지정은 가능).
- EP4 진행(2026-10-04): PHASE 2 Lock(사용자 「승인」, 관리사무소 v2-1 일본어 교체본 최종). PHASE 3 초안 `docs/EP4-PHASE3-샷리스트.md`(생성기 `scripts/build_ep4_phase3.py`, 54컷·05:01.20·디졸브 10·카드 8). 아웃트로 `outro-ja-ep4`(25초, 진행자 Typecast `tc_629fe972013e90b4db213fd8`, 버튼·로고 `scripts/outro_cta_overlay.py`): generate run 37175515279 → burn run 37175761153(OmniHuman 25초 1회 과금) → **불합격**: 연속 25초 생성에서 얼굴이 점점 달라지고 고개 기울기 큼(`deliveries/outro-ja-ep4-skit-final.mp4`). 교훈: OmniHuman은 7초 이하로 끊고, 가슴 위 CU 키프레임(제6장 1)을 아웃트로에도 적용.
- EP4 아웃트로 v2(2026-10-04, 사용자 「재제작 + 빠이빠이 승인」): 28.0초 = 0~9.75 트리 불빛 몽타주(인사·여운 멘트 목소리만) → 9.75~17.12 진행자 CU 구독 요청(OmniHuman, 「高評価」12.2s·「チャンネル登録」13.0s 버튼, 15.9s 퇴장) → 17.12~24.10 허리 위 다음 화 예고·인사(OmniHuman) → 24.10~28.0 손 흔들기(i2v, 손가락 Kill Gate 합격). 좌상단 로고 「美談ものがたり」. 유튜브 최종 화면 요소 자리 18~28s(오른쪽 2/3). v2 1차에서 1구간(3.5s) OmniHuman도 1.5s부터 얼굴 변화 → 몽타주로 교체(무과금). 최종본 `assets/auditions/outro-host/OUTRO-SCENE-ja-ep4.mp4`(버튼·로고 합성, `scripts/outro_cta_overlay.py`), 원본 burn run 37179075281(캐시 재사용, 무과금).
- EP4 아웃트로 도입부 교체 결정(사용자 A안, 2026-10-04): 0~9.75s 트리 몽타주 → 본편 하이라이트 4컷(S38·S41·S50·S52, 디졸브)으로 PHASE 5 후 교체(무과금, `scripts/scenes/outro-ja-ep4.json` `_교체예정`).
- EP4 품질 파일럿 키프레임(2026-10-04): S36·S41(레터박스 크롭)·S50(재생성, 벽 메모지 지움) Kill Gate 합격 → `assets/portraits/ep4-keyframes/`. 다음: i2v lite vs pro 비교·S50 OmniHuman(짧게).
- EP4 PHASE 4·5·6(2026-10-04): 키프레임 51장 Kill Gate(이미지 69장) → i2v 39컷 run 37182807944(인물 22 pro·무인 17 lite) → 불합격 7컷 정지 푸시인·일본어 글자 8컷 합성·S44 얼굴 그늘 → burn(OmniHuman 7) → 조립 끊김(117s) 수정(frame_quantize) → BGM 정적·S52 줌아웃 → 인물 대조로 S45 엄마 얼굴 교체. **교훈 전부 `docs/제작규격-보강-EP4실증.md`·CLAUDE.md 제7장에 반영(사용자 지시)**.
- EP4 대본 승인일 / 시트 run ID / 키프레임 run ID / 클립 run ID / burn run ID: ______
- 요양보호사 편 진단서 위치: ______
- 지출(잔액 변동): ______ (대장 `docs/시리즈-제작비용.md`에 기입)

## 7. 전수 검수 절차 (조립본마다, CLAUDE.md 제6장 7)
1. 길이 `ffprobe`, 2. 전환 콘택트시트(각 전환 −0.5/−0.1/+0.3s), 3. 대사 장면 0.5s 입 크롭, 4. 인물 시트 정면 셀 대조, 5. 재생성 컷 1초 간격, 6. 음량 윈도(ebur128 + silencedetect −60dB 1.5s), 7. 사용자 지적 재현 시트.
한 항목이라도 불합격이면 전달하지 않는다.
