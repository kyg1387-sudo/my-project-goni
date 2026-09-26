# EP3 컷 프롬프트 (규칙집 §5, 5블록 양식)

총 44개 컷 · 각 프롬프트 끝에 파이프라인 고유 규칙 문구(`한국어로 말하는 입 모양, 영어 없음`)를 덧붙여 실제 생성에 사용한다.

**컷 길이 제약**: [5, 10]초만 사용 — fal.ai Seedance가 5·10초만 지원해서(scripts/generate_video.py), 규칙집 §6의 이상적 길이표(인서트 3~4초 등)는 가까운 값으로 반올림했다.

## 콜드오픈

### CUT 1 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet, the "CHOI - SCRAPYARD OWNER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly two people in frame: the guard (Kim), Choi (the scrapyard owner). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, 낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 굳은 표정으로 50대 한국 남성 고물상 주인(다부진 체격, 짧게 깎은 희끗한 머리, 기름때 묻은 무늬 없는 회색 작업 조끼와 검은 목장갑, 허리에 낡은 무전기) 앞을 가로막고 서 있고 그 옆에 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카가 놓여 있는 장면, 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임
[CAMERA]
Movement: Slow dolly in toward Kim
Speed: natural, unhurried
Framing: keep the full cast in frame, Medium close-up throughout, Eye-level
End: hold on Kim's resolute expression
[DURATION] 10 seconds
[DIALOGUE] the guard (Kim) (Korean, [firm, low]): "이 손잡이, 가죽끈 감긴 거 보이시죠."
[SOUND] rusty cart wheel creak, distant scrap metal clinking, tense quiet, no crowd murmur
```

### CUT 2 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet, the "CHOI - SCRAPYARD OWNER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly two people in frame: the guard (Kim), Choi (the scrapyard owner). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, 낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 굳은 표정으로 50대 한국 남성 고물상 주인(다부진 체격, 짧게 깎은 희끗한 머리, 기름때 묻은 무늬 없는 회색 작업 조끼와 검은 목장갑, 허리에 낡은 무전기) 앞을 가로막고 서 있고 그 옆에 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카가 놓여 있는 장면, 정면 상반신 구도, 한국어로 대사를 마무리하며 입을 자연스럽게 움직이고, 최사장은 미심쩍은 표정으로 침묵
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the full cast in frame, Medium close-up throughout, Eye-level
End: hold on Choi's wary silent stare after Kim finishes speaking
[DURATION] 10 seconds
[DIALOGUE] the guard (Kim) (Korean, [steady, resolute]): "이거 임자 되시는 분이 직접 감으신 겁니다. 함부로 못 없애는 물건입니다."
[SOUND] rusty cart wheel creak, tense quiet, no crowd murmur
```

## 궁금증 캡션

### CUT 3 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, 낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판, 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카 손잡이의 가죽끈만 어둡게 보이는 정지된 듯한 구도, 인물 없음
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the setting in frame, Extreme close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] none — quiet natural room tone only
```

## 타이틀

### CUT 4 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 아파트 단지 정문 앞 인도, 화단과 낮은 담장, 저녁 어스름이 내려앉은 텅 빈 인도, 사람이 한 명도 없는, 인물 없음
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the setting in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] none — quiet natural room tone only
```

## 사흘 전 캡션

### CUT 5 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 아파트 단지 정문 앞 인도, 화단과 낮은 담장, 오후 햇살이 비치는 인도, 사람이 한 명도 없는, 인물 없음
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the setting in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] none — quiet natural room tone only
```

## 1막 — 할머니의 하루

### CUT 6 (10s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 아파트 단지 정문 앞 인도, 화단과 낮은 담장, 오후 햇살 속 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카를 끌고 걸어오는 모습
[CAMERA]
Movement: Side tracking, camera moves parallel to the grandmother
Speed: natural, unhurried
Framing: keep the grandmother in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] cart wheel creaking softly, quiet afternoon street
```

