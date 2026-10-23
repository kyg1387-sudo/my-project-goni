#!/usr/bin/env python3
"""대본 자동 검사(무료): 한 문장 ≤30자, 한 줄 ≤2문장, 집계·길이 추정, 1음절 감탄사, 시청자 호칭 あなた 횟수."""
import re, sys
path = sys.argv[1] if len(sys.argv) > 1 else 'productions/yamibaito-ja/00_script_ja.md'
txt = open(path, encoding='utf-8').read()
pat = re.compile(r'^\s*(NA\d+[a-z]?|L\d+[a-z]?|OUT\d+)\s*([^:：\n]*?)[:：]「(.+?)」', re.M)
rows = pat.findall(txt)
na = [r for r in rows if r[0].startswith('NA')]
ln = [r for r in rows if r[0].startswith('L')]
out = [r for r in rows if r[0].startswith('OUT')]
def clean(s): return re.sub(r'[\s　]', '', s)
bad_len, bad_cnt, anata, mono = [], [], 0, []
for tag, who, body in rows:
    sents = [s for s in re.split(r'(?<=[。！？])', body) if clean(s)]
    if len(sents) > 2: bad_cnt.append((tag, len(sents)))
    for s in sents:
        n = len(clean(re.sub(r'[。、！？…「」―]', '', s)))
        if n > 30: bad_len.append((tag, n, s))
    anata += body.count('あなた')
    if re.fullmatch(r'[ぁ-んァ-ン]{1}[。！？…]*', clean(body)): mono.append(tag)
tot = lambda rs: sum(len(clean(re.sub(r'[。、！？…「」―]', '', b))) for _,_,b in rs)
cn, cl, co = tot(na), tot(ln), tot(out)
print(f'내레이션 {len(na)}줄 {cn}자 · 대사 {len(ln)}줄 {cl}자 · 아웃트로 {len(out)}줄 {co}자 · 합계 {cn+cl+co}자')
for rate, label in ((3.5,'EL 느린 내레이터 실측'), (4.3,'보통')):
    voice = (cn+co)/rate + cl/4.5
    print(f'  말소리 {label} {rate}자/초: {voice/60:.1f}분 → 지문·여운 +2.0분 가정 시 {(voice+120)/60:.1f}분')
print('30자 초과 문장:', len(bad_len)); [print('   ', t, n, s) for t, n, s in bad_len]
print('3문장 이상 줄:', bad_cnt); print('あなた 사용 횟수:', anata, '| 1음절 감탄사:', mono)
whos = {}
for tag, who, body in ln:
    w = who.split('[')[0].split('(')[0].strip() or '?'; whos[w] = whos.get(w, 0) + 1
print('화자별 대사:', whos)
print('Omni 표시 줄:', sum(1 for _, w, _ in rows if 'Omni' in w), '| VO 줄:', sum(1 for _, w, _ in rows if 'VO' in w))
