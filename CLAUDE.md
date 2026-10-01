# 시네마틱 AI 영상 제작 표준 운영 규격서

**문서 목적**: 생성형 AI 특유의 인위적인 이질감('AI 티')을 전면 배제하고, 전문 영화감독의
연출 문법과 탑티어 유튜브 PD의 편집 리듬을 결합하여 오차율 0% 및 일관된 시네마틱 퀄리티를
구현하는 표준 제작 규격서.

**적용 원칙 (사용자 확정, 2026-10-01)**: 앞으로 모든 작업은 이 규격서의 단계(PHASE 1~6)와
규칙을 시스템 프롬프트로 100% 엄수한다.

---

## 제1장. 불변의 6단계 제작 파이프라인 (Locked Pipeline)

**원칙**: 선행 단계가 승인되어 '고정(Lock)'되지 않으면 절대 다음 단계의 렌더링 크레딧과
시간을 소모하지 않는다.

```
[PHASE 1] 대본 동결 & 오디오 앵커링 (Script & Voice Waveform Lock)
   ↓
[PHASE 2] 기준 마스터 에셋 고정 (Character ID & Location Asset Lock)
   ↓
[PHASE 3] 정밀 샷 리스트 & 프롬프트 설계 (Storyboard & Transition Lock)
   ↓
[PHASE 4] 키프레임 스틸 렌더링 & 결함 1차 필터링 (Artifact & Text Kill Gate)
   ↓
[PHASE 5] 제어된 모션 & 정밀 립싱크 합성 (Motion Control & Cut-away Cheating)
   ↓
[PHASE 6] 사운드스케이프 마스터링 & 최종 퀄리티 게이트 (Mastering & Output)
```

### PHASE 1. 대본 동결(Script Freeze) 및 오디오 앵커링

1. **대본 최종 고정 (Script Freeze)**:
   - 대본이 확정된 후 문장 구조, 어휘, 쉼표 위치까지 100% 동결한다.
     (본편 생성 착수 후 대본 수정 절대 금지)
2. **보이스(TTS/내레이션) 선행 생성**:
   - 기계적 연조를 방지하기 위해 문장 간 0.3~0.5초의 호흡 간격(Pause)을 확보한다.
3. **타임라인 오디오 배치 & 파형 기준점 마킹**:
   - 편집 타임라인에 음성 트랙을 먼저 배치한다.
   - 문장의 시작점(Attack), 강세(파열음), 감정 고조 지점, 씬 전환 지점에 마커(Marker)를
     생성하여 샷당 정확한 타임코드(초·프레임 단위)를 강제 확정한다.

### PHASE 2. 기준 마스터 에셋 고정 (Character & Environment Lock)

모든 컷은 이 단계에서 생성된 원본 에셋의 '참조 복제'여야 한다.

1. **캐릭터 마스터 시트 (Character Anchor)**:
   - 인물의 정면, 45도, 측면, 전신, 3가지 기본 표정(중립, 미소, 긴장)을 단 1회 완벽하게
     렌더링하여 Seed값 및 고정 ID(Face Reference)를 확보한다.
   - 복장과 헤어스타일의 세부 특징을 프롬프트 레벨에서 잠근다.
2. **로케이션 마스터 시트 (Location Anchor)**:
   - 인물이 배제된 순수 배경 공간을 35mm 표준 화각으로 렌더링하여 보관한다.
   - 시간대, 광원의 방향(Key Light 위치), 색온도(3200K/5600K)를 영구 고정한다.
3. **공통 스타일 프리셋 잠금**:
   - 카메라 기종 모사, 필름 그레인, 조명 스타일 태그를 공통 템플릿화하여 모든 프롬프트에
     동일하게 주입한다.

### PHASE 3. 정밀 샷 리스트 및 연출 설계 (Storyboard Lock)

생성 전, 씬별 세부 연출 스펙을 표준 규격 테이블에 작성한다.

| 항목 | 규격 작성 기준 |
|---|---|
| 타임코드 & 듀레이션 | 예: 00:03.12 ~ 00:06.24 (3초 12프레임) |
| 오디오 파형 & 대사 | 시작 파형과 끝 파형의 위치, 핵심 키워드 |
| 샷 사이즈 & 렌즈 | Extreme Close-up / Close-up (85mm) / Medium (50mm) / Wide (24mm) |
| 조명 설계 | Chiaroscuro, Rembrandt, Golden Hour Rim Light, Backlit 등 |
| 카메라 무빙 | Slow push-in, Subtle handheld sway, Static (극미세 모션만 허용) |
| 전환 기법 | Match Cut, J-Cut(사운드 선행 0.5초), B-roll Cut-away |
| 참조 에셋 | Character Sheet ID + Location Sheet ID 결합 호출 |

