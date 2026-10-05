import os
os.environ.setdefault('OMP_NUM_THREADS','1'); os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import numpy as np, cv2, json
cv2.setNumThreads(1)
from scipy.optimize import minimize
from textmodel import hires, adv, HS
T=json.load(open('targets.json'))
TR=dict(np.load('tracks_fixed.npz'))
RANGES={'form_date':(0,1204),'form_amt':(0,1204),'conf_date':(1214,1830),'conf_amt':(1214,1830),'conf_total':(1214,1830)}
HKEY={'form_date':'Hform','form_amt':'Hform','conf_date':'Hconf','conf_amt':'Hconf','conf_total':'Hconf'}
def affine(x0,y0,size,sx=1.0,rot=0.0,shear=0.0):
    c,s=np.cos(rot),np.sin(rot); R=np.array([[c,-s],[s,c]]); K=np.array([[size*sx,size*shear],[0,size]]); L=R@K
    return np.array([[L[0,0],L[0,1],x0],[L[1,0],L[1,1],y0]])
def compose_H(H,M,center):
    """linearize projective H at center; return affine M' ~ H∘M (both in px)"""
    p=np.array([center[0],center[1],1.]); q=H@p; w=q[2]; qc=q[:2]/w
    J=(H[:2,:2]*w - np.outer(q[:2],H[2,:2]))/(w*w)
    A=M[:,:2]; t=M[:,2]
    return np.hstack([J@A, (qc + J@(t-center))[:,None]])
def kernel(s1,s2,th):
    s1=max(s1,0.05); s2=max(s2,0.05)
    r=int(np.ceil(3*max(s1,s2)))+1
    y,x=np.mgrid[-r:r+1,-r:r+1].astype(np.float32)
    c,s=np.cos(th),np.sin(th); u=c*x+s*y; v=-s*x+c*y
    k=np.exp(-0.5*((u/s1)**2+(v/s2)**2)); return k/k.sum()
def render(font,text,M,x0,y0,w,h,blur,ss=4):
    a,(ox,oy),_=hires(font,text)
    A=np.array([[1/HS,0,-ox/HS],[0,1/HS,-oy/HS],[0,0,1]])
    Mf=np.vstack([M,[0,0,1]]); Mf=np.array([[1,0,-x0],[0,1,-y0],[0,0,1]])@Mf
    S=np.array([[ss,0,(ss-1)/2.],[0,ss,(ss-1)/2.],[0,0,1]])
    Tm=S@Mf@A
    big=cv2.warpAffine(a,Tm[:2],(w*ss,h*ss),flags=cv2.INTER_LINEAR,borderValue=0)
    sm=cv2.resize(big,(w,h),interpolation=cv2.INTER_AREA)
    return cv2.filter2D(sm,-1,kernel(*blur),borderType=cv2.BORDER_CONSTANT)
def design(alpha,w,h):
    Y,X=np.mgrid[0:h,0:w].astype(np.float32)
    return np.stack([np.ones_like(alpha),(X-w/2)/w,(Y-h/2)/h,alpha],-1).reshape(-1,4)
def linfit(crop,alpha,wts=None):
    h,w=alpha.shape; Xd=design(alpha,w,h); Y=crop.reshape(-1,3)
    if wts is None: coef=np.linalg.lstsq(Xd,Y,rcond=None)[0]
    else:
        sw=np.sqrt(wts.reshape(-1))[:,None]; coef=np.linalg.lstsq(Xd*sw,Y*sw,rcond=None)[0]
    pred=(Xd@coef).reshape(h,w,3)
    return coef,pred
