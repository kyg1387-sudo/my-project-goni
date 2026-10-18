import sys,subprocess,os,importlib.util
spec=importlib.util.spec_from_file_location('b','productions/chika-souko-ja/build_tts.py'); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
D='assets/auditions/chika-tts'; S='/tmp/claude-0/-home-user-my-project-goni/42e6d0dd-0112-559a-bfb9-4d4fe0601ef5/scratchpad/seg'
os.makedirs(S,exist_ok=True)
def run(*a): subprocess.run(['ffmpeg','-y','-v','error',*a],check=True)
def sil(sec,out): run('-f','lavfi','-i',f'anullsrc=r=44100:cl=mono','-t',str(max(sec,0.01)),'-ar','44100','-ac','1',out)
lst=[]
lines=b.load_lines()
for n,sc,tag,spk,omni,text in lines:
    emo,inten,tempo,pre,post,note=b.T[n]
    src=f'{D}/line{b.SAME_AS.get(n,n):03d}.mp3'
    if n==36:
        laugh='assets/auditions/chika-gondo-laugh/mix_B_bellow+happy.mp3'; src=laugh; pre=0.3
    p=f'{S}/p{n:03d}.wav'; sil(pre,p); lst.append(p)
    a=f'{S}/a{n:03d}.wav'; run('-i',src,'-af','loudnorm=I=-18:TP=-2','-ar','44100','-ac','1',a); lst.append(a)
    q=f'{S}/q{n:03d}.wav'; sil(post if post else 0.6,q); lst.append(q)
open(f'{S}/list.txt','w').write(''.join(f"file '{x}'\n" for x in lst))
out='assets/auditions/chika-tts/전체청취_대본순서.mp3'
run('-f','concat','-safe','0','-i',f'{S}/list.txt','-af','loudnorm=I=-16:TP=-1.5','-ar','44100','-b:a','160k',out)
print(out, subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out],capture_output=True,text=True).stdout)
