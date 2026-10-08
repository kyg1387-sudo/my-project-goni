# 시네마틱 AI 영상 제작 표준 운영 규격서

**문서 목적**: 생성형 AI 특유의 인위적인 이질감('AI 티')을 전면 배제하고, 전문 영화감독의
연출 문법과 탑티어 유튜브 PD의 편집 리듬을 결합하여 오차율 0% 및 일관된 시네마틱 퀄리티를
구현하는 표준 제작 규격서.

**적용 원칙 (사용자 확정, 2026-10-01)**: 앞으로 모든 작업은 이 규격서의 단계(PHASE 1~6)와
규칙을 시스템 프롬프트로 100% 엄수한다.

**호칭 (사용자 지정, 2026-10-04)**: 사용자를 **「고니감독님」**으로 부른다(모든 보고·답변).

---

## 제0장. 영상 제작 기준 — 길이·구성 공식 (이탈 방지) · 사용자 확정 2026-10-04, EP5부터 모든 영상에 적용

**모든 영상은 대본(PHASE 1)부터 이 기준으로 설계한다.** 제작 리소스(비용)·시청 지속 시간·광고 수익을 모두 고려한 기본 규격이다.

1. **길이**: 영상 전체 **10분~11분 내외, 최소 9분대 후반(9분 40초 이상)**. 아웃트로 포함, 엔드카드 제외.
   PHASE 1 음성 실측 Lock 타임라인이 9분 40초 미만이면 PHASE 2로 넘어가지 않고 대본(이야기 비트)을 보강한다.
2. **구간 공식**:

   | 시간 | 구간 | 내용 |
   |---|---|---|
   | 0:00~0:20 | 도입부 후크 | 결말의 가장 충격적이거나 눈물 나는 핵심 씬(또는 대사 한 줄)을 먼저 보여 호기심 유발 |
   | 0:20~3:30 | 발단·갈등 | 일상의 평온함 속에 숨겨진 아픔, 혹은 억울한 상황 묘사 |
   | **3:30** | **1차 중간광고** | 「그때, 생각지도 못한 일이 벌어졌습니다…」(「その時、思いもよらないことが起きたのです…」) 같은 전환점에 배치 |
   | 3:40~7:00 | 전개·위기 | 갈등 심화, 감정의 깊은 바닥(눈물/분노 게이지 상승) |
   | **7:00** | **2차 중간광고** | 진실이 밝혀지기 직전, 반전 직전 |
   | 7:10~9:30 | 절정·결말 | 오열하는 감동, 묵직한 보은, 사이다 응징(카타르시스) |
   | 9:30~10:30 | 아웃트로·여운 | 본편 하이라이트 몽타주 + 따뜻한 마무리 인사 + 다음 화 예고(구독 유도) |

3. **광고 지점(수익화 대비 설계)**: 현재는 유튜브 수익 창출 전이므로 **실제 광고는 넣지 않는다.** 수익화 후 바로 중간광고를 삽입할 수 있도록 **모든 영상에 3:30·7:00 광고 지점을 미리 설계**해 둔다(수익화 후 기존 영상에도 YouTube 스튜디오에서 해당 타임코드에 삽입). 대사·내레이션 중간 금지. 전환 문장 → 0.8~1.0초 여운 → 장면 경계(하드컷 또는 0.5초 디졸브)에 둔다. 업로드 가이드에 **「수익화 후 삽입용」 광고 타임코드**(3:30·7:00 ±10초)를 적는다.
4. **길이 채우기**: 이야기 비트(장면·사건)로 채운다. 여운·리액션·디졸브를 늘려 끌지 않는다(제4장 3~5초 시각 환기 유지).
5. **검수 항목**: 대본 승인 시 구간별 시작 시각표, PHASE 1 Lock 시 구간 경계·광고 지점 타임코드, 최종 조립 시 전체 길이(9:40 이상)를 보고한다.
6. 설계·비용 환산과 제작 메모는 `docs/제작규격-보강-EP4실증.md` §0-1(약 70~80줄·110~125컷, 1차 약 60~75달러).

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

## 제6장. EP3 실증 보강 규격 (2026-10-02 확정, EP4부터 적용)

상세 근거와 도구는 `docs/제작규격-보강-EP3실증.md`. 아래는 반드시 지키는 요약 규칙이다.