class Tracker:
    def __init__(self,name):
        t=T[name]; self.name=name; self.font=t['font']; self.old=t['text']; self.new=t['new']
        p=t['p']; self.Mref=affine(*p[:6]); self.blur0=max(p[6],0.15)
        wem=adv(self.font,self.old); self.center=self.Mref@np.array([wem/2,-0.35,1.])
        self.wem=wem; self.prev=None; self.prev_i=-9
    def bbox(self,M,margin=4):
        pts=np.array([[0,-0.78],[self.wem,-0.78],[0,0.22],[self.wem,0.22]])
        q=(M[:,:2]@pts.T).T+M[:,2]
        x0=int(np.floor(q[:,0].min()))-margin; y0=int(np.floor(q[:,1].min()))-margin
        x1=int(np.ceil(q[:,0].max()))+margin; y1=int(np.ceil(q[:,1].max()))+margin
        return x0,y0,x1-x0,y1-y0
    def process(self,i,frame,out,diag):
        lo,hi=RANGES[self.name]
        if not(lo<=i<=hi): return
        H=TR[HKEY[self.name]][i]
        if np.isnan(H).any(): diag[self.name]='noH'; return
        M0=compose_H(H,self.Mref,self.center)
        x0,y0,w,h=self.bbox(M0,6)
        Hh,Ww=frame.shape[:2]
        if x0<1 or y0<1 or x0+w>Ww-1 or y0+h>Hh-1: diag[self.name]='out'; return
        crop=frame[y0:y0+h,x0:x0+w].astype(np.float32)
        def Mof(q):
            dx,dy,ds,dr=q[:4]; c,s=np.cos(dr),np.sin(dr)
            A=(1+ds)*np.array([[c,-s],[s,c]])@M0[:,:2]
            cc=M0[:,:2]@np.array([self.wem/2,-0.35])+M0[:,2]
            t=cc+np.array([dx,dy])-A@np.array([self.wem/2,-0.35])
            return np.hstack([A,t[:,None]])
        W=[np.ones((h,w),np.float32)]
        def obj(q):
            if q[4]<0.05 or q[5]<0.05 or q[4]>6 or q[5]>6: return 1e12
            a=render(self.font,self.old,Mof(q),x0,y0,w,h,(q[4],q[5],q[6]))
            coef,pred=linfit(crop,a,W[0])
            if coef[3].mean()>-20: return 1e11  # text must be darker than bg
            r=((crop-pred)**2).sum(-1)
            return float((r*W[0]).sum())
        cont=self.prev is not None and self.prev_i==i-1 and not getattr(self,'force_fresh',False)
        q,wts=self._optimize(i,obj,cont,W,crop,Mof,x0,y0,w,h)
        a=render(self.font,self.old,Mof(q),x0,y0,w,h,(q[4],q[5],q[6]))
        coef,pred=linfit(crop,a,wts)
        bad=coef[3].mean()>-75 or float(np.sqrt(((crop-pred)**2*wts[...,None]).sum()/max(wts.sum()*3,1)))>9.0
        if bad:
            W1=W[0]; W[0]=np.ones((h,w),np.float32)
            q2,w2=self._optimize(i,obj,False,W,crop,Mof,x0,y0,w,h,wide=True)
            a2=render(self.font,self.old,Mof(q2),x0,y0,w,h,(q2[4],q2[5],q2[6]))
            c2,p2=linfit(crop,a2,w2)
            r1=((crop-pred)**2).sum(-1).mean(); r2=((crop-p2)**2).sum(-1).mean()
            if r2<r1: q,wts=q2,w2
            else: W[0]=W1
        self._finish(i,frame,out,diag,q,wts,crop,Mof,x0,y0,w,h)
    def _optimize(self,i,obj,cont,W,crop,Mof,x0,y0,w,h,wide=False):
        if cont:
            q0=self.prev.copy(); grid=[(q0[0],q0[1])]+[(q0[0]+a,q0[1]+b) for a,b in ((-0.6,0),(0.6,0),(0,-0.6),(0,0.6))]
            iters=220
        else:
            b0=np.array([self.blur0,self.blur0,0.]); q0=np.concatenate([[0,0,0,0],b0])
            st=(-2.0,-1.0,0,1.0,2.0) if wide else (-1.0,0,1.0)
            grid=[(a,b) for a in st for b in st]; iters=500
        best=None
        for dx,dy in grid:
            qq=q0.copy(); qq[0]=dx; qq[1]=dy; v=obj(qq)
            if best is None or v<best[0]: best=(v,qq)
        q=best[1]
        for it in range(2):
            o=minimize(obj,q,method='Nelder-Mead',options={'maxiter':iters,'xatol':3e-3,'fatol':2.0})
            q=o.x
            a=render(self.font,self.old,Mof(q),x0,y0,w,h,(q[4],q[5],q[6]))
            coef,pred=linfit(crop,a,W[0])
            res=np.abs(crop-pred).max(-1)
            nw=np.where(res>38,0.0,1.0).astype(np.float32)
            nw=cv2.erode(nw,np.ones((3,3),np.uint8))
            if it==0 and nw.min()>0: break
            W[0]=nw
        return q,W[0]
    def _finish(self,i,frame,out,diag,q,wts,crop,Mof,x0,y0,w,h):
        self.prev=q.copy(); self.prev_i=i
        M=Mof(q); blur=(q[4],q[5],q[6])
        a_old=render(self.font,self.old,M,x0,y0,w,h,blur)
        a_new=render(self.font,self.new,M,x0,y0,w,h,blur)
        coef,pred_old=linfit(crop,a_old,wts)
        Xd_new=design(a_new,w,h); pred_new=(Xd_new@coef).reshape(h,w,3)
        resid=crop-pred_old
        # occlusion: big residual blobs
        g_old=cv2.dilate((a_old>0.04).astype(np.uint8),np.ones((3,3),np.uint8)).astype(np.float32)
        g_wide=cv2.dilate((a_old>0.02).astype(np.uint8),np.ones((5,5),np.uint8))
        occ=(np.abs(resid).max(-1)>45).astype(np.uint8)
        n,lab,st,_=cv2.connectedComponentsWithStats(occ)
        occ2=np.zeros_like(occ)
        for k in range(1,n):
            sel=lab==k
            outside=(sel & (g_wide==0)).sum()
            if st[k,4]>=10 and outside>=0.5*st[k,4]: occ2[sel]=1
        # grow occluder into glyph area it touches (finger over text)
        if occ2.any():
            big=(np.abs(resid).max(-1)>25).astype(np.uint8)
            n2,lab2,_,_=cv2.connectedComponentsWithStats(big)
            ids=np.unique(lab2[occ2>0]); ids=ids[ids>0]
            occ2=np.isin(lab2,ids).astype(np.uint8)|occ2
        occ2=cv2.dilate(occ2,np.ones((5,5),np.uint8)).astype(np.float32)
        # noise: keep residual away from old glyphs, synth inside
        bgstd=float(np.std(resid[(g_old==0)&(occ2==0)])) if ((g_old==0)&(occ2==0)).sum()>20 else 3.0
        rng=np.random.default_rng(i*7+hash(self.name)%1000)
        syn=cv2.GaussianBlur(rng.normal(0,1,(h,w)).astype(np.float32),(0,0),0.6)
        syn=syn/ (syn.std()+1e-6)*bgstd*0.8
        noise=resid*(1-g_old)[...,None]+syn[...,None]*g_old[...,None]
        synth=pred_new+noise
        # change mask
        chg=(np.abs(a_new-a_old)>0.015).astype(np.uint8)
        chg=cv2.dilate(chg,np.ones((3,3),np.uint8)).astype(np.float32)
        m=cv2.GaussianBlur(chg,(0,0),0.7)
        m=np.clip(m*1.6,0,1)*(1-cv2.GaussianBlur(occ2,(0,0),0.8))
        m=np.clip(m,0,1)[...,None]
        region=out[y0:y0+h,x0:x0+w].astype(np.float32)
        comp=region*(1-m)+synth*m
        out[y0:y0+h,x0:x0+w]=np.clip(comp,0,255).astype(np.uint8)
        diag[self.name]=dict(rms=float(np.sqrt(((crop-pred_old)**2*wts[...,None]).sum()/max(wts.sum()*3,1))),
                             b=float(coef[3].mean()),blur=[round(v,2) for v in blur],occ=int(occ2.sum()),box=[x0,y0,w,h],
                             quad=((M[:,:2]@np.array([[0,-0.75],[self.wem,-0.75],[self.wem,0.2],[0,0.2]]).T).T+M[:,2]).round(2).tolist())
