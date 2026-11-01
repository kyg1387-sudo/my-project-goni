# 1화 BGM 브리프 (작곡가 / Suno·Udio 생성 겸용)

전 구간 공통: 멜로디를 거의 쓰지 않는 저음역 중심 다크 누아르. 믹스는 BGM 30~35%, 저음역 부스트, 3kHz 이상 고역은 -3dB 쉘빙으로 나레이션 자리를 비워 둡니다. 키는 전 곡 D minor 계열로 통일해 큐 전환이 매끄럽게 이어지도록 합니다. 각 큐는 루프 가능한 스템(드럼 / 베이스 / 패드 / 텍스처) 4트랙으로 납품받습니다.

| 큐 | 구간 | 시작 | BPM | 성격 | 핵심 악기 | 생성 프롬프트(영문) |
|---|---|---|---|---|---|---|
| Q1 Heartbeat | 후크 | 00:00 | 60→90 가속 | 심장 박동형 베이스 드럼, 멜로디 없음 | 서브 베이스 킥, 로우 톰, 비 소리 텍스처 | dark cinematic heartbeat, sub bass kick accelerating from 60 to 90 bpm, no melody, rain texture, tension, D minor drone, noir trailer |
| Q2 Drone | 1막 | 00:38 | 60 고정(초침 동기) | 떨림 없는 저음 드론, 초침 클릭에 맞춘 미세 펄스 | 로우 패드, 콘트라베이스 보잉, 클릭 | minimal low drone in D minor, ticking clock pulse at 60 bpm, fluorescent hum texture, anxious, no melody, no drums |
| Q3 Pulse | 2막 | 02:30 | 70→80→100 단계 상승 | 심장 박동 비트 재개, 승인음마다 한 단계씩 BPM 상승 | 킥, 808 베이스, 짧은 금속 퍼커션 | cinematic pulse building in three steps 70 80 100 bpm, deep 808 bass, metallic ticks, luxury tension, D minor, no melody |
| Q3-stop | 2막 전화 | 04:1x | 무음 | BGM 완전 정지, 빗소리만 | - | (없음) |
| Q4 Strings | 3막 | 05:00 | 템포 없음 | 저음 첼로와 바이올린의 긴 지속음, 봉투 순간 정지 | 첼로 C현 지속음, 바이올린 하모닉스 | sustained low cello and high violin harmonics, no tempo, slow swell, restrained elegance, D minor, cinematic revenge, no percussion |
| Q5 Build | 클라이맥스 | 08:00 | 72 | 드럼이 서서히 쌓여 「判子は」에서 정지, 찢는 소리 뒤 타격 한 방 | 플로어 톰 레이어, 서브 베이스, 메탈 임팩트 1회 | slow building floor tom layers at 72 bpm, sub bass, abrupt stop, single metallic impact hit, dark noir climax, D minor |
| Q6 Signature | 에필로그 | 09:43 | 84 | 웅장하고 중독성 있는 시그니처 아웃트로. 전화 장면에서 저주파만 남기고 CTA에서 복구 | 베이스 리프 4음, 로우 브라스, 킥 | memorable dark bass riff 4 notes, low brass stabs, 84 bpm, cinematic outro hook, D minor, modern noir, loopable |

## 시그니처 리프 규칙
- Q6의 4음 베이스 리프(D–F–E–A♭ 제안)는 시리즈 전 화에 같은 음형으로 반복합니다. 썸네일의 「残り○日」 배지처럼 소리의 시리즈 표식입니다.
- 쇼츠 티저의 마지막 4초에도 같은 리프를 씁니다.

## 큐 전환 지점(매니페스트 bgm_cues 기준)
sfx_cuesheet.csv의 BGM 행이 정확한 시각입니다. 편집 시 큐 교차는 크로스페이드 대신 하드 컷을 기본으로 하고, 유일한 예외는 Q4→Q5(8:00 미드롤 뒤)로 1초 페이드인입니다.

## 납품 사양
- 48kHz / 24bit WAV, 스템 4트랙 + 2mix, 루프 포인트 표기
- 각 큐는 구간 길이보다 20초 이상 길게, 끝은 테일 포함
