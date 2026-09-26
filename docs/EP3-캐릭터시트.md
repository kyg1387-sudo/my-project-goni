# EP3 캐릭터 시트 프롬프트 (규칙집 §2 규격)

무료 단계 — 텍스트만 생성함(API 호출 없음). 실제 이미지 생성은 승인 후 진행.

**시트 안 텍스트는 영문으로 둠**: 생성 모델이 한글은 물론 라틴 문자도 정교하게 못 쓰기 때문에(실증), 글자 수가 적은 영문 라벨로 실패 확률을 낮췄다. 이 시트는 레퍼런스 전용이라 시청자에게 노출되지 않는다.

## 경비원 김씨 (김영곤) (`kim.txt`)

- 고정 식별자: 가슴의 흰색 무지 명찰표(글자 없음), 짧은 반백 스포츠머리, 짙은 감색 유니폼
- 헤더 텍스트: "GUARD KIM" / "Height: 170cm" / "Quiet, dutiful, gentle beneath a gruff exterior" / "Voice: low, calm, few words"

**카메오 확정(시리즈 전편 공통, CLAUDE.md 참고)**: 경비원 김씨 역은 감독 김영곤 본인 얼굴로 EP1부터 마지막 편까지 출연한다. 아래 프롬프트는 사진이 없을 때 쓰는 순수 텍스트 생성용 폴백이다 — **실제로는 감독 정면 사진을 이미지 편집 모델(예: 얼굴을 보존하며 의상만 바꾸는 nano-banana류)에 입력해 만들어야 한다.** 사진을 받으면 이 시트를 그 사진 기반 image-to-image 프롬프트로 다시 만들 것 — 지금 프롬프트로 먼저 생성하지 말 것.

```
Character reference sheet, one single 16:9 image on a pure white background, photorealistic, soft studio lighting, minimal style, fashion-lookbook layout. Top-left header in clean black sans-serif text: large bold title "GUARD KIM", then four small lines below it: "Height: 170cm" / "Quiet, dutiful, gentle beneath a gruff exterior" / "Voice: low, calm, few words" / "Photorealistic, soft studio lighting, minimal style, modern Korean apartment complex, contemporary, worn everyday clothing". Left half: full-body front view and full-body back view of the same 60대 초반 한국 남성(a Korean man in his early 60s), standing side by side, feet visible, both figures cropped at the neck so the head is cut off by the top edge of the frame — no face shown on the left side. Wardrobe: plain dark navy security guard uniform, a blank white nameplate with absolutely no text or lettering on the left chest, a black leather duty belt with an old handheld radio, black work shoes. Body: sturdy build, slightly stooped shoulders from long standing, weathered hands. Right half: one large close-up portrait from the shoulders up, straight to camera, calm, neutral, watchful, short salt-and-pepper buzz cut, round face, no hat. No text other than the header.
```

## 폐지 줍는 할머니 (`grandma.txt`)

- 고정 식별자: 색 바랜 갈색 꽃무늬 두건, 굽은 허리, 해진 갈색 목장갑
- 헤더 텍스트: "GRANDMOTHER" / "Height: 150cm" / "Frail but fiercely independent, quietly warm" / "Voice: soft, raspy, few words"

```
Character reference sheet, one single 16:9 image on a pure white background, photorealistic, soft studio lighting, minimal style, fashion-lookbook layout. Top-left header in clean black sans-serif text: large bold title "GRANDMOTHER", then four small lines below it: "Height: 150cm" / "Frail but fiercely independent, quietly warm" / "Voice: soft, raspy, few words" / "Photorealistic, soft studio lighting, minimal style, modern Korean apartment complex, contemporary, worn everyday clothing". Left half: full-body front view and full-body back view of the same 70대 후반 한국 여성(a Korean woman in her late 70s), standing side by side, feet visible, both figures cropped at the neck so the head is cut off by the top edge of the frame — no face shown on the left side. Wardrobe: a faded brown floral headscarf tied over her hair, a plain worn dark brown baggy work trousers ("monpe") and a thick navy quilted jacket, worn brown work gloves. Body: thin frame, stooped back, deeply wrinkled hands. Right half: one large close-up portrait from the shoulders up, straight to camera, tired but gentle, quiet dignity, grey hair mostly covered by the headscarf, faded brown floral headscarf. No text other than the header.
```

## 고물상 주인 최사장 (`choi.txt`)

- 고정 식별자: 기름때 묻은 무늬 없는 회색 작업 조끼, 짧게 깎은 희끗한 머리, 검은 목장갑
- 헤더 텍스트: "CHOI - SCRAPYARD OWNER" / "Height: 173cm" / "Gruff, businesslike, secretly soft-hearted" / "Voice: brisk, low, businesslike"

```
Character reference sheet, one single 16:9 image on a pure white background, photorealistic, soft studio lighting, minimal style, fashion-lookbook layout. Top-left header in clean black sans-serif text: large bold title "CHOI - SCRAPYARD OWNER", then four small lines below it: "Height: 173cm" / "Gruff, businesslike, secretly soft-hearted" / "Voice: brisk, low, businesslike" / "Photorealistic, soft studio lighting, minimal style, modern Korean apartment complex, contemporary, worn everyday clothing". Left half: full-body front view and full-body back view of the same 50대 한국 남성(a Korean man in his 50s), standing side by side, feet visible, both figures cropped at the neck so the head is cut off by the top edge of the frame — no face shown on the left side. Wardrobe: a grease-stained plain grey work vest over a dark shirt, black work gloves, a worn radio clipped to his belt. Body: stocky, sturdy build, calloused hands. Right half: one large close-up portrait from the shoulders up, straight to camera, wary, businesslike, short greying hair, no hat. No text other than the header.
```

