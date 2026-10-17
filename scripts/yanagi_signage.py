#!/usr/bin/env python3
"""버들잎 가상 간판 「やなぎマート 鎌倉店」 디자인(평면 원화) + 로케이션 시트 합성 미리보기. 무과금(로컬).
키프레임 단계에서 같은 원화를 ja_text_overlay 방식(원근·추적)으로 외부 컷에 합성한다."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, cv2, math
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=os.path.join(ROOT,'productions','willow-leaf-ja','signage')+'/'
FD=os.path.join(ROOT,'scripts','fonts')+'/'
MARU=FD+'ZenMaruGothic-Black.ttf'; MONT=FD+'Montserrat-VF.ttf'
GREEN_T,GREEN_B=(22,128,74),(10,92,52); GOLD=(214,178,94); WHITE=(250,250,246)
def leaf(d,cx,cy,L,W,ang,fill):
    pts=[]
    for i in range(61):
        t=i/60; x=(t-0.5)*L; y=W/2*math.sin(math.pi*t)**1.15*(1-0.25*t)
        pts.append((x,y))
    pts+=[(x,-y) for x,y in reversed(pts)]
    c,s=math.cos(ang),math.sin(ang)
    d.polygon([(cx+x*c-y*s,cy+x*s+y*c) for x,y in pts],fill=fill)
def mark(size,bg=WHITE,fg=GREEN_B):
    S2=4; Z=size*S2
    im=Image.new('RGBA',(Z,Z),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.ellipse((0,0,Z-1,Z-1),fill=bg)
    # 가문(家紋) 풍 「늘어진 버들」: 굽은 줄기 + 길이가 다른 가지 5개가 바람에 살짝 흔들리며 늘어지고, 가지마다 가는 잎이 엇갈려 붙는다
    trunk=[(Z*(0.24+0.52*t), Z*(0.20+0.05*math.sin(math.pi*t))) for t in [i/30 for i in range(31)]]
    d.line(trunk,fill=fg,width=int(Z*0.022),joint='curve')
    for k,(t,ln) in enumerate([(0.0,0.46),(0.25,0.56),(0.5,0.62),(0.75,0.54),(1.0,0.44)]):
        x0,y0=trunk[int(t*30)]
        strand=[]
        for i in range(41):
            u=i/40; strand.append((x0+Z*0.06*math.sin(u*2.2)*(1 if k%2 else 0.7), y0+Z*ln*0.9*u))
        d.line(strand,fill=fg,width=int(Z*0.016),joint='curve')
        for j,u in enumerate([0.22,0.38,0.54,0.70,0.86]):
            if u*ln>ln-0.02: continue
            x,y=strand[int(u*40)]; side=1 if j%2 else -1
            ang=math.pi/2-side*0.55
            L=Z*0.10
            leaf(d,x+math.cos(ang)*L/2,y+math.sin(ang)*L/2,L,Z*0.036,ang,fg)
        x,y=strand[-1]; leaf(d,x,y+Z*0.035,Z*0.09,Z*0.036,math.pi/2,fg)
    for w,yy in [(0.40,0.86),(0.24,0.92)]:
        d.arc((Z*(0.5-w/2),Z*(yy-0.04),Z*(0.5+w/2),Z*(yy+0.04)),20,160,fill=GOLD,width=int(Z*0.024))
    return im.resize((size,size),Image.LANCZOS)
def grad(w,h):
    a=np.zeros((h,w,3),float)
    for y in range(h):
        t=y/(h-1); a[y]=np.array(GREEN_T)*(1-t)+np.array(GREEN_B)*t
    return Image.fromarray(a.astype(np.uint8))
def main_panel(W=2100,H=560):
    im=grad(W,H).convert('RGBA'); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,14),fill=WHITE); d.rectangle((0,H-46,W,H),fill=WHITE); d.rectangle((0,H-34,W,H-22),fill=GOLD)
    m=mark(380); im.alpha_composite(m,(70,(H-46-380)//2))
    f=ImageFont.truetype(MARU,236); t="やなぎマート"; bb=d.textbbox((0,0),t,font=f)
    x=500; d.text((x,52-bb[1]+10),t,font=f,fill=WHITE)
    tw=bb[2]-bb[0]
    fm=ImageFont.truetype(MONT,62); fm.set_variation_by_axes([700])
    sub="Y A N A G I   M A R T"; sw=d.textlength(sub,font=fm)
    d.text((x+(tw-sw)/2,345),sub,font=fm,fill=GOLD)
    fk=ImageFont.truetype(MARU,64); d.text((W-300,380),"鎌倉店",font=fk,fill=WHITE)
    return im
def side_panel(W=480,H=560):
    im=grad(W,H).convert('RGBA'); d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,14),fill=WHITE); d.rectangle((0,H-46,W,H),fill=WHITE); d.rectangle((0,H-34,W,H-22),fill=GOLD)
    m=mark(300); im.alpha_composite(m,((W-300)//2,40))
    fm=ImageFont.truetype(MONT,64); fm.set_variation_by_axes([800]); t="24H"; tw=d.textlength(t,font=fm)
    d.text(((W-tw)/2,385),t,font=fm,fill=WHITE)
    return im
def apply(img,art,quad,lit=1.0):
    a=np.array(img).astype(float); art=np.array(art.convert('RGB')).astype(float); h,w=art.shape[:2]
    M=cv2.getPerspectiveTransform(np.float32([(0,0),(w,0),(w,h),(0,h)]),np.float32(quad))
    p=cv2.warpPerspective(art,M,(a.shape[1],a.shape[0]),flags=cv2.INTER_AREA)
    m=cv2.warpPerspective(np.full((h,w),255,np.uint8),M,(a.shape[1],a.shape[0])).astype(float)/255
    lum=cv2.GaussianBlur(a.mean(2),(0,0),9); inside=m>0.5
    rel=np.clip(lum/ max(lum[inside].mean(),1),0.75,1.25)[...,None]
    out=p*rel*lit
    m=cv2.GaussianBlur(m,(3,3),0)[...,None]
    return Image.fromarray(np.clip(a*(1-m)+out*m,0,255).astype(np.uint8))
if __name__=='__main__':
    mp,sp=main_panel(),side_panel()
    flat=Image.new('RGB',(2100+40+480,560),(235,235,235)); flat.paste(mp,(0,0)); flat.paste(sp,(2140,0)); flat.save(D+'sign_flat.png')
    S=3
    base=Image.open(os.path.join(ROOT,'assets/portraits/yanagi-cast/cells/loc-store-ext-angles-day.png')).convert('RGB').resize((398*S,498*S),Image.LANCZOS)
    o=apply(base,mp,[(133*S,94*S),(344*S,94*S),(344*S,152*S),(133*S,152*S)])
    o=apply(o,sp,[(349*S,94*S),(398*S,94*S),(398*S,152*S),(349*S,152*S)])
    o.crop((0,40*S,398*S,380*S)).save(D+'sign_on_day.png')
