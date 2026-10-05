import numpy as np, json
from PIL import Image
from scipy.optimize import minimize
from textmodel import *
S='/tmp/claude-0/-home-user-videolar/382d2130-cacd-5747-84a8-97f4036a3749/scratchpad/'
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
def darkbbox(img,win,thr=55):
    x0,y0,x1,y1=win; g=img[y0:y1,x0:x1].mean(-1)
    ys,xs=np.where(g<np.median(g)-thr)
    return xs.min()+x0,ys.min()+y0,xs.max()+x0,ys.max()+y0
def fit_one(img,text,win,fonts=('OpenSans-600',),baseline_off=0.5):
    bx0,by0,bx1,by1=darkbbox(img,win)
    box=(bx0-5,by0-4,bx1+6,by1+5)
    x0,y0,x1,y1=box; crop=img[y0:y1,x0:x1]
    best=None
    for fn in fonts:
        # approx size from width: n digits tabular
        w_em=adv(fn,text)
        s0=(bx1-bx0+1)/w_em
        g=None
        for size in np.arange(s0*0.9,s0*1.12,0.2):
            for dx in np.arange(-1.5,1.6,0.5):
                for dy in np.arange(-2.5,1.6,0.5):
                    M=affine(bx0+dx-x0,by1+baseline_off+dy-y0,size)
                    a=render(fn,text,M,crop.shape[:2],0.5)
                    r=fit_linear(crop,a)[1]
                    if g is None or r<g[0]: g=(r,size,dx,dy)
        r,size,dx,dy=g
        p0=np.array([bx0+dx-x0,by1+baseline_off+dy-y0,size,1.0,0.0,0.0,0.5])
        def obj(p):
            if p[6]<0 or p[2]<4: return 1e12
            a=render(fn,text,affine(*p[:6]),crop.shape[:2],p[6]); return fit_linear(crop,a)[1]
        o=minimize(obj,p0,method='Nelder-Mead',options={'maxiter':2000,'xatol':1e-3,'fatol':1e-2})
        if best is None or o.fun<best['res']:
            p=o.x.copy(); p[0]+=x0; p[1]+=y0   # to absolute frame coords
            best=dict(font=fn,text=text,res=float(o.fun),rms=float(np.sqrt(o.fun/crop.size)),p=p.tolist(),box=[int(v) for v in box])
    return best
if __name__=='__main__':
    f10=load(S+'ref/f10.png'); f50=load(S+'ref/f50.png')
    fonts=('OpenSans-500','OpenSans-600','OpenSans-700')
    T={}
    T['form_date']=dict(ref=10.0,**fit_one(f10,'03/11/2025',(148,326,230,350),fonts),new='07/10/2026')
    T['form_amt']=dict(ref=10.0,**fit_one(f10,'2.500,00',(148,448,204,467),fonts),new='3.275,00')
    T['conf_date']=dict(ref=50.0,**fit_one(f50,'03.11.2025',(300,375,372,395),fonts),new='07.10.2026')
    T['conf_amt']=dict(ref=50.0,**fit_one(f50,'2.500,00',(300,408,354,428),fonts),new='3.275,00')
    T['conf_total']=dict(ref=50.0,**fit_one(f50,'2.500,00',(300,474,354,494),fonts),new='3.275,00')
    for k,v in T.items(): print(k,v['font'],round(v['rms'],2),np.round(v['p'],3).tolist(),v['box'])
    json.dump(T,open('targets.json','w'),indent=1)
