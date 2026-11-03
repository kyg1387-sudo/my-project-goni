#!/usr/bin/env python3
"""다른 작품 세션과 충돌 없이 실행해도 되는지 검사(무료, 읽기 전용). 고니감독님 지시 2026-11-03 「충돌하면 안 돼, 위험하면 늦어도 괜찮으니 멈췄다가 안전할 때」.
사용법: python3 scripts/safe_to_run.py <우리 브랜치> [kind]   kind = image(키프레임·시트) / lipsync(립싱크·burn) / any
판정: 다른 브랜치에 진행 중(queued·in_progress) 실행이 하나라도 있으면 「대기」 — 립싱크는 fal 대기열을 막아 결과 없이 취소된 실증(제19장 18),
      이미지 생성도 잔액·대기열을 같이 쓰므로 기본은 대기. 우리 브랜치에 진행 중 실행이 있으면 푸시·새 실행 모두 대기(제7장 9)."""
import json, sys, urllib.request
REPO = "kyg1387-sudo/my-project-goni"
ours = sys.argv[1] if len(sys.argv) > 1 else "claude/aihaha-ja"
kind = sys.argv[2] if len(sys.argv) > 2 else "any"
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"Accept": "application/vnd.github+json", "User-Agent": "safe-to-run"}), timeout=30) as r:
        return json.load(r)
runs = []
for st in ("in_progress", "queued"):
    runs += get(f"https://api.github.com/repos/{REPO}/actions/runs?status={st}&per_page=50")["workflow_runs"]
busy = []
for r in runs:
    jobs = [j["name"] for j in get(r["jobs_url"])["jobs"] if j["conclusion"] != "skipped"]
    busy.append((r["run_number"], r["head_branch"], r["name"], r["status"], jobs))
mine = [b for b in busy if b[1] == ours]
other = [b for b in busy if b[1] != ours]
for b in busy:
    print(f"#{b[0]} {b[1]} {b[2]} {b[3]} 작업={','.join(b[4]) or '-'}")
if mine:
    print("판정: 대기 — 우리 브랜치 실행 진행 중(푸시·새 실행 금지)"); sys.exit(2)
if other:
    print(f"판정: 대기 — 다른 브랜치 실행 {len(other)}건 진행 중({kind}). 끝난 뒤 다시 검사"); sys.exit(1)
print("판정: 안전 — 진행 중인 실행 없음"); sys.exit(0)
