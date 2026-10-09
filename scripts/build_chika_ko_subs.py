#!/usr/bin/env python3
"""#02 검수용 한글 자막(.ass) 생성 — 고니감독님 지시(2026-10-08): 영상 검수 시 한글 자막을 함께 보여 준다.
00_script_ja.md의 각 대사 바로 아래 「→ 한국어」 줄을 번호 순으로 모아, subs/chika.ass의 Dialogue 타이밍·화자에 그대로 입힌다(일본어 자막 위, 작게·연노랑).
출력: subs/chika-ko.ass (검수 전용 — 본편 업로드본에는 넣지 않는다). 사용법: build_chika_ko_subs.py"""
import os, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
s = open(os.path.join(ROOT, "productions/chika-souko-ja/00_script_ja.md"), encoding="utf-8").read()
body = s[s.index("## 4. 대본"):s.index("## 5. 대사별")]
ko, pending = [], False
for ln in body.split("\n"):
    if re.match(r"^\s+(\S+?):((?:【OMNI】)?(?:\([^)]*\))?)「(.+)」", ln):
        pending = True; continue
    m = re.match(r"^\s+→\s*(.+)$", ln)
    if pending and m:
        ko.append(m.group(1).strip()); pending = False
ass = open(os.path.join(ROOT, "subs/chika.ass"), encoding="utf-8").read()
head, _, events = ass.partition("[Events]")
styles = re.findall(r"^Style: (\w+),", head, re.M)
head = re.sub(r"^Style: (\w+),([^,]+),(\d+),&H00([0-9A-F]{6}),", lambda m: f"Style: {m.group(1)},{m.group(2)},{max(30, int(int(m.group(3)) * 0.72))},&H0090F0FF,", head, flags=re.M)
def _mv(m):   # MarginL, MarginR, MarginV, Encoding — 한글은 일본어 자막(MarginV 150) 위에
    f = m.group(0).split(","); f[-2] = str(int(f[-2]) + 86); return ",".join(f)
head = re.sub(r"^Style: .*$", _mv, head, flags=re.M)
out, k = [], 0
groups, order = {}, []   # 제11장 21: 분할된 일본어 조각(Effect=line###)을 줄 단위로 묶어 한글은 줄 전체 시간에 1번
for ln in events.split("\n"):
    m = re.match(r"^Dialogue: (\d+),([^,]+),([^,]+),(\w+),([^,]*),(\d+),(\d+),(\d+),([^,]*),(.*)$", ln)
    if not m or m.group(4) in ("Emph", "Caption"):
        continue
    key = m.group(9) or f"ev{len(order):03d}"
    if key not in groups:
        groups[key] = [m]; order.append(key)
    else:
        groups[key].append(m)
for key in order:
    ms = groups[key]; m = ms[0]; last = ms[-1]
    k += 1
    if k > len(ko): break
    n_ja = max(mm.group(10).count("\\N") + 1 for mm in ms)
    mv = str(150 + 86 + 68 * (n_ja - 1)) if n_ja > 1 else m.group(8)
    out.append(f"Dialogue: {m.group(1)},{m.group(2)},{last.group(3)},{m.group(4)},{m.group(5)},{m.group(6)},{m.group(7)},{mv},{m.group(9)},{ko[k - 1]}")
open(os.path.join(ROOT, "subs/chika-ko.ass"), "w", encoding="utf-8").write(head + "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n" + "\n".join(out) + "\n")
print(f"한글 번역 {len(ko)}줄, 자막 이벤트 {len(out)}줄 → subs/chika-ko.ass")