### CUT 7 (10s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 아파트 단지 정문 앞 인도, 화단과 낮은 담장 인근 골목, 오후, 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 허리를 굽혀 상자를 주워 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카에 싣는 모습
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the grandmother in frame, Medium throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] cardboard rustling, quiet afternoon street
```

### CUT 8 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카 손잡이에 감긴 낡은 갈색 가죽끈, 아파트 단지 정문 앞 인도, 화단과 낮은 담장 배경, 오후 햇살
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the setting in frame, Close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] none — quiet natural room tone only
```

### CUT 9 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 아파트 단지 정문 앞 인도, 화단과 낮은 담장 인근 골목, 오후, 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 다른 곳은 험하게 다뤄도 손잡이의 가죽끈만은 헝겊으로 정성스레 닦아내는 손
[CAMERA]
Movement: Slow dolly in toward her hands
Speed: natural, unhurried
Framing: keep the grandmother in frame, Close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] soft cloth wiping, quiet street
```

### CUT 10 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판, 오후, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 창문 너머로 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 지나가는 모습을 무표정하게 지켜보는 장면
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Medium close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] none — quiet natural room tone only
```

### CUT 11 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판 앞 화단, 이른 아침, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 납작하게 접은 종이상자 더미를 조용히 내려놓고 돌아서는 모습
[CAMERA]
Movement: Static rear shot, back of Kim fills frame
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Full shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet early morning ambience, birds distant
```

### CUT 12 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 아파트 단지 정문 앞 인도, 화단과 낮은 담장, 이른 아침, 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 그 상자 더미를 발견하고 살짝 고개를 끄덕이며 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카에 싣는 모습
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the grandmother in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet early morning ambience
```

## 2막 — 리어카 분실

### CUT 13 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터, 늦은 오후, 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카를 담벼락 옆에 세워두고 폐지를 주우러 자리를 비우는 모습
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the grandmother in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] demolition site rubble settling, distant truck engine idling, no crowd voices
```

### CUT 14 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터, 늦은 오후, 철거 인부들이 잔해를 트럭에 싣는 장면, 배경에 놓인 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카가 함께 실려가는 모습
[CAMERA]
Movement: Slow dolly in toward the departing truck
Speed: natural, unhurried
Framing: keep the setting in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] truck engine, rubble loading, distant
```

### CUT 15 (10s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터, 늦은 오후, 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 폐지를 안고 돌아와 텅 빈 자리를 발견하고 얼어붙은 표정으로 서 있는 장면, 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임
[CAMERA]
Movement: Dolly zoom: camera pulls back while lens zooms in, subject size constant, background stretches
Speed: natural, unhurried
Framing: keep the grandmother in frame, Medium close-up throughout, Eye-level
End: hold on her frozen face for the last second
[DURATION] 10 seconds
[DIALOGUE] the grandmother (Korean, [breathless, quiet]): "…내 리어카…"
[SOUND] sudden silence, wind
```

### CUT 16 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터, 늦은 오후, 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 주저앉아 빈손으로 바닥을 짚는 모습
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the grandmother in frame, Full shot throughout, Low angle
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet, distant city hum
```

### CUT 17 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터 인근, 늦은 밤, 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 홀로 주변을 헤매며 찾는 모습, 지친 모습
[CAMERA]
Movement: Handheld, fine natural tremor
Speed: natural, unhurried
Framing: keep the grandmother in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet night street ambience, footsteps
```

## 3막 — 김씨의 사흘 밤

### CUT 18 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판, 밤, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 퇴근 준비를 하다 창밖 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)의 빈 자리를 보고 잠시 멈춰서는 장면
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Medium close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] quiet night office hum, clock ticking
```

### CUT 19 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판, 밤, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 결심한 듯 문을 열고 나서는 모습
[CAMERA]
Movement: Follow shot, camera behind Kim at shoulder height
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Full shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] door, footsteps into the night
```

### CUT 20 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 가로등 하나만 켜진 어두운 동네 골목, 쌓여 있는 폐지 더미들과 낡은 셔터문들, 옅은 밤안개, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 손전등을 들고 골목 구석구석을 살피며 걷는 모습
[CAMERA]
Movement: Side tracking, camera moves parallel to Kim
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] footsteps, flashlight click, distant night ambience
```

