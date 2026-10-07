"""00_script_ja.md 4장에서 대사·내레이션 줄을 시간 순서로 뽑는다(장면 ID·화자·OMNI 여부·본문)."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))

def load_lines():
    t = open(os.path.join(HERE, "00_script_ja.md"), encoding="utf-8").read()
    body = t.split("## 4. 대본")[1].split("## 5.")[0]
    scene, out = "S00", []
    for l in body.split("\n"):
        s = l.strip()
        m = re.match(r"^(S\d+(?:-\d)?|OUT-\d)\b", s)
        if m:
            scene = m.group(1)
        m = re.match(r"^(NA[\d-]+|[^\s:「→\[]{1,6}):(【OMNI】)?(\([^)]*\))?「(.*)」", s)
        if m:
            out.append({"scene": scene, "spk": m.group(1), "omni": bool(m.group(2)),
                        "note": (m.group(3) or "").strip("()"), "text": m.group(4)})
    return out

if __name__ == "__main__":
    for i, x in enumerate(load_lines(), 1):
        print(i, x["scene"], x["spk"], "OMNI" if x["omni"] else "", x["text"][:40])
