#!/usr/bin/env python3
"""ElevenLabs 오디션 결과 → 배역별 청취 묶음 mp3 + 청취 순서표(무료, 로컬 ffmpeg).
사용법: python3 productions/aihaha-ja/build_listen.py
입력: assets/auditions/aihaha-el-cast/*.mp3, assets/auditions/aihaha-el-haha/*.mp3 (+ el_ja_voices.jsonl)
출력: productions/aihaha-ja/PHASE1_청취/<배역>_청취묶음.mp3, 00_청취순서표.md
묶음 순서: 후보1 A → (0.8초) → 후보1 B → (1.6초) → 후보2 A … — 같은 대사를 후보끼리 비교하기 쉽게 후보별로 A·B 연속.
"""
import glob, json, os, re, subprocess, collections
ROOT = 'assets/auditions'
OUT = 'productions/aihaha-ja/PHASE1_청취'
ROLE_KO = {'yukiko': '由紀子(주인공·내레이션)', 'haha': '어머니 佐和子(A·B 진짜 / C 가짜 비디오레터)',
           'oji': '숙부 剛', 'oba': '숙모 頼子', 'shota': '사촌 翔太', 'miyashita': '형사 宮下'}
os.makedirs(OUT, exist_ok=True)
files = sorted(glob.glob(f'{ROOT}/aihaha-el-cast/*.mp3') + glob.glob(f'{ROOT}/aihaha-el-haha/*.mp3'))
groups = collections.OrderedDict()
for f in files:
    m = re.match(r'(\w+?)_EL(\d)-(.+?)_([A-C])\.mp3$', os.path.basename(f))
    if not m: continue
    role, cand, name, line = m.groups()
    groups.setdefault(role, collections.OrderedDict()).setdefault((int(cand), name), {})[line] = f
def dur(f):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).decode().strip())
rows = []
for role, cands in groups.items():
    seq = []
    for (ci, name), lines in sorted(cands.items()):
        for k, lid in enumerate(sorted(lines)):
            seq.append((lines[lid], 0.8 if k else (1.6 if seq else 0.0)))
            rows.append((role, ci, name, lid, round(dur(lines[lid]), 2)))
    inputs, filt, n = [], [], 0
    for f, gap in seq:
        if gap:
            inputs += ['-f', 'lavfi', '-t', str(gap), '-i', 'anullsrc=r=44100:cl=mono']; n += 1
        inputs += ['-i', f]; n += 1
    filt = ''.join(f'[{i}:a]aresample=44100,aformat=channel_layouts=mono[a{i}];' for i in range(n)) + ''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1[o]'
    out = f'{OUT}/{role}_청취묶음.mp3'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', filt, '-map', '[o]', '-b:a', '160k', out], check=True)
    print('묶음', out)
voices = {}
for jl in glob.glob(f'{ROOT}/aihaha-el-*/*.jsonl'):
    for l in open(jl, encoding='utf-8'):
        try: d = json.loads(l); voices[(d['role'], d['cand'])] = d
        except Exception: pass
with open(f'{OUT}/00_청취순서표.md', 'w', encoding='utf-8') as w:
    w.write('# 『母が遺したビデオレター』 ElevenLabs 오디션 청취 순서표\n\n각 묶음은 후보1 A → B → 후보2 A → B … 순서(후보 사이 1.6초, 대사 사이 0.8초). A = 평상, B = 감정 정점, (어머니만) C = 같은 목소리로 만든 가짜 비디오레터.\n\n')
    w.write('| 배역 | 후보 | 목소리 | 대사 | 길이(초) | 고니감독님 선택 |\n|---|---|---|---|---|---|\n')
    for role, ci, name, lid, d in rows:
        v = voices.get((role, ci), {})
        w.write(f"| {ROLE_KO.get(role, role)} | {ci} | {name}{(' · ' + str(v.get('age') or '') + ' ' + str(v.get('accent') or '')) if v else ''} | {lid} | {d} | |\n")
print('순서표', f'{OUT}/00_청취순서표.md', len(rows), '샘플')
