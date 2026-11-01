# -*- coding: utf-8 -*-
"""
Black Card Ep.1 - timeline manifest builder
대본(第1話 완성대본)과 공통 메타 지침을 하나의 JSON 매니페스트로 변환하고,
타임라인 정합성(총 길이, 미드롤 위치, 발화 속도, 조명/SFX 큐)을 검증한다.

실행:  python3 build_manifest.py [--total 710]
출력:  manifest.json / timeline.csv / narration_ja.txt / subtitles_ja.srt / validation_report.md
"""
import json, csv, argparse, re, sys
from pathlib import Path

OUT = Path(__file__).parent

# ---------------------------------------------------------------- 메타
PROJECT = {
    "title_ja": "解雇された日、六本木のビルの足元で拾った\"限度額なしのブラックカード\"の正体",
    "title_ko": "해고당한 날, 롯폰기 빌딩 바닥에서 주운 '무한 한도 블랙카드'의 진짜 정체",
    "series": "Black Card",
    "episode": 1,
    "platform": "YouTube (JP)",
    "genre": "ざまぁ / dark noir",
    "aspect_ratio": "16:9",
    "letterbox": "2.39:1 cinematic bars (shorts re-cut safe area: center 9:16)",
    "fps": 24,
    "audio_mix": {"voice": 1.00, "bgm": "0.30-0.35 (low-end boost, high-shelf -3dB)", "sfx": "0.60-0.70"},
    "narration_pov": "健二 1인칭「俺」",
}

CHARACTERS = {
    "Kenji":     {"ja": "高橋 健二", "role": "주인공 43세, 나레이터", "voice": "낮고 빠른 속삭임, 감정 억제"},
    "Shibata":   {"ja": "柴田",     "role": "부장, 동기, 불륜 상대", "voice": "거만한 구어체"},
    "Misaki":    {"ja": "美咲",     "role": "아내 41세", "voice": "차가운 여성 구어체, 클라이맥스에서 끊김"},
    "Concierge": {"ja": "声",       "role": "비통지 전화 컨시어지", "voice": "완전 경어, 감정 없음, 느림"},
    "Guard":     {"ja": "警備員",   "role": "보조", "voice": "접객 경어"},
    "Driver":    {"ja": "運転手",   "role": "보조", "voice": "접객 경어"},
    "Clerk":     {"ja": "店員",     "role": "보조", "voice": "접객 경어"},
    "Manager":   {"ja": "店長",     "role": "보조", "voice": "접객 경어"},
    "President": {"ja": "社長",     "role": "보조", "voice": "당황"},
}

MIDROLLS = [150, 300, 480]  # 02:30 / 05:00 / 08:00

# 조명 큐 (지침의 4단계 매핑 + 2막 골드 전환 + 에필로그)
LIGHTING = [
    {"id": "L1", "name": "Low-key deep blue + red neon",   "start": 0,   "end": 38,
     "kelvin": 4200, "grade": "deep blue shadows, red neon spill, crushed blacks", "flicker": None,
     "note": "빗물 붉은 반사광으로 피 이미지. 광과민성 자막 00:00 표기"},
    {"id": "L2", "name": "Fluorescent green flicker",      "start": 38,  "end": 150,
     "kelvin": 5200, "grade": "green-magenta tint, -20 saturation, under-angle key", "flicker": "irregular 0.3-1.2s",
     "note": "회의실·집 공통. 플리커 깊이 15% 이내(광과민성)"},
    {"id": "L3", "name": "Cold blue -> gold/red luxury",    "start": 150, "end": 300,
     "kelvin": "5600 -> 3400", "grade": "blue until 03:25, then gold key + red neon rim; ceiling +1 stop at approval", "flicker": None,
     "note": "승인 순간(04:05 부근) 천장 조명 한 단계 상향"},
    {"id": "L4", "name": "Warm tungsten emotional spot",    "start": 300, "end": 480,
     "kelvin": 3200, "grade": "warm tungsten base, single spot on Kenji, Shibata half-face shadow (no fill)", "flicker": None,
     "note": "리무브(필 제거) 라이팅"},
    {"id": "L5", "name": "High-contrast white + red pulse", "start": 480, "end": None,
     "kelvin": 5600, "grade": "single white desk lamp, aviation-light red pulse 2s period on Kenji's half face", "flicker": "red pulse 0.5Hz",
     "note": "클라이맥스. 종료 시각은 total에 따라 계산"},
    {"id": "L6", "name": "Neon reflection warm -> cool",    "start": None, "end": None,
     "kelvin": "3000 -> 6500", "grade": "neon reflections on face, spot on card emblem only, cool shift at phone ring", "flicker": None,
     "note": "에필로그. 시작/종료는 total에 따라 계산"},
]

