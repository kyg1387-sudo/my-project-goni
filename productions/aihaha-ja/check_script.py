#!/usr/bin/env python3
"""aihaha-ja 대본 규격 자동 검사 (제14장 8 · 제17장 4 ② · 제13장 1 · 제14장 7).
사용법: python3 productions/aihaha-ja/check_script.py [대본.md]
검사: 한 문장 ≤30자, 한 줄 ≤2문장, 자막 2줄×20자 안에 들어가는지(≤40자), 「あなた」 시청자 호칭, 「皆さん」, 「懲役」,
줄 번호 중복, 구간별 글자 수·줄 수.
"""
import re, sys, collections
path = sys.argv[1] if len(sys.argv) > 1 else 'productions/aihaha-ja/00_script_ja.md'
t = open(path, encoding='utf-8').read()
body = t.split('## 4. 대본')[1].split('## 5.')[0]
sec = None; rows = []
for ln in body.splitlines():
    m = re.match(r'^### (.+)', ln)
    if m: sec = m.group(1).split('·')[0].strip(); continue
    m = re.match(r'^\s*((?:NA|L|OUT)\d+\w*)\s*([^:「]*?)\s*[:：]\s*「(.+)」\s*$', ln)
    if m: rows.append((sec, m.group(1), m.group(2).strip(), m.group(3)))
P = re.compile(r"[\s、。，．・…―！？!?『』「」（）()　]")
errs = []; ids = collections.Counter(r[1] for r in rows)
for k, v in ids.items():
    if v > 1: errs.append(f'{k}: 줄 번호 중복 {v}회')
for sec_, lid, who, txt in rows:
    sents = [s for s in re.split(r'(?<=[。！？])', txt) if P.sub('', s)]
    if len(sents) > 2: errs.append(f'{lid}: 문장 {len(sents)}개(최대 2) — {txt}')
    for s in sents:
        if len(s) > 30: errs.append(f'{lid}: 문장 {len(s)}자(최대 30) — {s}')
    if len(txt) > 40: errs.append(f'{lid}: 줄 {len(txt)}자 — 자막 2줄×20자 초과 위험')
    if '懲役' in txt: errs.append(f'{lid}: 「懲役」 금지(拘禁刑)')
    if lid.startswith(('NA', 'OUT')) and ('あなた' in txt or '皆さん' in txt):
        errs.append(f'{lid}: 시청자 호칭은 「皆様」(제14장 7)')
by = collections.OrderedDict()
for sec_, lid, who, txt in rows:
    d = by.setdefault(sec_, [0, 0, 0]); d[0] += 1; d[1] += len(txt); d[2] += len(P.sub('', txt))
tot = [sum(v[i] for v in by.values()) for i in range(3)]
print(f'파일: {path}')
for k, v in by.items(): print(f'  {k:<14} 줄 {v[0]:>3} · 원문 {v[1]:>5}자 · 구두점 제외 {v[2]:>5}자')
print(f'  합계           줄 {tot[0]:>3} · 원문 {tot[1]:>5}자 · 구두점 제외 {tot[2]:>5}자')
main = [r for r in rows if not r[1].startswith('OUT')]
print(f'  본편(아웃트로 제외) 줄 {len(main)} · 원문 {sum(len(r[3]) for r in main)}자 '
      f'(직전 작품 『引きこもり』 96줄·약 1,977자 = 본편 10:06 실측)')
print('검사 결과:', '문제 0건' if not errs else f'{len(errs)}건')
for e in errs: print(' -', e)
sys.exit(1 if errs else 0)