1. **대사 장면**: 단독 가슴 위 CU 정지 키프레임 → 음성 구동 생성(OmniHuman). 영상 위 립싱크 덧씌우기 금지.
   리액션 컷은 정지 푸시인 + 립싱크 제외, 7초 이하. 생성 후 첫 2초 헤드턴 검사(있으면 정지 리드 패치).
2. **인물**: 키프레임 승인 전 시트 정면 셀과 얼굴형 대조. 주연·조연은 머리·수염·의상 명도 중 2가지 이상
   다르게. 얼굴·표정 교체는 편집이 아니라 시트 표정 셀 참조 또는 신규 생성으로.
3. **소품·날씨·동작**: 소품 시트+셀 참조+고정 문장. 변형 시 소동작 한정 프롬프트로 재생성. 정지 폴백은
   손·정물 컷만, 보행·전신 자세 정지 금지. 날씨 효과는 로컬 오버레이 합성 + 현장음 지정.
4. **사운드**: 사람 있는 장면·"quiet/tense" 현장음 금지(웅얼거림 혼입), 대화 블록은 BGM만.
   BGM 볼륨 0.36~0.45, 0초부터 전편 커버, 리미터. −60dB 이하 2초 이상 무음 금지.
   내레이션 1.2배속, 줄 간 호흡 0.5초. TTS 후보는 언어 검사 + 사용자 청취로 확정.
5. **여운**: 말 끝→컷 ≥1.0초, 인물 대사 끝→컷 ≥1.8초. 시간·장소 전환은 디졸브 0.5~1.0초.
   `retime_transitions.py --gap 0.5 --tail 1.0`, 재실행 전 원본 .ass 복원. 대사 줄 오프셋 1프레임 이내 고정.
6. **엔딩(시리즈 공통)**: 본편 1.0초 페이드아웃 → 검은 화면 0.8초 → 진행자 아웃트로 → 0.6초 크로스페이드
   → 「미담이야기」 엔드카드 5.5초 → 암전. `append_outro.py`.
7. **검수**: 조립본마다 길이·전환 콘택트시트·대사 입 크롭(0.25~0.5초)·인물 대조·재생성 컷 1초 간격·
   음량 윈도를 전수 수행. 사용자 지적은 0.25초 간격 크롭으로 재현 후 원인 기록.
8. **운영**: 캐시 이어하기 기본, 오디오만 바뀌면 remix(무과금), 클립 교체는 generate→burn 순서.
   유료 전 규모·비용 보고. 한 브랜치 한 세션. 전달은 480p 미리보기 + 원본 28MB 분할.
   수정 요청은 번호 목록으로 관리하고 매 보고에 상태 갱신.

---

## 제7장. EP4 실증 보강 규격 (2026-10-04 확정, EP5부터 적용)

상세 근거·도구·단가는 `docs/제작규격-보강-EP4실증.md`. 목적: 다음 편 **시간 단축·오류 감소·지출 절감**. 아래는 반드시 지키는 요약 규칙이다.

