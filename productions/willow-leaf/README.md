# 버들잎 한 장 — 제작 패키지

광주·전남 구전설화 ① 나주 완사천 버들잎 설화 모티브. 러닝타임 8:13, 16:9, 80컷. AI 영화 제작 규칙집(Seedance 2.0 기준)을 따른다.

| 순서 | 파일 | 내용 |
|---|---|---|
| — | `00_script.md` | 최종 대본 (콜드오픈 + 6막, 컷 번호 표기, 제목·썸네일) |
| 1 | `01_character_sheets.md` | 캐릭터 시트 9장 (3패널, 얼굴은 한 번만) |
| 2 | `02_location_sheets.md` | 로케이션 시트 4장 (4셀 그리드) |
| 3 | `03_storyboards.md` | 스토리보드 콘택트시트 21장 (시트당 패널 5개 이하) |
| 4 | `04_cut_prompts.md` | 컷 프롬프트 80개 (LOCK/SCENE/CAMERA/DURATION/DIALOGUE/SOUND) |
| 5–6 | `05_edit_timeline.md` | 타임코드, VO, 자막 합성, 편집 지시 |
| — | `cuts.json` | 컷 데이터 (자동화 파이프라인용) |

## 수정 방법

03 · 04 · 05 · `cuts.json`은 `build_prompts.py`로 만든 파일이다. 직접 고치지 말고 스크립트의 `CUTS`와 `SCENES` 데이터를 고친 뒤 다시 생성한다.

```bash
python3 productions/willow-leaf/build_prompts.py
```

스크립트는 인물 식별자, 인원수 LOCK, 로케이션 시트 참조, 스타일 블록을 모든 컷에 자동으로 넣는다. 그래서 컷 하나를 고쳐도 규칙집 체크리스트가 깨지지 않는다.
