import subprocess,sys,re
D=sys.argv[1]
def lufs(f):
    o=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',f,'-af','ebur128','-f','null','-'],capture_output=True,text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS',o)[-1])
# (laugh, voiced_end, line, line_lead)
pairs=[('sfx_laugh_A_sneer',1.214,'gondo_S13_line_normal',0.324,'mix_A_sneer+normal'),
       ('sfx_laugh_B_bellow',1.618,'gondo_S13_line_happy',0.109,'mix_B_bellow+happy'),
       ('sfx_laugh_C_wheeze',1.52,'gondo_S13_line_happy',0.109,'mix_C_wheeze+happy')]
GAP=0.12   # 웃음 꼬리 → 첫 음절 사이 숨 간격
TARGET=-18.0
for lg,lend,ln,lead,out in pairs:
    L=f'{D}/{lg}.mp3'; S=f'{D}/{ln}.mp3'
    gl=TARGET+1.0-lufs(L)   # 웃음은 대사보다 1dB 크게(터지는 느낌)
    gs=TARGET-lufs(S)
    delay=int((lend+GAP-lead)*1000)
    fc=(f"[0]atrim=0:{lend+0.06},afade=t=out:st={lend-0.04}:d=0.10,volume={gl}dB[l];"
        f"[1]volume={gs}dB,adelay={delay}|{delay}[s];"
        f"[l][s]amix=inputs=2:normalize=0,highpass=f=70,"
        f"aecho=0.85:0.5:45|80:0.18|0.10,"   # 같은 연회장 잔향을 둘에 함께 입혀 한 공간처럼
        f"loudnorm=I=-16:TP=-1.5:LRA=11")
    subprocess.run(['ffmpeg','-y','-v','error','-i',L,'-i',S,'-filter_complex',fc,'-ar','44100','-b:a','192k',f'{D}/{out}.mp3'],check=True)
    print(out, 'line starts at', round((delay/1000)+lead,2),'s')