1. **생성기 우선**: PHASE 3·4는 생성기 스크립트(`build_ep4_phase3.py`, `build_ep4_keyframes.py`를 편 번호만 바꿔 복사)로 스토리보드·장면·오디오·자막·키프레임 스펙을 한 번에 만든다. 손으로 옮겨 적지 않는다.
2. **무료 먼저**: 리액션=정지 푸시인, 대사=OmniHuman용 정지 프레임, **무인 정물·종이·글자 합성 면·잠든 인물=정지 푸시인**을 i2v 전에 `video-overrides/`로 만든다(i2v는 이런 컷에 글자를 만들고 조명을 바꾼다). i2v는 사람이 움직이는 컷과 눈·김·불빛이 필요한 배경에만.
3. **혼합 화질**: 인물 얼굴이 보이는 i2v 컷만 Seedance pro 1080p(0.108/s), 무인·CCTV·원경은 lite(0.036/s). 출력 1920x1080 crop. OmniHuman 0.16/s, **한 번에 8초 이하**, 가슴 위 CU.
4. **인물 i2v 동작**: 장면별 동작 고정 문장 + 금지 동작(뒤돌기·내려오기)을 반드시 쓴다. 줌인·줌아웃은 편집에서 로컬로.
5. **키프레임 보정**: 생성 직후 레터박스 자동 크롭·16:9 검사(검수 시트는 원본 비율), 작은 외계어는 세로 보간 채움, 같은 장소 연속 컷·표정 변화 컷은 합격 컷 부분 편집(EDIT_FROM).
6. **일본어 글자**: 무지 면 생성 → `ja_text_overlay.py`(실글꼴·원근·전체 화면 추적) 합성. 호수판·명판은 그려 넣기.
5-1. **눈물 표현(사용자 확정 2026-10-08)**: 흘리는 눈물은 실제 눈물처럼 자연스럽게. 키프레임은 아래 눈꺼풀에 고인 얇은 물막 + 눈가·코끝 붉어짐 + 한쪽 뺨에 가는 줄기 최대 1개(무광 피부). 굵고 반짝이는 젤 같은 줄기·여러 줄·양 뺨 동시 금지(#01 S03e 실증). 억누르는 장면은 「젖었지만 흐르지 않음」. i2v 동작은 한 줄기가 천천히 자연 곡선으로. 생성기가 눈물 컷을 자동 감지해 문장을 넣고, Kill Gate에서 눈물 질감을 검사한다.
7. **인물 일관성**: 키프레임 승인 때와 조립 후 `qa_faces.py`로 인물별 얼굴을 전부 대조. 기준 얼굴은 대사 키프레임 → 다른 컷을 그 얼굴로 편집.
8. **조립**: 장면 경계 프레임 맞춤(`frame_quantize`), BGM 구간 숨은 내레이션 아래(무언 컷 금지), `qa_assembly.py`로 전수 검수, `export_files=QA`로 클립 검수 시트만 받기.
9. **운영**: 보류(나중에 처리)한 요청은 수정 목록에 「보류」로 올리고 **최종 전달 전 전부 처리 확인**(EP4 아웃트로 하이라이트 누락 교훈). burn 실행 중에는 브랜치에 푸시하지 않는다(결과 커밋 충돌). 실패 시 Artifact를 `deliver_from_run_id`·`resume_run_id`로 무료 회수. 유료 단계는 실측 단가로 추정해 보고.
10. **아웃트로(일본어판)**: 하이라이트 몽타주 → CU 구독 요청(버튼) → 허리 위 예고 → 손 흔들기, 28초. `outro_cta_overlay.py`.
11. **영상 길이·구성**: **제0장(영상 제작 기준)** 을 따른다 — 10~11분(최소 9분 40초), 후크 0:20 · 1차 광고 3:30 · 2차 광고 7:00 · 결말 9:30 · 아웃트로 10:30.

---

## 제8장. 조명·카메라 앵글·편집 구현 기준 (2026-10-04 사용자 확정, 모든 작품에 적용)

상세 근거와 프롬프트 문구는 `docs/제작규격-보강-조명카메라앵글.md`. 제3장을 실전용으로 보강한 것이며, 아래는 반드시 지키는 요약 규칙이다.

1. **구간별 조명**: 일상·회상·눈물은 디퓨즈 자연광 + 골든아워 역광 림라이트(대비 낮게). 압박·갑질은 위에서 수직으로 떨어지는 차가운 형광등(5600K 이상). 대면·권력 등장은 강한 역광 실루엣. Chiaroscuro는 압박·대면 구간에만. 조명은 **로케이션 시트에서 잠근다**. 프롬프트에는 감독 이름 대신 묘사어를 쓴다.
2. **앵글 다양화(사용자 지시)**: 연속 두 컷 같은 구도 금지(사이즈 2단계 또는 각도 30° 이상 차이). 대화는 180° 축 고정. 와이드 → 미디엄 → CU로 들어가고 정점 뒤에는 와이드·인서트로 여운. 장면마다 전경 너머로 엿보는 컷 최소 1개. 렌즈 24/35/50/85mm + 100mm 매크로 인서트.
3. **앵글의 의미**: 하이 = 무력·감시, 로우 = 권력·위압, 아이레벨 = 공감, 오버헤드 = 운명. 권력이 반전되면 같은 장소에서 앵글을 뒤집는다(전반 가해자 로우 → 후반 가해자 하이).
4. **왜곡 기법 제한**: 돌리줌은 작품당 1회(정체 발각 순간). 더치(5~7°)는 **악역의 탐욕·붕괴 모티프로만, 작품당 최대 2회**(예: 갑질 장면 5° 1회 + 비리 발각 7° 1회), 주인공 장면에는 쓰지 않는다. 악역 근접 CU 금지(가슴 위까지), 긴장은 손·땀·안경 ECU 인서트로. 초커는 주인공의 감정 정점에만.
4-1. **카메라 안정도 축(사용자 확정)**: 주인공·조력자(정직·품격) 장면은 고정(트라이포드)과 절제된 팬·슬로우 푸시인만. 악역 장면은 갑질·횡령·패닉 구간에서 미세 핸드헬드(+더치)로 불안을 표현한다. 핸드헬드·팬·틸트·지브는 모두 편집에서 구현한다.
4-2. **소품의 인격화**: 핵심 소품(작품의 상징물, 종이컵·수첩·서류 등)은 화면의 70% 이상을 채우는 ECU + 얕은 심도로 찍어 인물의 감정을 대변하게 한다.
4-3. **권력 역전의 극단**: 반전 후 몰락한 가해자는 극단적 부감(버즈아이, 위에서 수직)으로 격하하고, 권력자는 로우앵글로 올려다본다.
5. **AI 한계 대응**: OmniHuman 대사 CU는 정면~45°만. 와이드 인물은 실루엣·뒷모습. 주 무대(컷 60% 이상)는 PHASE 2에서 **앵글 시트**(역방향·하이·로우·전경 너머)를 추가로 잠근다.
6. **편집 구현(무료)**: 푸시인·풀백·팬·틸트·지브(고해상도 키프레임 위 크롭 이동)·돌리줌(인물 마스크 2.5D)·랙 포커스(초점이 다른 키프레임 2장 디졸브)·더치(회전)·핸드헬드(미세 흔들림)·색감 통일(전 컷 공통 그레이딩 + 그레인)은 생성 지시가 아니라 편집에서 만든다. i2v는 이런 지시를 무시한다. **한 컷에 카메라 움직임 하나**(크레인→패닝→풀백 같은 복합 무빙은 컷을 나눈다). 측면(프로필) 투샷은 대사 없는 비트에만 쓰고, 대사는 정면·3/4 단독 CU로.
7. **산출물·검사**: 작품마다 `02_카메라앵글설계.md`(장면별 컷 순서)를 만들고, PHASE 3 생성기가 연속 같은 구도·축 위반·왜곡 2회 이상·OMNI 측면 각도를 자동 검사한다. PHASE 4 보고에 앵글 분포를 포함하고, 한 앵글이 60%를 넘으면 다시 설계한다.

---

## 제9장. 제작 도구 안전장치 (2026-10-04 코드 반영, 모든 작품에 적용)

김씨 시리즈 실증 오류와 코드 점검(취약점 18건)에서 나온 장치다. 도구가 기본으로 막으므로 끄지 않는다.

1. **비용 상한**: `scripts/scenes/<작품>.json`에 `budget_usd`를 넣는다. `generate_video.py`가 생성 전에 실측 단가로 추산을 출력하고, 상한을 넘으면 멈춘다.
2. **유료 누수 차단**: 정지 푸시인·재사용·카드 장면은 `override_required: true`로 표시한다(교체 클립이 없으면 중단). 키프레임 없는 t2v는 기본 금지(`allow_t2v`). OmniHuman이 아닌 대사 장면과 Omni 실패 장면은 폐기한 sync-lipsync로 넘어가지 않고 원본을 유지한다(`legacy_lipsync`는 지난 편 재조립용).
3. **OmniHuman 8초 상한**: 8초를 넘는 Omni 장면이 있으면 생성 전에 멈춘다(`omnihuman_max_s`).
4. **조립 안전**: 장면 파일은 숫자 순서로 정렬한다(100개 이상 대응). `scene_durations` 개수가 클립 수와 다르면 멈춘다. BGM 구간 캐시는 Artifact에 함께 저장해 재조립 때 재과금·곡 변경을 막는다.
5. **언어 검사**: 자막에 가나가 있으면 ja + large-v3로 자동 검사한다. 오디션 폴더도 스펙 대사와 대조한다. Typecast는 `language`(jpn/kor)를 지정하지 않으면 멈춘다.
6. **운영**: 유료 폴링은 30분 상한(재제출 없이 중단). burn의 `source_run_id`는 기본값 없이 필수. 제작 도구는 브랜치 병합 대신 **파일 단위로만 가져온다**(미디어 히스토리 유입 방지).

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
  `docs/영화제작규칙집.md`, `docs/기획안-김씨시리즈.md`, `docs/EP3-인수인계.md`, `docs/제작규격-보강-EP3실증.md`,
  `docs/시리즈-제작비용.md`, `docs/제작규격-보강-조명카메라앵글.md`도 참조.