### CUT 21 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 가로등 하나만 켜진 어두운 동네 골목, 쌓여 있는 폐지 더미들과 낡은 셔터문들, 옅은 밤안개, 비가 내리는 가운데 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 우산도 없이 젖은 채 골목을 헤매는 모습
[CAMERA]
Movement: Handheld, fine natural tremor
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Full shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] heavy rain, footsteps splashing
```

### CUT 22 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판, 밤, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 서랍에서 아내의 낡은 꽃무늬 수첩을 꺼내 펼쳐보는 모습
[CAMERA]
Movement: Slow dolly in toward Kim
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Medium close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] quiet night office hum, paper rustling
```

### CUT 23 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 아내의 낡은 꽃무늬 수첩 페이지 클로즈업, 손글씨가 적힌 모습이나 글자는 흐릿하게 표현, 인물 없음
[CAMERA]
Movement: Rack focus from the page edge to the writing, camera locked
Speed: natural, unhurried
Framing: keep the setting in frame, Extreme close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] paper rustling
```

### CUT 24 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판 창가, 밤, 지친 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 보온병 뚜껑을 열어 마시며 먼 곳을 응시하는 장면
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Medium close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet night office hum
```

### CUT 25 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 가로등 하나만 켜진 어두운 동네 골목, 쌓여 있는 폐지 더미들과 낡은 셔터문들, 옅은 밤안개, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)의 지친 발걸음 클로즈업, 다리를 절며 걷는 모습
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] tired footsteps, night ambience
```

## 4막 도입 — 고물상을 찾아가다

### CUT 26 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 거리 초입, 리어카들이 줄지어 서 있는 낮의 골목, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 두리번거리며 걸어가는 모습
[CAMERA]
Movement: Side tracking, camera moves parallel to Kim
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Full shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] daytime street ambience, distant traffic
```

### CUT 27 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 마당 입구, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 걸음을 멈추고 안쪽의 낯익은 손잡이를 발견하는 모습
[CAMERA]
Movement: Slow zoom in, camera locked
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Medium close-up throughout, Eye-level
End: hold on Kim's focused gaze
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] daytime scrapyard ambience
```

## 4막 — 고물상 대치

### CUT 28 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet, the "CHOI - SCRAPYARD OWNER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly two people in frame: the guard (Kim), Choi (the scrapyard owner). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, 낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 굳은 표정으로 50대 한국 남성 고물상 주인(다부진 체격, 짧게 깎은 희끗한 머리, 기름때 묻은 무늬 없는 회색 작업 조끼와 검은 목장갑, 허리에 낡은 무전기) 앞을 가로막고 서 있고 그 옆에 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카가 놓여 있는 장면, 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임
[CAMERA]
Movement: Slow dolly in toward Kim
Speed: natural, unhurried
Framing: keep the full cast in frame, Medium close-up throughout, Eye-level
End: hold on Kim's resolute expression
[DURATION] 10 seconds
[DIALOGUE] Choi (the scrapyard owner) (Korean, [brisk, businesslike]): "이미 계근까지 끝난 물건입니다. 값도 다 쳐드렸고요."
[SOUND] rusty cart wheel creak, tense quiet, no crowd murmur
```