def jpeg_match(out,orig,boxes,q=82):
    # emulate codec texture only inside patched boxes
    for (x0,y0,w,h) in boxes:
        X0=max(0,(x0-8)//8*8); Y0=max(0,(y0-8)//8*8); X1=min(out.shape[1],x0+w+8); Y1=min(out.shape[0],y0+h+8)
        reg=out[Y0:Y1,X0:X1]
        ok,enc=cv2.imencode('.jpg',reg,[cv2.IMWRITE_JPEG_QUALITY,q])
        dec=cv2.imdecode(enc,1)
        diff=(np.abs(reg.astype(int)-orig[Y0:Y1,X0:X1].astype(int)).max(-1)>0).astype(np.float32)
        mm=cv2.GaussianBlur(cv2.dilate(diff,np.ones((3,3),np.uint8)),(0,0),0.8)[...,None]
        out[Y0:Y1,X0:X1]=np.clip(reg*(1-mm)+dec*mm,0,255).astype(np.uint8)
NAMES=['form_date','form_amt','conf_date','conf_amt','conf_total']
def make_trackers(): return {n:Tracker(n) for n in NAMES}
def process_frame(trk,i,frame,jpeg=True):
    out=frame.copy(); diag={}
    for n,t in trk.items(): t.process(i,frame,out,diag)
    if jpeg: jpeg_match(out,frame,[d['box'] for d in diag.values() if isinstance(d,dict)])
    return out,diag