### PHASE 4. 키프레임 스틸 렌더링 & 결함 1차 필터링

1. **Image-to-Image / Multi-Reference 렌더링**:
   - 승인된 캐릭터 시트와 배경 시트를 결합해 정지 화면(Keyframe)을 생성한다.
2. **1차 결함 검수 (Kill Gate)**:
   - 외계어 텍스트(옷깃, 명패, 배경 간판), 손가락 관절 왜곡, 양쪽 눈동자 비대칭 여부를
     스틸 단계에서 확인한다.
   - 결함 발견 시 인페인팅(Inpainting)으로 제거하거나, 크롭(Crop) 또는 즉시 재생성한다.
     (비디오 생성 전 차단)

### PHASE 5. 제어된 모션 렌더링 & 정밀 립싱크 (Motion & Sync)

1. **Image-to-Video 원칙 (Text-to-Video 전면 금지)**:
   - 승인된 키프레임만 비디오 변환을 진행하며, 컷 길이는 3~4초 내외로 제한한다.
   - 급격한 회전(Spin), 달리기 등 과도한 모션 명령을 금지하고 시선 이동, 미세 호흡,
     카메라 패닝 위주로 구동한다.
2. **오디오 파형 맞춤 립싱크**:
   - PHASE 1 오디오 트랙과 립싱크 툴을 연동하여 렌더링한다.
   - 파형의 파열음(ㅂ, ㅍ, ㅁ 계열)과 입술의 개폐를 1프레임 단위로 동기화한다.
3. **타임 스트레치(Time Stretch) 미세 보정**:
   - 오디오 속도와 입술 움직임의 오차가 생길 경우, Optical Flow 모드로 비디오 트랙을
     95%~105% 범위 내에서 스트레치하여 맞춘다.
4. **컷어웨이(Cut-away) 치팅 적용 (필수)**:
   - 인물이 말하는 씬이 4초를 초과할 경우:
     **말하는 얼굴(Talking face) → B-roll 인서트(Cut-away) → 리액션 클로즈업**
     으로 교차 편집하여 립싱크 연산 오류 노출을 원천 방지한다.

### PHASE 6. 사운드스케이프 마스터링 & 최종 퀄리티 게이트

1. **사운드스케이프 3중 레이어링**:
   - Voice(TTS): 100% 명료도 유지.
   - Ambience(공간 앰비언스): 방의 공조기 소음, 빗소리, 바람 소리 등을 깔아 인공적
     적막감 제거.
   - BGM: 내레이션 대역(1kHz~3kHz)을 EQ로 감쇄(-3dB~-5dB)하여 목소리와의 주파수 충돌
     방지.
2. **J-Cut 사운드 선행 편집**:
   - 씬이 전환되기 0.5초 전에 다음 장면의 핵심 사운드(효과음, 앰비언스, 대사 첫마디)를
     먼저 유입시켜 뇌의 인지 전환을 부드럽게 유도한다.
3. **얼굴 복구(Face Restoration) 전수 검사**:
   - 모션 중 눈·코·입의 윤곽선 흐려짐이 발생한 클립은 CodeFormer/Face Restoration
     업스케일러를 통과시켜 칼같은 해상도를 복구한 뒤 최종 마스터 렌더링을 진행한다.

---

## 제2장. 3대 고질적 결함(외계어·립싱크·얼굴 일그러짐) 0% 제어 규격

### 1. 외국어 텍스트 및 의미불명 기호 원천 박멸 규격

- **공통 네거티브 프롬프트 필수 주입**:
  ```
  gibberish, foreign text, incomprehensible letters, fake alphabets, blurry typography,
  text on badge, text on name tag, logo on shirt, signage lettering, watermarks, stamps,
  symbols on collar
  ```
- **명찰/명판 대체 프롬프트**:
  - 명찰을 달지 않거나, 텍스트가 없는 순수 금속/단색 패브릭으로 묘사한다.
  - `plain clean uniform without any badge or patch, nameless suit, pristine clean lapel,
    blank golden brass plaque on desk with no engraving`
- **광학적 흐림(Bokeh) 및 크롭 회피**:
  - 배경에 글자가 생길 우려가 있는 경우, 조리개 값을 f/1.4~f/1.8로 설정
    (`creamy background bokeh, shallow depth of field`)하여 배경 문자를 완전히 흐리게
    처리한다.