### CUT 29 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, 낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)의 손이 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카 손잡이에 감긴 낡은 가죽끈을 천천히 짚는 모습, 결연한 표정, 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임
[CAMERA]
Movement: Slow dolly in toward Kim
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Medium close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] the guard (Kim) (Korean, [firm, low]): "이 손잡이, 가죽끈 감긴 거 보이시죠."
[SOUND] tense quiet
```

### CUT 30 (10s)
```
[LOCK] Use the "CHOI - SCRAPYARD OWNER" reference character sheet, the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly two people in frame: Choi (the scrapyard owner), the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, 낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판, 50대 한국 남성 고물상 주인(다부진 체격, 짧게 깎은 희끗한 머리, 기름때 묻은 무늬 없는 회색 작업 조끼와 검은 목장갑, 허리에 낡은 무전기)가 팔짱을 낀 채 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)을 바라보는 장면, 김씨가 대사를 마무리하는 목소리를 들으며 표정이 서서히 흔들리는 모습
[CAMERA]
Movement: Slow zoom in, camera locked
Speed: natural, unhurried
Framing: keep the full cast in frame, Close-up throughout, Eye-level
End: hold on Choi's softening expression
[DURATION] 10 seconds
[DIALOGUE] the guard (Kim) (Korean, [steady, resolute]): "이거 임자 되시는 분이 직접 감으신 겁니다. 함부로 못 없애는 물건입니다."
[SOUND] tense quiet fading into a softer stillness
```

### CUT 31 (10s)
```
[LOCK] Use the "CHOI - SCRAPYARD OWNER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: Choi (the scrapyard owner). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 고물상 마당, 압축된 폐지 더미와 녹슨 저울, 머리 위로 매달린 알전구 조명, 낡은 트럭 한 대, 벽에는 아무 글자도 없는 매끈한 함석판, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 누그러진 표정으로 손짓하며 50대 한국 남성 고물상 주인(다부진 체격, 짧게 깎은 희끗한 머리, 기름때 묻은 무늬 없는 회색 작업 조끼와 검은 목장갑, 허리에 낡은 무전기) 앞을 가로막고 서 있고 그 옆에 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카가 놓여 있는 장면, 정면 상반신, 한국어로 대사하며 입을 자연스럽게 움직임
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep Choi (the scrapyard owner) in frame, Medium close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] Choi (the scrapyard owner) (Korean, [gruff, softened]): "…가져가십쇼. 값은 됐습니다."
[SOUND] quiet resolution, distant scrapyard ambience
```

## 5막 — 새벽 배달

### CUT 32 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판 앞, 밤늦게, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 손전등을 입에 물고 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카 바퀴를 직접 갈아 끼우는 모습
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Medium close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] metal clinking, tools, quiet night
```

### CUT 33 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카 손잡이 클로즈업, 밤, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)의 거친 손이 해진 갈색 가죽끈 위에 낡은 남색 작업 장갑 한 짝을 조심스레 덧대어 감는 모습
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet night, soft fabric handling
```

### CUT 34 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 가로등 하나만 켜진 어두운 동네 골목, 쌓여 있는 폐지 더미들과 낡은 셔터문들, 옅은 밤안개, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 고쳐진 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카를 새벽 어스름 속에 혼자 밀고 걸어가 할머니의 평소 자리에 조용히 세워두는 모습
[CAMERA]
Movement: Follow shot, camera behind Kim at shoulder height
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Long shot throughout, Eye-level
End: ends as he sets the cart down and walks away, hold for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] pre-dawn quiet street ambience, single cart wheel creak, distant rooster
```

## 다음날 아침 캡션

### CUT 35 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터 인근 골목, 이른 아침 옅은 안개, 사람이 한 명도 없는, 인물 없음
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the setting in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] none — quiet natural room tone only
```

## 6막 — 결말

### CUT 36 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터 인근 골목, 이른 아침, 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카를 발견하고 놀라 다가가는 장면
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the grandmother in frame, Medium throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] the grandmother (Korean, [trembling, tender]): "…영감이 감아준 건데…"
[SOUND] quiet morning ambience, birds
```

### CUT 37 (10s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카 손잡이의 가죽끈을 두 손으로 감싸 쓰다듬는 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)의 손, 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터 배경, 이른 아침, 한국어로 대사하며
[CAMERA]
Movement: Slow zoom in, camera locked
Speed: natural, unhurried
Framing: keep the grandmother in frame, Close-up throughout, Eye-level
End: hold on her trembling hands
[DURATION] 10 seconds
[DIALOGUE] the grandmother (Korean, [trembling, tender]): "…영감이 감아준 건데…"
[SOUND] quiet morning ambience
```

### CUT 38 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)의 얼굴, 눈물이 고인 채 옅은 미소, 재개발 철거가 한창인 공터, 무너진 담벼락 잔해와 뿌연 흙먼지, 안전 펜스와 아무 글자도 없는 매끈한 흰색 안내판, 인적 없는 공터 배경, 이른 아침
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the grandmother in frame, Choker throughout, Eye-level
End: hold on her tearful smile
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet morning ambience
```

