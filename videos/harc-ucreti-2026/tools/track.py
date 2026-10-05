import cv2, numpy as np, sys
from multiprocessing import Pool
sift=None; REF={}
def feats(img,mask=None,up=2):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    g=cv2.resize(g,None,fx=up,fy=up,interpolation=cv2.INTER_CUBIC)
    m=None if mask is None else cv2.resize(mask,None,fx=up,fy=up,interpolation=cv2.INTER_NEAREST)
    kp,d=sift.detectAndCompute(g,m)
    return np.float32([k.pt for k in kp])/up,d
def init():
    global sift,REF,bf
    sift=cv2.SIFT_create(); bf=cv2.BFMatcher()
    rf=cv2.imread('ref_form.png'); m=np.zeros(rf.shape[:2],np.uint8); m[230:540,120:400]=255
    REF['form']=feats(rf,m)
    rc=cv2.imread('ref_conf.png'); m=np.zeros(rc.shape[:2],np.uint8); m[290:520,90:400]=255
    REF['conf']=feats(rc,m)
def work(args):
    i,img,which=args
    kc,dc=feats(img)
    out={}
    for w in which:
        kr,dr=REF[w]
        if dc is None or len(kc)<10: out[w]=(None,0); continue
        mm=bf.knnMatch(dr,dc,k=2)
        good=[a for a,b in (p for p in mm if len(p)==2) if a.distance<0.75*b.distance]
        if len(good)<10: out[w]=(None,len(good)); continue
        src=kr[[a.queryIdx for a in good]]; dst=kc[[a.trainIdx for a in good]]
        H,inl=cv2.findHomography(src,dst,cv2.RANSAC,1.5,maxIters=4000,confidence=0.999)
        if H is None or inl is None: out[w]=(None,0); continue
        # refine with inliers only (LMEDS-free least squares)
        sel=inl.ravel().astype(bool)
        H2=None
        if sel.sum()>=8: H2,_=cv2.findHomography(src[sel],dst[sel],0)
        out[w]=(H2 if H2 is not None else H,int(sel.sum()))
    return i,out
def gen():
    cap=cv2.VideoCapture('cfr30.mkv'); i=0
    while True:
        ok,f=cap.read()
        if not ok: break
        which=[]
        if i<=1260: which.append('form')
        if i>=1140: which.append('conf')
        yield (i,f,which); i+=1
if __name__=='__main__':
    N=1831
    Hs={'form':np.full((N,3,3),np.nan),'conf':np.full((N,3,3),np.nan)}
    inl={'form':np.zeros(N,int),'conf':np.zeros(N,int)}
    with Pool(4,initializer=init) as p:
        for i,out in p.imap(work,gen(),chunksize=4):
            for w,(H,n) in out.items():
                inl[w][i]=n
                if H is not None: Hs[w][i]=H
            if i%100==0: print(i,{w:inl[w][i] for w in out},flush=True)
    np.savez('tracks.npz',Hform=Hs['form'],Hconf=Hs['conf'],iform=inl['form'],iconf=inl['conf'])