# ---------------------------------------------------------------- 대본 이벤트
# 이벤트 튜플:
#  ("N", speaker, ja, ko)            나레이션
#  ("D", speaker, ja, ko)            대사
#  ("P", sec, label)                 지시된 침묵/정지
#  ("V", sec, label)                 나레이션 없는 비주얼 비트
#  ("SFX", label, abs_time or None)  효과음 트리거 (None = 현재 커서 위치)
#  ("BGM", label)                    BGM 큐
#  ("SCENE", id, title, prompt_en)   씬 경계 마커
SEGMENTS = [
 {"id": "HOOK", "label": "오프닝 후크", "start": 0, "end": 38, "rate_hint": 5.5,
  "ambience": ["폭우", "롯폰기 교차로 차량 소음(원거리)", "우산 위 빗소리"],
  "events": [
   ("SCENE", "01", "빗속의 블랙카드",
    "Extreme low angle, rain-soaked asphalt behind a Roppongi high-rise at night. Matte black card in macro, red neon reflections bleeding across puddles, 120fps raindrops, low-key deep blue grade, 2.39:1."),
   ("BGM", "heartbeat bass drum 60bpm -> 90bpm, no melody"),
   ("SFX", "천둥 크랙", 3),
   ("V", 3.5, "카드 매크로 → 빗방울 슬로모션"),
   ("N", "Kenji", "十五年。魂を削って尽くした会社に、今朝、俺はゴミのように切り捨てられた。",
    "15년. 영혼을 깎아 바친 회사에서, 오늘 아침 나는 쓰레기처럼 잘려 나갔다."),
   ("SFX", "사원증 절단 シャキッ (플래시컷 0.5s)", 12),
   ("N", "Kenji", "鼻で笑った上司。冷たく背を向けた妻。虫を見るような目で俺を見た、同期の連中。",
    "코웃음 친 상사. 차갑게 등을 돌린 아내. 벌레 보듯 나를 본 동기 녀석들."),
   ("N", "Kenji", "世界が俺をどん底へ蹴り落とした、その瞬間。",
    "세상이 나를 바닥으로 걷어차 떨어뜨린 그 순간."),
   ("SFX", "서류봉투가 빗물에 떨어지는 소리", 20),
   ("P", 0.75, "「その瞬間」 뒤 침묵"),
   ("N", "Kenji", "雨のアスファルトで俺が拾ったのは、残高ゼロの通帳じゃなかった。",
    "빗물 고인 아스팔트에서 내가 집어 든 것은 잔고 0의 통장이 아니었다."),
   ("N", "Kenji", "日本の上位0.01%だけに許される、\"限度額なし\"のブラックカード。",
    "일본에서 상위 0.01%만 가질 수 있는 '한도 없는' 블랙카드."),
   ("N", "Kenji", "今夜から、あいつらに教えてやる。地獄とは、何かを。",
    "오늘 밤부터 그놈들에게 가르쳐 주겠다. 지옥이 무엇인지."),
   ("P", 0.75, "「地獄とは、何かを」 절반 속도 후 컷"),
  ]},

 {"id": "ACT1", "label": "1막 나락", "start": 38, "end": 150, "rate_hint": 5.2,
  "ambience": ["회의실: 초침, 유리벽 너머 키보드음, 수군거림 환청", "집: 냉장고 모터음, 빗물 방울"],
  "events": [
   ("SCENE", "02", "12층 유리 회의실",
    "Glass-walled meeting room on the 12th floor, telephoto voyeur shot from outside the glass, greenish fluorescent flicker, under-angle on Kenji's face. Shibata slides a resignation form across the table."),
   ("BGM", "저음 드론, 초침에 동기화, 멜로디 없음"),
   ("V", 2, "유리벽 바깥 망원 샷, 사원들 곁눈질"),
   ("D", "Shibata", "高橋。希望退職って形にしてやる。退職金は規定どおりだ。判子は――ここ。",
    "다카하시. 희망퇴직 형식으로 해 줄게. 퇴직금은 규정대로. 도장은, 여기."),
   ("D", "Kenji", "……十五年だぞ、柴田。同期だろ。", "...15년이야, 시바타. 동기잖아."),
   ("D", "Shibata", "だから、だよ。お前が隣にいると、俺の評価が下がる。",
    "그래서 그러는 거야. 네가 옆에 있으면 내 평가가 떨어지니까."),
   ("SFX", "인감이 종이에 닿는 トン", None),
   ("D", "Guard", "社員証は、こちらで処分いたします。私物は十八時以降、裏口の警備室でお受け取りください。",
    "사원증은 이쪽에서 처분합니다. 개인 짐은 18시 이후 뒷문 경비실에서 받아 가시기 바랍니다."),
   ("SFX", "사원증 절단 シャキッ", None),
   ("N", "Kenji", "解雇、ではない。\"希望退職\"。会社は、俺が自分で辞めたことにしたいらしい。",
    "해고가 아니다. '희망퇴직'. 회사는 내가 스스로 그만둔 것으로 하고 싶은 모양이다."),
   ("N", "Kenji", "抵抗すれば、次は\"追い出し部屋\"だ。", "저항하면 다음은 '쫓아내기 방'이다."),
   ("N", "Kenji", "同期の柴田は俺より三年早く部長になり、今日、俺に判子を押させる側に立っていた。",
    "동기인 시바타는 나보다 3년 빨리 부장이 되었고, 오늘 내게 도장을 찍게 하는 쪽에 서 있었다."),
   ("N", "Kenji", "ガラス越しに、部下たちが見ないふりで――全部、見ていた。",
    "유리벽 너머로 부하들이 안 보는 시늉을 하며 전부 보고 있었다."),
   ("N", "Kenji", "午前十時四十五分。十五年が、紙切れ一枚で終わった。", "오전 10시 45분. 15년이 종이 한 장으로 끝났다."),
   ("SCENE", "03", "낡은 맨션 거실",
    "Old condominium living room, afternoon, handheld micro-shake, green fluorescent flicker. Insert of a bankbook showing ¥3,218. Wife Misaki slides a stamped divorce form across the dining table, a wheeled suitcase beside her."),
   ("V", 2, "통장 잔고 3,218円 인서트"),
   ("SFX", "통장이 테이블에 내려찍히는 소리", None),
   ("D", "Misaki", "残高、見た？三千二百十八円。ローンの引き落とし、来週よ。", "잔고 봤어? 3,218엔. 대출 이체, 다음 주야."),
   ("D", "Kenji", "……話を、聞いてくれ。", "...이야기를, 들어 줘."),
   ("D", "Misaki", "聞いたわ。四十三で、無職。それが全部。もう、あなたみたいな人とは暮らせない。",
    "들었어. 43살에 무직. 그게 전부야. 더는 당신 같은 사람과 못 살아."),
   ("SFX", "離婚届 종이 마찰음 (3막 봉투와 동일 음원)", None),
   ("D", "Misaki", "あなたの欄だけ、空けておいたから。判子は――ここ。", "당신 칸만 비워 놓았어. 도장은, 여기."),
   ("N", "Kenji", "今日、二度目だ。\"判子はここ\"。", "오늘 두 번째다. '도장은 여기'."),
   ("N", "Kenji", "金がないということは――合法的に殺されても、文句を言えないということだ。",
    "돈이 없다는 것은, 합법적으로 살해당해도 할 말이 없다는 뜻이다."),
   ("N", "Kenji", "四十三歳。残ったのは、三十年ローンと、空っぽの口座と、俺を捨てた家族。",
    "43세. 남은 것은 30년 대출과 빈 통장, 나를 버린 가족."),
   ("N", "Kenji", "息ができないほどの恐怖と、腹の底から湧く、殺意に近い怒り。",
    "숨이 막히는 공포와 배 속에서 솟는 살의에 가까운 분노."),
   ("N", "Kenji", "世界は、弱い者の涙に一秒も目をくれない。すべてを失うまでは。",
    "세상은 약자의 눈물에 1초도 눈길을 주지 않는다. 모든 것을 잃기 전까지는."),
   ("P", 2.0, "BGM 완전 컷, 빗소리만"),
   ("N", "Kenji", "だが――その夜。雨の中、あのビルの裏口から追い出された、まさにその場所で。",
    "하지만 그날 밤. 빗속, 그 빌딩 뒷문에서 쫓겨난 바로 그 자리에서."),
   ("N", "Kenji", "俺のつま先に当たった\"あるもの\"が、すべてを、ひっくり返した。",
    "내 발에 차인 '어떤 것'이 모든 것을 뒤집어 놓았다."),
  ]},

 {"id": "ACT2", "label": "2막 카드의 룰", "start": 150, "end": 300, "rate_hint": 5.2,
  "ambience": ["폭우", "경비실 라디오", "택시 와이퍼", "긴자 보도 빗소리 → 쇼룸 정적"],
  "events": [
   ("SCENE", "04", "뒷문 카드 발견 → 택시",
    "POV looking down at a matte black card on rain-pooled asphalt by a building's rear exit, cold blue grade. Then taxi back seat: meter reads ¥2,340, trembling hand taps the card on the terminal, green approval light."),
   ("BGM", "심장 박동 비트 재개 70bpm"),
   ("SFX", "카드가 신발 앞코에 차이는 플라스틱음", None),
   ("V", 10, "상자 들고 퇴장, 봉투 투기, 카드에 발이 차임, 집어 들어 뒷면 문양 확인, 경비실 창"),
   ("N", "Kenji", "名前がない。番号もない。ただ、裏面に、見たことのない紋章。",
    "이름이 없다. 번호도 없다. 다만 뒷면에 본 적 없는 문양."),
   ("N", "Kenji", "届けるべきだ。頭では、分かっていた。", "신고해야 한다. 머리로는 알고 있었다."),
   ("N", "Kenji", "だが、俺の社員証をハサミで二つに切ったあの警備室に――俺は、背を向けた。",
    "하지만 내 사원증을 가위로 두 조각으로 자른 그 경비실에, 나는 등을 돌리고 말았다."),
   ("V", 4, "빗속 택시 승차, 와이퍼"),
   ("D", "Kenji", "銀座まで。", "긴자까지."),
   ("SFX", "단말기 ピッ (택시)", None),
   ("P", 3.0, "승인 대기 무음 3초"),
   ("D", "Driver", "二千三百四十円です。……はい、承認されました。ありがとうございました。",
    "2,340엔입니다. ...네, 승인되었습니다. 감사합니다."),
   ("BGM", "BPM 80"),
   ("N", "Kenji", "二千三百四十円。たったそれだけで、心臓が、壊れそうだった。",
    "2,340엔. 고작 그 금액에 심장이 터질 것 같았다."),
   ("SCENE", "05", "긴자 시계점",
    "Ginza heritage watch boutique ten minutes before closing. Soaked man with a cardboard box under his arm. Grade shifts from cold blue to gold key light with red neon rim through the window. Slow push-in on the clerk's face, macro of the receipt printing."),
   ("V", 8, "시계점 입장, 점원이 위아래로 훑어봄, 쇼케이스로 걸어가 가리킴"),
   ("D", "Clerk", "……お客様、閉店のお時間が。", "...손님, 폐점 시간이..."),
   ("D", "Kenji", "あれを。", "저걸."),
   ("D", "Clerk", "……こちらは、三千八百万円になりますが。", "...이쪽은 3,800만 엔입니다만."),
   ("D", "Kenji", "カードで。", "카드로."),
   ("SFX", "단말기 ピッ (시계점)", None),
   ("P", 3.0, "승인 대기 무음 3초"),
   ("SFX", "영수증 인쇄 ジジジ――", None),
   ("D", "Clerk", "……承認、されました。", "...승인, 되었습니다."),
   ("BGM", "BPM 100, 천장 조명 +1 stop"),
   ("V", 5, "영수증 인쇄 매크로, 점원 얼굴, 시계를 손목에 채움"),
   ("N", "Kenji", "口座に一円もない男の手に――日本経済を動かす側の\"力\"が、転がり込んだ瞬間だった。",
    "통장에 1엔도 없는 남자의 손에 일본 경제를 움직이는 쪽의 '힘'이 굴러들어온 순간이었다."),
   ("N", "Kenji", "不安は、消えた。代わりに頭を満たしたのは、ただ一つ。", "불안은 사라졌다. 대신 머리를 채운 것은 단 하나."),
   ("N", "Kenji", "\"復讐\"という名の、痺れるようなドーパミン。", "'복수'라는 이름의, 저릿한 도파민."),
   ("SCENE", "06", "빗속의 비통지 전화",
    "Rainy Ginza sidewalk at night, new watch on wrist, old phone screen reads 非通知. Distant Roppongi tower lights through the rain. BGM fully cut, only rain."),
   ("SFX", "비통지 전화 버즈 (BGM 완전 차단, 빗소리만)", None),
   ("BGM", "완전 정지"),
   ("D", "Concierge", "高橋健二様。カードのご利用を、確認いたしました。", "다카하시 켄지 님. 카드 사용을 확인했습니다."),
   ("D", "Kenji", "……誰だ。なぜ、俺の名前を。", "...누구냐. 어째서 내 이름을."),
   ("D", "Concierge", "ご質問は、お受けしておりません。ご要望だけを、お聞かせください。すべて、二十四時間以内に。",
    "질문은 받지 않습니다. 요구사항만 말씀해 주십시오. 모두 24시간 이내에."),
   ("D", "Kenji", "……何でも、か。", "...뭐든, 인가."),
   ("D", "Concierge", "何でも。", "뭐든."),
   ("V", 3, "빗속 롯폰기 빌딩 불빛을 본다"),
   ("D", "Kenji", "……あのビルの、オーナーになりたい。それと、東都商事の株を――全部。",
    "...저 빌딩의 오너가 되고 싶다. 그리고 도토상사 주식을, 전부."),
   ("D", "Concierge", "承知いたしました。", "알겠습니다."),
   ("SFX", "통화 종료음", None),
   ("V", 3, "끊긴 휴대폰, 빌딩을 올려다보는 켄지"),
   ("N", "Kenji", "翌日。俺を切り捨てた男の前に立ったとき、あいつが浮かべた表情を――俺は、一生、忘れない。",
    "다음 날. 나를 버린 남자 앞에 섰을 때 그가 지은 표정을 나는 평생 잊지 못할 것이다."),
  ]},

 {"id": "ACT3", "label": "3막 첫 번째 복수", "start": 300, "end": 480, "rate_hint": 5.0,
  "ambience": ["호텔: 도심 아침 사이렌 원음", "레스토랑: 식기음과 웅성임 → 봉투 순간 일제 정지"],
  "events": [
   ("SCENE", "07", "호텔 아침 → 회원제 레스토랑 VIP룸",
    "Roppongi hotel suite at 7am, tailored suit and a handwritten note by the door, tablet headline about a tower ownership transfer. Then a members-only restaurant private room, 3200K tungsten, single emotional spotlight on Kenji at the head seat, arc shot from behind; Shibata freezes in the doorway, half his face in shadow."),
   ("BGM", "저음 첼로와 바이올린 긴 지속음"),
   ("SFX", "신문 펼치는 소리", None),
   ("V", 10, "호텔 스위트 아침, 문 앞 정장과 메모, 넥타이 매는 손, 손목 시계, 엘리베이터"),
   ("N", "Kenji", "ホテルのドアの前には、体に合う仕立てのスーツと、一枚のメモ。", "호텔 문 앞에는 몸에 맞는 정장과 메모 한 장."),
   ("N", "Kenji", "『本日十二時、ラ・ルミエール。個室はご用意しております。』", "'오늘 12시, 라 루미에르. 개실은 준비되어 있습니다.'"),
   ("N", "Kenji", "差出人の名は、ない。", "보낸 사람의 이름은 없다."),
   ("V", 4, "태블릿 기사 인서트 「六本木グランドタワー、所有権移転」"),
   ("N", "Kenji", "ニュースの片隅に、小さな見出し。『六本木グランドタワー、所有権移転』。",
    "뉴스 한구석에 작은 제목. '롯폰기 그랜드타워, 소유권 이전'."),
   ("N", "Kenji", "二十四時間。あの声は、嘘をつかなかった。", "24시간. 그 목소리는 거짓말을 하지 않았다."),
   ("V", 10, "레스토랑 입장, 店長 인사, 상석 착석 아크 샷, 임원들 입장, 하품하던 柴田 정지"),
   ("SFX", "샴페인 코르크 ポンッ (켄지 등장 직후)", None),
   ("D", "Manager", "オーナー、お待ちしておりました。", "오너, 기다리고 있었습니다."),
   ("D", "Shibata", "た、高橋……？ここは、うちの予約席――", "다, 다카하시...? 여기는 우리 예약석..."),
   ("D", "Manager", "本日より、こちらのお席は、ビルのオーナー様のお席となっております。",
    "오늘부터 이 자리는 빌딩 오너 분의 자리입니다."),
   ("SFX", "社長 휴대폰 진동", None),
   ("D", "President", "……筆頭株主が、変わった？", "...최대주주가, 바뀌었다고?"),
   ("D", "Kenji", "株は、今朝、買わせていただきました。――柴田。座れ。", "주식은 오늘 아침 사들였습니다. 시바타. 앉아."),
   ("V", 3, "柴田이 천천히 앉는다"),
   ("SCENE", "08", "辞令 봉투",
    "Top-down and profile shots: a white envelope slides slowly across the white tablecloth into Shibata's shadowed half of frame. Room noise drops out. Shibata's chair scrapes back as his knees give."),
   ("SFX", "봉투 마찰음 (1막 離婚届과 동일 음원)", None),
   ("BGM", "정지"),
   ("V", 4, "봉투가 테이블 위를 미끄러진다, 柴田이 봉투를 연다"),
   ("D", "Kenji", "希望退職って形にしてやる。退職金は、規定どおりだ。", "희망퇴직 형식으로 해 줄게. 퇴직금은 규정대로."),
   ("D", "Shibata", "……待て、高橋。俺たち、同期だろ。", "...기다려, 다카하시. 우린 동기잖아."),
   ("D", "Kenji", "だから、だよ。お前が隣にいると――俺の評価が下がる。", "그래서 그러는 거야. 네가 옆에 있으면 내 평가가 떨어지니까."),
   ("P", 1.5, "間"),
   ("D", "Kenji", "判子は――ここ。", "도장은, 여기."),
   ("SFX", "柴田 의자가 뒤로 밀리는 소리", None),
   ("V", 4, "柴田의 무릎이 의자와 함께 무너진다, 임원들 시선"),
   ("N", "Kenji", "昨日まで俺を犬のように使っていた男が、俺の前で膝を折るまでにかかった時間は――二十四時間。",
    "어제까지 나를 개처럼 부리던 남자가 내 앞에서 무릎을 꺾기까지 걸린 시간은 24시간."),
   ("N", "Kenji", "三千八百万の時計が、俺の腕で光っていた。", "3,800만 엔 시계가 내 손목에서 반짝였다."),
   ("N", "Kenji", "だが、本当に重かったのは、時計じゃない。この、紙一枚だ。", "하지만 정말 무거웠던 것은 시계가 아니다. 이 종이 한 장이다."),
   ("N", "Kenji", "柴田が、椅子ごと後ろに崩れ落ちた。", "시바타가 의자와 함께 뒤로 무너져 내렸다."),
   ("N", "Kenji", "気持ちいい、とは思わなかった。ただ、静かだった。", "기분이 좋다고는 생각하지 않았다. 다만, 조용했다."),
   ("P", 3.0, "BGM·환경음 100% 제거"),
   ("N", "Kenji", "十五年、耳の奥で鳴り続けていた雑音が、やっと止まった。", "15년 동안 귀 안쪽에서 울리던 잡음이 마침내 멎었다."),
   ("N", "Kenji", "胸がすく――という言葉の意味を、四十三年目にして初めて知った。",
    "'가슴이 트인다'라는 말의 의미를 43년 만에 처음 알았다."),
   ("V", 3, "샴페인 잔, 창밖을 보는 켄지"),
   ("N", "Kenji", "だが、本当のクライマックスは、その夜に待っていた。", "하지만 진짜 클라이맥스는 그날 밤에 기다리고 있었다."),
   ("N", "Kenji", "俺を捨てた妻が――新しいオフィスのドアを、叩き壊すように開けたのだ。",
    "나를 버린 아내가 새 사무실 문을 부수듯 열고 들어온 것이다."),
  ]},

 {"id": "CLIMAX", "label": "클라이맥스 이중 복수", "start": 480, "end": None, "rate_hint": 5.2,
  "ambience": ["고층 공조음", "창밖 고속도로 원음", "하이힐이 대리석을 울림"],
  "events": [
   ("SCENE", "09", "구 사장실, 美咲 입장",
    "Former president's office at night, high contrast: one cold white desk lamp, red aviation light pulsing every 2 seconds through the window across half of Kenji's face. Door bursts open; Misaki, face drained white, phone in hand showing a news headline, divorce form in the other."),
   ("BGM", "드럼 비트 서서히 축적"),
   ("SFX", "문이 벽에 부딪히는 ドン", None),
   ("V", 3, "오버숄더, 켄지는 창밖을 본다"),
   ("V", 3, "美咲가 휴대폰 뉴스 화면을 들고 다가온다"),
   ("D", "Misaki", "健二……あなた、これ……本当、なの？", "켄지... 당신, 이거... 정말이야?"),
   ("D", "Kenji", "ニュースは、早いな。", "뉴스는 빠르네."),
   ("D", "Misaki", "ねぇ、あの……離婚届、まだ出してないの。私、あのときは動揺してて――ずっと、あなたを信じて――",
    "있잖아, 그... 이혼 신고서, 아직 안 냈어. 나, 그때는 동요해서... 줄곧 당신을 믿고..."),
   ("D", "Kenji", "\"四十三で、無職。それが全部\"。昨日の、君の言葉だ。", "'43살에 무직. 그게 전부야.' 어제 당신이 한 말이야."),
   ("SCENE", "10", "증거 사진과 찢어지는 離婚届",
    "Top-down: an envelope slides, photographs scatter across the glass desk; the man in the photos is Shibata. Extreme close-up on Kenji's face lit by the red pulse as he tears the divorce form in two."),
   ("SFX", "봉투 마찰음, 사진이 유리 테이블에 뿌려지는 소리", None),
   ("V", 4, "사진 탑다운, 상대의 얼굴은 柴田, 美咲의 손이 떨린다"),
   ("D", "Misaki", "……これ、どこで……", "...이거, 어디서..."),
   ("D", "Kenji", "君の家族カードは、今朝止めた。慰謝料の請求書と、財産分与ゼロの協議書。弁護士が、全部用意してくれた。",
    "당신 가족카드는 오늘 아침 정지했어. 위자료 청구서와 재산분할 0엔 협의서. 변호사가 전부 준비해 줬어."),
   ("D", "Misaki", "待って、健二、お願い。一度だけ――", "기다려, 켄지, 제발. 한 번만..."),
   ("D", "Kenji", "\"あなたの欄だけ、空けておいたから\"。", "'당신 칸만 비워 놓았어.'"),
   ("P", 1.5, "間"),
   ("SFX", "離婚届 찢어지는 ビリッ", None),
   ("BGM", "비트 정지 → 타격 한 방"),
   ("D", "Kenji", "これは、いらない。離婚は――俺の条件でする。判子は、ここ。",
    "이건 필요 없어. 이혼은 내 조건으로 한다. 도장은, 여기."),
   ("V", 3, "美咲가 무너져 앉고, 켄지는 창밖으로 돌아선다"),
   ("N", "Kenji", "真っ白な顔で、オフィスに飛び込んできた、俺を捨てた妻。",
    "하얗게 질린 얼굴로 사무실에 뛰어든, 나를 버린 아내."),
   ("N", "Kenji", "泣きながら縋る彼女の手に、俺が渡したのは――離婚届じゃなかった。",
    "울며 매달리는 그녀의 손에 내가 건넨 것은 이혼 신고서가 아니었다."),
   ("N", "Kenji", "彼女が隠してきた不倫の証拠と、慰謝料の請求書。", "그녀가 숨기고 온 불륜의 증거와 위자료 청구서."),
   ("N", "Kenji", "相手の名前は――柴田。", "상대의 이름은 시바타."),
   ("N", "Kenji", "俺を切った男と、俺を捨てた女は、同じベッドで笑っていた。", "나를 자른 남자와 나를 버린 여자는 같은 침대에서 웃고 있었다."),
   ("N", "Kenji", "他人を踏みつけて笑っていた人間に、慈悲はいらない。", "남을 짓밟으며 웃던 인간에게 자비는 필요 없다."),
   ("N", "Kenji", "俺が味わった恐怖と不安を、何倍にもして、返す。", "내가 겪은 공포와 불안을 몇 배로 돌려준다."),
   ("N", "Kenji", "それが――本物の復讐だ。", "그것이 진짜 복수다."),
   ("P", 3.0, "암전 3초"),
  ]},

 {"id": "EPILOGUE", "label": "에필로그 & CTA", "start": None, "end": None, "rate_hint": 5.2,
  "ambience": ["고급 세단 실내 주행음(거의 무음)", "와이퍼 없음, 비 개었음"],
  "events": [
   ("SCENE", "11", "렉서스 LS 뒷좌석",
    "Back seat of a Lexus LS at night, Tokyo neon flowing across Kenji's face, warm neon reflection grade. Macro on the emblem on the card's back; dissolve to the identical emblem above the tower's main entrance as the car stops at a light."),
   ("BGM", "시그니처 아웃트로 비트"),
   ("SFX", "카드를 손가락으로 돌리는 마찰음", None),
   ("V", 3, "뒷좌석 사이드 샷, 야경"),
   ("N", "Kenji", "金がなければ人間以下。金があれば神になれる街――東京。", "돈이 없으면 인간 이하, 돈이 있으면 신이 될 수 있는 도시, 도쿄."),
   ("N", "Kenji", "俺はもう、底じゃない。この巨大な食物連鎖の、一番上に座っている。",
    "나는 이제 바닥이 아니다. 이 거대한 먹이사슬의 맨 꼭대기에 앉아 있다."),
   ("N", "Kenji", "……そう、思っていた。", "...그렇게, 생각했다."),
   ("SCENE", "12", "비통지 전화 → 候補者 No.7 → 카운트다운",
    "Phone screen 非通知; grade shifts cool. Spotlight on the card emblem. The silent driver passes a thick envelope over the seat; inside, a 15-year-old interview-day photo of Kenji, red stamp on the back reading 候補者 No.7 with today's date. Dashboard clock flips 23:59 to 0:00; on-screen caption 残り7日 flickers to 残り6日. Hard blackout."),
   ("SFX", "비통지 버즈 (저주파 베이스만 남김)", None),
   ("BGM", "저주파 베이스만"),
   ("D", "Concierge", "高橋様。一点、お伝えし忘れておりました。カードの有効期限は――あと、七日です。",
    "다카하시 님. 한 가지, 말씀드리는 것을 잊었습니다. 카드의 유효기간은, 남은 7일입니다."),
   ("D", "Kenji", "……七日？その後は。", "...7일? 그 다음은."),
   ("D", "Concierge", "期限の日に、精算がございます。ビルも、株も、時計も――すべて。",
    "기한일에 정산이 있습니다. 빌딩도, 주식도, 시계도, 전부."),
   ("D", "Kenji", "精算……俺に、払えと？", "정산... 나한테, 갚으라고?"),
   ("D", "Concierge", "それをお決めになるのは、カードのオーナーです。期限の日に、オーナーが、お会いになります。",
    "그것을 결정하시는 분은 카드의 오너입니다. 기한일에 오너가 만나실 것입니다."),
   ("SFX", "통화 종료음", None),
   ("V", 2, "끊긴 전화, 카드 뒷면을 본다"),
   ("N", "Kenji", "カードの裏の紋章。", "카드 뒷면의 문양."),
   ("V", 4, "문양 매크로 → 빌딩 정문 문양 디졸브"),
   ("N", "Kenji", "それは、十五年間、毎朝くぐってきたあのビルの、正面玄関に刻まれた紋章と――同じだった。",
    "그것은 15년 동안 매일 아침 지나 들어온 그 빌딩의 정문에 새겨진 문양과 같았다."),
   ("N", "Kenji", "俺を切ったのは、本当に、あの会社だったのか。", "나를 자른 것은 정말 그 회사였나."),
   ("SFX", "운전사가 봉투를 좌석 너머로 건네는 소리", None),
   ("D", "Driver", "高橋様。オーナーより、お預かりしております。", "다카하시 님. 오너께서 맡기신 것입니다."),
   ("V", 4, "봉투를 연다. 15년 전 면접날 사진. 뒷면 붉은 스탬프 『候補者 No.7』과 오늘 날짜"),
   ("N", "Kenji", "一枚の写真。十五年前、入社面接の日の俺。", "사진 한 장. 15년 전 입사 면접 날의 나."),
   ("N", "Kenji", "裏には、赤いスタンプ。『候補者、No.7』。そして――今日の日付。", "뒷면에는 붉은 스탬프. '후보자 No.7'. 그리고 오늘 날짜."),
   ("P", 1.0, "間"),
   ("N", "Kenji", "七日。七人目。偶然じゃない。", "7일. 일곱 번째. 우연이 아니다."),
   ("N", "Kenji", "俺は、カードを拾ったんじゃない。十五年前から――\"選ばれていた\"。",
    "나는 카드를 주운 게 아니다. 15년 전부터 '선택되어 있었다'."),
   ("SFX", "대시보드 시계 23:59 → 0:00 전환 ティック", None),
   ("V", 3, "시계 0:00. 자막 「残り7日」가 깜빡이며 「残り6日」로 바뀐다"),
   ("N", "Kenji", "時計が、午前零時を回った。残り――六日。", "시계가 자정을 넘었다. 남은 시간, 6일."),
   ("BGM", "비트 복구 (CTA)"),
   ("N", "Kenji", "次回――十五年前、俺を\"候補者\"に選んだのは誰か。No.1からNo.6は、どこへ消えたのか。",
    "다음 화. 15년 전 나를 '후보자'로 뽑은 것은 누구인가. No.1부터 No.6은 어디로 사라졌는가."),
   ("N", "Kenji", "そして期限の日――ビルと株と時計の請求書は、誰の手に渡るのか。",
    "그리고 기한일, 빌딩과 주식과 시계의 청구서는 누구의 손에 넘어가는가."),
   ("N", "Kenji", "見逃したくない方は、チャンネル登録と、通知のベルをオンにしてください。",
    "놓치고 싶지 않다면 구독과 알림 설정을 켜 주세요."),
   ("N", "Kenji", "あなたなら――残り六日で、何を買い、誰に復讐しますか？コメントで、教えてください。",
    "여러분이라면 남은 6일 동안 무엇을 사고, 누구에게 복수하시겠습니까? 댓글로 알려 주세요."),
   ("SFX", "심장 박동 1회 → 블랙아웃", None),
   ("P", 1.0, "블랙아웃"),
  ]},
]

