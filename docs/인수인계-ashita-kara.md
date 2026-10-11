# 인수인계 — 일본판 「明日から来なくていい」(ashita-kara) 작업 현황

작성일: 2026-10-11. 이 문서는 다른 세션(모델 무관)이 작업을 그대로 이어받기 위한 것이다.
먼저 `CLAUDE.md`(저장소 규칙) → `docs/기획-일본판-ashita-kara.md`(기획·비용·결정 항목) 순으로 읽을 것.

## 1. 현재 상태 (한 줄)

일본판 제작 자산이 **전부 생성·검증·커밋**됐고, **생성(과금) 워크플로는 아직 한 번도 실행하지 않았다.**
브랜치: `claude/happy-volta-9w5oxb` (origin에 푸시됨, main에는 아직 병합 안 됨).

## 2. 완료된 것

| 파일 | 상태 |
|---|---|
| `scripts/build_ashita_kara.py` | 대본(일본어 TTS 원문+한국어)·장면·자막·오디오 설정·톤 연출표·대본 문서를 한 번에 생성. **대본 수정은 이 파일에서만** 하고 실행하면 아래 파일이 전부 재생성된다. |
| `scripts/scenes/ashita-kara.json` | 장면 72개 (10초 57 + 5초 15 = 645초, 10분 45초). 규칙집 5블록 양식. |
| `subs/ashita-kara.ass` | 일본어 구움 자막 63줄 + 화면 카드 9장(Caption/Title 스타일, TTS 제외). |
| `subs/ashita-kara.ko.srt` | 한국어 CC. |
| `scripts/audio/ashita-kara.json` | MiniMax speech-02-hd, language_boost=Japanese, 전 63줄 감정·속도 지정, scene_speakers, silent_styles. |
| `docs/톤연출표-ashita-kara.md` | 줄별 톤 연출표. |
| `docs/기획-일본판-ashita-kara.md` | 비용 추정($30~45), 결정 필요 항목 5개, 유튜브 일본어 제목·설명, 글로벌 가이드. |
| `skits/ashita-kara.md` | 읽기용 대본. |

검증 통과: 화자-화면 불일치 0, 한 장면 다화자 0, 대사 겹침 0, 감정·속도 미지정 0, TTS 본문 영문·숫자 0,
ffmpeg 자막 렌더 확인(카드 중앙 붉은색, 대사 하단).

파이프라인 변경(기존 작품 호환 확인됨):
- `generate_video.py`, `slice_scenes.py`: 장면 항목 `{"prompt","duration":5|10}` 지원.
- `generate_audio.py`: `silent_styles`(화면 전용 자막 → TTS 제외), 빈 현장음 프롬프트는 생략.
- `qc_tts.py`: `--config` 로 language_boost 읽어 일본어(가나·한자) 비율 검사. burn 워크플로에 `--config` 전달 반영.

## 3. 사용자 답변 대기 중 (이게 다음 단계의 입력)

기획안 3절의 5개 항목. 요약:
① 기준 초상 → image-to-video 채택 여부 (채택 시 `generate_video.py`에 refs/i2v 입력 추가 필요 — 무과금 코드 작업).
② 카메오 여부 (본인 사진 → 사토 역). 일본판이라 "김영곤" 명찰은 제외 권장.
③ 목소리 오디션: 핵심 3줄(63번 사토 마지막 대사 계열·타나카 해고 통보·내레이션 1번)을 후보 목소리로 시험 생성 후 확정.
④ 채널: 일본 전용 새 채널에 업로드(한국어 채널에 올리지 말 것).
⑤ 콜드 오픈 중복 장면(3번=26번 프롬프트 동일)은 그냥 2회 생성(소액).

## 4. 답변 후 실행 순서

1. (①채택 시) refs 지원 코드 추가 → 인물 4명 기준 초상 생성 → 사용자 확인.
2. 오디션 3줄 생성 → 사용자 청취 → `scripts/audio/ashita-kara.json` voices 확정.
3. GitHub Actions `콩트 영상 생성`: `skit=ashita-kara` (72장면). 실패 시 같은 워크플로 `scenes_only`로 부분 재생성.
4. 전 장면 프레임 검수(시작·중간·끝 + 무인 지시 장면 인물 유무 + 글자 유무) → 불합격만 `scenes_only` 재생성.
5. `콩트 영상 자막 입히기`: 먼저 `qc_tts=true`(일본어 언어 검사) → 통과 후
   `skit=ashita-kara, source_run_id=<3번 run>, add_audio=true, lipsync=true, commit_output=true`.
6. 완성본 시사 → 쇼츠 5개 → 업로드(기획안 6절 가이드).

## 5. 주의 (이 작품 고유)

- 한국어 전용 규칙은 이 작품에서 **일본어 전용**으로 대체된다. 장면 프롬프트 [DIALOGUE]에 "일본어로 말하는 입 모양, 영어 없음" 이미 포함.
- 대본을 고치면 `python3 scripts/build_ashita_kara.py` 재실행 후 아래 검증을 다시 돌릴 것(정렬 검증 스니펫은 기획안 0절 결과와 같은 항목: 화자-화면 일치·겹침·감정 누락·영문 포함).
- 긴 내레이션은 빌더가 문장 단위로 자동 분할한다(자막 2줄 이내). 줄 번호가 바뀌므로 `emotion_overrides`를 손으로 고치지 말고 빌더의 L(...) 값으로 고칠 것.
- 폰트: .ass는 Noto Sans CJK JP. 워크플로가 설치하는 fonts-noto-cjk에 포함돼 있다.