### 2. 정밀 립싱크 동기화 및 연출 치팅

- **오디오 파형(Waveform) 정렬 기준**:
  - 나레이션 음성의 파형 첫 진폭 상승점(Attack)과 입술이 벌어지는 프레임을 오차
    0~1프레임 이내로 일치시킨다.
- **치아 및 구강 구조 왜곡 방지**:
  - 립싱크 렌더링 시 치아가 하나로 붙어 나오거나 구강 내부가 뭉개지는 현상이 발생하면,
    즉시 해당 구간을 컷어웨이(B-roll 인서트)로 가린다.

### 3. 얼굴 일그러짐(Morphing) 방지 규격

- **헤드 턴(Head Turn) 각도 제한**:
  - 인물의 고개 회전은 최대 15도~20도 이내로 제한한다. (90도 측면 회전 모션 명령 절대 금지)
- **표정 중립화(Pre-Expression)**:
  - 무표정 상태에서 비디오 툴에 '웃음'이나 '분노'를 지시하지 않는다. 키프레임 이미지
    자체에 이미 해당 감정이 50% 반영된 상태로 생성한 뒤 미세한 모션만 부여한다.
- **모션 프롬프트 승인/금지 목록**:
  - 승인: `subtle eye blink, micro chest breathing, gentle focal adjustment, slow cinematic push-in`
  - 금지: `fast walking, running, dynamic spinning, dramatic body movement, rapid facial expression shift`

---

## 제3장. 카메라 촬영 기법 & 조명 & 오디오 시네마틱 연출 규격

### 1. 카메라 광학 및 렌즈 설정 (Cinematography)

- **인물 감정 클로즈업 (Emotional Impact)**:
  `85mm prime lens, f/1.8, shallow depth of field, razor-sharp focus on the irises, soft
  optical bokeh, cinematic portrait`
- **상황 제시 및 스토리텔링 (Context/Environment)**:
  `35mm lens, f/4.0, eye-level cinematic shot, environmental storytelling, perfectly
  balanced composition, rule of thirds`
- **압도적 스케일 및 긴장감 (Grandeur/Tension)**:
  `24mm wide angle, low-angle shot, deep focus, sharp architectural lines, imposing perspective`

### 2. 입체적 조명 설계 (Lighting Design)

- **명암 대비 연출**:
  플랫한 조명(Flat Lighting)을 전면 배제하고, `Chiaroscuro lighting, dramatic high-contrast
  shadows, deep cinematic mood`를 적용한다.
- **빛의 분리감(Rim Lighting)**:
  인물과 배경이 달라붙지 않도록 피사체 외곽선에 빛을 입힌다.
  `Subtle warm rim light separating subject from dark background, cinematic volumetric side light`
- **색온도 기준**:
  - 감정적·과거 회상: `Warm amber tones, 3200K tungsten feel`
  - 냉철·현대·정보 분석: `Cool crisp daylight, 5600K clean balanced tones`

### 3. 무결점 장면 전환 (Transitions)

1. **매치 컷 (Match Cut)**: 이전 씬 피사체의 시선/중심 구도와 다음 씬 피사체의 구도를
   완벽히 일치시켜 컷 전환 충격을 상쇄한다.
2. **사운드 선행 J-Cut**: 비디오 컷보다 오디오(환경음/효과음/첫마디)를 0.5초 앞당겨
   배치하여 뇌가 장면 변화를 자연스럽게 수용하도록 한다.
3. **모션 블러 패스 (Whip/Motion Cut)**: 카메라 이동 방향(좌→우)을 연속된 두 샷에서
   일치시켜 자연스러운 속도감을 형성한다.

---

## 제4장. 최종 송출 전 무결점 검증 체크리스트 (Quality Gate)

아래 항목 중 단 하나라도 '불합격' 판정 시 해당 클립은 최종 타임라인에 삽입할 수 없다.