# ---------------------------------------------------------------- 계산
def nchars(s):
    return len(re.sub(r"[\s「」『』\"（）()―…]", "", s))

def tc(sec):
    sec = round(sec, 2)
    m = int(sec // 60); s = sec - m * 60
    return f"{m:02d}:{s:05.2f}"

def srt_tc(sec):
    h = int(sec // 3600); m = int((sec % 3600) // 60); s = sec % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}"

def build(total):
    # 클라이맥스/에필로그 경계: 글자 수 비례로 분배, 에필로그는 침묵 여유 포함
    seg = {s["id"]: s for s in SEGMENTS}
    rem = total - 480
    c_cl = sum(nchars(e[2]) for e in seg["CLIMAX"]["events"] if e[0] in ("N", "D"))
    c_ep = sum(nchars(e[2]) for e in seg["EPILOGUE"]["events"] if e[0] in ("N", "D"))
    fix_cl = sum(e[1] for e in seg["CLIMAX"]["events"] if e[0] in ("P", "V"))
    fix_ep = sum(e[1] for e in seg["EPILOGUE"]["events"] if e[0] in ("P", "V"))
    speech = rem - fix_cl - fix_ep
    rate = (c_cl + c_ep) / speech
    boundary = 480 + fix_cl + c_cl / rate
    boundary = round(boundary)  # 정수 초로 컷 포인트 고정
    seg["CLIMAX"]["end"] = boundary
    seg["EPILOGUE"]["start"] = boundary
    seg["EPILOGUE"]["end"] = total
    for L in LIGHTING:
        if L["id"] == "L5": L["end"] = boundary
        if L["id"] == "L6": L["start"], L["end"] = boundary, total

    timeline, scenes, sfx, bgm, warnings = [], [], [], [], []
    for s in SEGMENTS:
        D = s["end"] - s["start"]
        ev = s["events"]
        fixed = sum(e[1] for e in ev if e[0] in ("P", "V"))
        chars = sum(nchars(e[2]) for e in ev if e[0] in ("N", "D"))
        avail = D - fixed
        rate = chars / avail
        s["_rate"] = rate; s["_chars"] = chars; s["_fixed"] = fixed
        if rate > 5.8: warnings.append(f"{s['id']}: 발화 속도 {rate:.2f}자/초 - 너무 빠름(권장 ≤5.8). 나레이션 축약 또는 구간 연장 필요")
        if rate < 3.6: warnings.append(f"{s['id']}: 발화 속도 {rate:.2f}자/초 - 너무 느림(권장 ≥3.6). 비주얼 비트 추가 가능")
        cur = s["start"]
        cur_scene = None
        for e in ev:
            k = e[0]
            if k == "SCENE":
                cur_scene = {"scene": e[1], "title": e[2], "start": cur, "end": None, "segment": s["id"], "prompt_en": e[3]}
                scenes.append(cur_scene)
            elif k == "BGM":
                bgm.append({"t": cur, "cue": e[1], "segment": s["id"]})
            elif k == "SFX":
                t = e[2] if e[2] is not None else cur
                if e[2] is not None and abs(e[2] - cur) > 4:
                    warnings.append(f"SFX '{e[1]}' 고정시각 {tc(e[2])} 와 대본 흐름 커서 {tc(cur)} 차이 {abs(e[2]-cur):.1f}s")
                sfx.append({"t": t, "label": e[1], "segment": s["id"], "scene": cur_scene["scene"] if cur_scene else None})
            elif k in ("P", "V"):
                timeline.append({"start": cur, "end": cur + e[1], "type": "pause" if k == "P" else "visual",
                                 "speaker": None, "text_ja": None, "text_ko": e[2], "segment": s["id"],
                                 "scene": cur_scene["scene"] if cur_scene else None})
                cur += e[1]
            else:
                dur = nchars(e[2]) / rate
                timeline.append({"start": cur, "end": cur + dur, "type": "narration" if k == "N" else "dialogue",
                                 "speaker": e[1], "text_ja": e[2], "text_ko": e[3], "segment": s["id"],
                                 "scene": cur_scene["scene"] if cur_scene else None, "chars": nchars(e[2])})
                cur += dur
        if abs(cur - s["end"]) > 0.05:
            warnings.append(f"{s['id']}: 누적 {tc(cur)} ≠ 구간 종료 {tc(s['end'])}")
    # line_id 부여 (L001.. 발화 / P001.. 침묵·비주얼)
    nl = np_ = 0
    for t in timeline:
        if t["type"] in ("narration", "dialogue"):
            nl += 1; t["line_id"] = f"L{nl:03d}"
        else:
            np_ += 1; t["line_id"] = f"P{np_:03d}"
    # 씬 종료 시각
    for i, sc in enumerate(scenes):
        sc["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else total

    # 미드롤 검증: 각 마커가 세그먼트 경계와 일치하고, 직전 이벤트가 오픈루프 나레이션인지
    midroll_check = []
    for m in MIDROLLS:
        seg_end = [s for s in SEGMENTS if s["end"] == m]
        prev = [t for t in timeline if t["type"] == "narration" and abs(t["end"] - m) < 0.1]
        midroll_check.append({"t": tc(m), "on_segment_boundary": bool(seg_end),
                              "preceded_by_open_loop": bool(prev),
                              "last_line": prev[0]["text_ja"] if prev else None})
        if not seg_end or not prev:
            warnings.append(f"미드롤 {tc(m)}: 경계/오픈루프 조건 불충족")

    manifest = {
        "project": {**PROJECT, "total_duration_sec": total, "total_duration": tc(total)},
        "characters": CHARACTERS,
        "midroll_markers": [tc(m) for m in MIDROLLS],
        "segments": [{"id": s["id"], "label": s["label"], "start": tc(s["start"]), "end": tc(s["end"]),
                      "duration_sec": s["end"] - s["start"], "speech_chars": s["_chars"],
                      "fixed_pause_sec": s["_fixed"], "speech_rate_chars_per_sec": round(s["_rate"], 2),
                      "ambience": s["ambience"]} for s in SEGMENTS],
        "scenes": [{**sc, "start": tc(sc["start"]), "end": tc(sc["end"])} for sc in scenes],
        "lighting_cues": [{**L, "start": tc(L["start"]), "end": tc(L["end"])} for L in LIGHTING],
        "bgm_cues": [{**b, "t": tc(b["t"])} for b in bgm],
        "sfx_triggers": [{**x, "t": tc(x["t"])} for x in sorted(sfx, key=lambda x: x["t"])],
        "timeline": [{**t, "start": tc(t["start"]), "end": tc(t["end"]), "duration_sec": round(t["end"] - t["start"], 2)} for t in timeline],
        "validation": {"midroll": midroll_check, "warnings": warnings,
                       "total_speech_chars": sum(s["_chars"] for s in SEGMENTS)},
    }
    return manifest, timeline, scenes, sfx, warnings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, default=720, help="총 길이(초). 기본 720 = 12:00")
    a = ap.parse_args()
    manifest, timeline, scenes, sfx, warnings = build(a.total)

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(OUT / "timeline.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["line_id", "start", "end", "dur_s", "segment", "scene", "type", "speaker", "text_ja", "text_ko"])
        for t in manifest["timeline"]:
            w.writerow([t["line_id"], t["start"], t["end"], t["duration_sec"], t["segment"], t["scene"], t["type"], t["speaker"] or "", t["text_ja"] or "", t["text_ko"] or ""])

    lines = []
    for t in manifest["timeline"]:
        if t["type"] in ("narration", "dialogue"):
            lines.append(f"{t['line_id']} [{t['start']}] {CHARACTERS[t['speaker']]['ja']}：{t['text_ja']}")
        elif t["type"] == "pause":
            lines.append(f"[{t['start']}] （{t['duration_sec']}秒 無音：{t['text_ko']}）")
    (OUT / "narration_ja.txt").write_text("\n".join(lines), encoding="utf-8")

    srt, n = [], 1
    for t in timeline:
        if t["type"] in ("narration", "dialogue"):
            srt.append(f"{n}\n{srt_tc(t['start'])} --> {srt_tc(t['end'] - 0.05)}\n{t['text_ja']}\n"); n += 1
    (OUT / "subtitles_ja.srt").write_text("\n".join(srt), encoding="utf-8")

    rep = ["# 타임라인 검증 리포트", "", f"총 길이: {tc(a.total)}  ·  발화 총 글자 수: {manifest['validation']['total_speech_chars']}", "",
           "| 구간 | 시작 | 종료 | 길이(초) | 글자 수 | 고정 침묵(초) | 발화 속도(자/초) |", "|---|---|---|---|---|---|---|"]
    for s in manifest["segments"]:
        rep.append(f"| {s['id']} | {s['start']} | {s['end']} | {s['duration_sec']} | {s['speech_chars']} | {s['fixed_pause_sec']} | {s['speech_rate_chars_per_sec']} |")
    rep += ["", "## 미드롤", "| 마커 | 구간 경계 | 직전 오픈루프 | 직전 대사 |", "|---|---|---|---|"]
    for m in manifest["validation"]["midroll"]:
        rep.append(f"| {m['t']} | {'O' if m['on_segment_boundary'] else 'X'} | {'O' if m['preceded_by_open_loop'] else 'X'} | {m['last_line']} |")
    rep += ["", "## 경고", ""] + ([f"- {w}" for w in warnings] or ["- 없음"])
    (OUT / "validation_report.md").write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep))

if __name__ == "__main__":
    main()