### CUT 39 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet, the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly two people in frame: the grandmother, the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, desaturated sepia-toned palette, soft grain, memory-like. No blood.
[SCENE] 십 년 전 겨울 회상 장면, 눈 내리는 어두운 골목에서 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)에게 김이 모락모락 나는 삶은 옥수수를 말없이 건네는 모습, 세피아 톤, 짧은 인서트
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the full cast in frame, Medium throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] soft snowfall silence, distant winter wind
```

### CUT 40 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판 앞 창턱, 이른 아침 햇살, 김이 모락모락 나는 삶은 옥수수가 담긴 작은 봉지 하나가 놓여 있는 모습, 사람이 한 명도 없는, 인물 없음
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the setting in frame, Close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet morning ambience
```

### CUT 41 (5s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판, 이른 아침, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 창턱의 옥수수 봉지를 발견하고 손에 들어보며 옅은 미소를 짓는 장면
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Medium close-up throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] quiet morning office ambience
```

### CUT 42 (5s)
```
[LOCK] Use the "GRANDMOTHER" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the grandmother. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 아파트 단지 정문 앞 인도, 화단과 낮은 담장, 아침 햇살 속 70대 후반 한국 여성(마르고 굽은 허리, 깊은 주름진 얼굴, 색 바랜 갈색 꽃무늬 두건을 머리에 두르고, 무늬 없는 낡은 밤색 몸빼 바지와 두꺼운 남색 누빔 점퍼, 해진 목장갑)가 다시 손잡이에 낡고 해진 갈색 가죽끈이 감긴, 여기저기 녹슨 폐지 리어카를 끌고 걸어가는 모습, 힘찬 걸음
[CAMERA]
Movement: Side tracking, camera moves parallel to the grandmother
Speed: natural, unhurried
Framing: keep the grandmother in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] cart wheel rolling smoothly, quiet morning street
```

## 엔딩 카드

### CUT 43 (10s)
```
[LOCK] Use the "GUARD KIM" reference character sheet for face and wardrobe only. Do not remove the background. Exactly one person in frame: the guard (Kim). Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판 앞, 60대 초반 한국 남성 아파트 경비원(둥근 얼굴, 짧고 단정한 반백 스포츠머리, 무늬 없는 짙은 감색 경비복 유니폼, 왼쪽 가슴에 아무 글자도 없는 매끈한 흰색 명찰표, 허리에 낡은 무전기)이 뒷모습으로 서서 조용히 단지를 바라보는 모습, 저녁 어스름
[CAMERA]
Movement: Static rear shot, back of Kim fills frame
Speed: natural, unhurried
Framing: keep the guard (Kim) in frame, Long shot throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 10 seconds
[DIALOGUE] none
[SOUND] quiet evening ambience
```

## 다음 편 예고

### CUT 44 (5s)
```
[LOCK] Use the reference character sheets for face and wardrobe only. Do not remove the background. Exactly zero people in frame — an empty shot, no one present. Photorealistic live-action, Kodak 35mm film grain, 24fps, 16:9, muted warm naturalistic palette, gentle late-autumn Korean apartment complex tones. No blood.
[SCENE] 작은 아파트 경비실 부스 내부, 낡은 흑백 CCTV 모니터 여러 대와 보온병이 놓인 좁은 책상, 창밖으로 단지 화단이 보임, 벽에는 아무 글자도 없는 매끈한 근무표 칠판 창가, 작은 트리 장식이 살짝 보이는 겨울 예고 컷, 사람이 한 명도 없는, 인물 없음
[CAMERA]
Movement: Static, locked off
Speed: natural, unhurried
Framing: keep the setting in frame, Medium throughout, Eye-level
End: hold on the final frame for the last second
[DURATION] 5 seconds
[DIALOGUE] none
[SOUND] none — quiet natural room tone only
```