| 검증 영역 | 체크 항목 | 검증 기준 (Pass Criteria) | 상태 |
|---|---|---|---|
| 안면/시선 | 안구 초점 및 시선 일치 | 양쪽 눈동자의 초점이 명확하며 시선 방향이 어색하지 않은가? | PASS |
| 신체/말단 | 손가락 및 관절 형태 | 손가락 개수 5개, 관절 꺾임 왜곡이 일절 없는가? | PASS |
| 텍스트/기호 | 옷깃, 명찰, 배경 글자 | 의도치 않은 외계어 문자, 변형된 폰트, 불필요한 마크가 0%인가? | PASS |
| 모션 왜곡 | 프레임 간 사물 붕괴 | 움직이는 도중 턱선, 귀, 배경 사물이 녹아내리거나 증식하지 않는가? | PASS |
| 립싱크 정밀도 | 음성 파형과 입술 타이밍 | 파열음 시작점과 입술 개폐 오차가 1프레임 이내인가? | PASS |
| 오디오 믹싱 | 주파수 간섭 및 앰비언스 | TTS 음성이 배경음악에 묻히지 않으며(EQ 컷), 현장 앰비언스가 자연스러운가? | PASS |
| 시청 리듬감 | 3~5초 시각적 환기 | 정적인 샷이 5초 이상 지속되지 않고 인서트, 줌, 화각 전환이 배치되었는가? | PASS |

---

## 제5장. 실전 씬 프롬프트 표준 템플릿

```
[SCENE SPECIFICATION]
- Scene ID: SC_01
- Timecode: 00:00.00 - 00:03.15 (Duration: 3s 15f)
- Narration: "우리가 믿어왔던 모든 규칙이, 단 1초 만에 완전히 무너져 내렸습니다."
- Audio Waveform Anchor: 00:00.00 (TTS Attack point) / 00:02.20 (Word '무너져' emphasis)
- Transition Out: J-Cut (Next scene rain ambience leads by 0.5s)

[KEYFRAME GENERATION PROMPT]
(Subject): 40-year-old disciplined detective, intense gaze, subtle tension, perfectly
symmetrical facial features, clear irises with sharp catchlights. Wearing a plain navy
woolen coat, pristine clean collar, no badges, no nametags, no text.
(Environment): Dark minimalist office interior, rain-streaked window in the background,
out of focus.
(Cinematography): 85mm portrait lens, f/1.8, razor-sharp focus on eyes, creamy background
bokeh, cinematic composition, Arri Alexa cinematic color grade.
(Lighting): Low-key Chiaroscuro lighting, dramatic soft rim light from the left, deep
cinematic shadows on the right side of the face, 4500K color temperature.
(Negative Prompt): gibberish, foreign text, incomprehensible letters, blurry typography,
text on badge, text on name tag, logo on shirt, signage lettering, watermarks, bad anatomy,
deformed eyes, extra fingers.

[MOTION & LIP-SYNC PROMPT]
- Engine: Image-to-Video
- Camera Motion: Extremely subtle slow push-in (Zoom factor: 1.05)
- Character Motion: Micro chest breathing, single slow eye blink, maximum 5-degree subtle
  head tilt. No sudden head turns.
- Lip-Sync Engine: Audio Waveform aligned at 00:00.00
- Edit Strategy: 00:00.00~00:01.20 (Talking face) -> 00:01.20~00:02.20 (B-roll: Clenched
  fist on wooden desk) -> 00:02.20~00:03.15 (Close-up intense eye reaction).
```

---

## 부록. 프로젝트 운영 정보 (규칙이 아닌 참조 사실)

- API 키는 GitHub Secrets(FAL_API_KEY, ARK_API_KEY, ELEVENLABS_API_KEY, TYPECAST_API_KEY)에만 둔다.
  코드·채팅·문서에 넣지 않는다.
- 제작 실행은 GitHub Actions(`generate-video.yml` 생성/초상/오디션, `burn-subtitles.yml`
  자막·오디오·립싱크·조립, `qa-language.yml` 언어 검사)로 수행하며, 유료 실행 전에는
  규모(장면 수·비용)를 사용자에게 먼저 알리고 승인받는다.
- 시리즈 배역 목소리: 김씨=ElevenLabs `8vwSOQHQApfVx993mKf9`, 내레이터·아웃트로=ElevenLabs
  `5n5gqmaQi9Ewevrz7bOS`, 준호=MiniMax Casual_Guy, 최사장(EP3)=Typecast 명주
  `tc_656059fc4db338e38f77d0bc`(ssfm-v30), 폐지 할머니(EP3)=Typecast `tc_60ad0841061ee28740ec2e1c`(ssfm-v30).
- 2026-10-01 이전까지의 제작 지침·EP1~EP3 실증 교훈 ①~㉔·성장 전략 체크리스트는
  `docs/아카이브-이전제작지침(CLAUDE.md-2026-10-01까지).md`에 보관되어 있다(참조용).
  `docs/영화제작규칙집.md`, `docs/기획안-김씨시리즈.md`, `docs/EP3-인수인계.md`도 참조.
