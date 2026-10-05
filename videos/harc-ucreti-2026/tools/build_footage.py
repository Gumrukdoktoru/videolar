import os
os.environ['OMP_NUM_THREADS']='4'
import cv2, numpy as np, json, subprocess, sys
from scipy.ndimage import gaussian_filter1d
FPS=30; DUR=73.5; NK=int(round(DUR*FPS))
OUTW,OUTH=1080,1920; BASE=OUTW/464.0  # 2.32759
PROJ='/home/user/videolar/videos/harc-ucreti-2026'
TR=dict(np.load('tracks_fixed.npz'))
# ---------- EDL ----------
def src_of(k):
    if k<387: return 600+k, 'form'
    if k<1506: return int(round(110+(k-387)*990/1118)), 'form'
    if k<1575: return int(round(1116+(k-1506)*88/68)), 'form'
    return int(round(1246+(k-1575)*584/629)), 'conf'
SEG=lambda k: 0 if k<387 else 1 if k<1506 else 2 if k<1575 else 3
# ---------- reference rects (native, ref frame coords) ----------
R={'header':(220,92,312,125),'iban':(140,147,392,187),'alici':(141,240,387,276),'tarih':(142,321,384,357),
   'odeme':(143,383,381,418),'tutar':(144,444,380,476),'aciklama':(145,500,377,531),'devam':(146,564,374,606),
   'c_tarih':(122,375,370,397),'c_tutar':(122,407,370,430),'c_toplam':(122,472,370,495),'c_block':(122,404,370,498),'onayla':(127,537,365,570)}
SCREEN={n:('conf' if n.startswith('c_') or n=='onayla' else 'form') for n in R}
def quad(n,k):
    s,scr=src_of(k)
    if SCREEN[n]!=scr: return None
    H=TR['Hform' if scr=='form' else 'Hconf'][s]
    x0,y0,x1,y1=R[n]; P=np.array([[x0,y0,1],[x1,y0,1],[x1,y1,1],[x0,y1,1]],float).T
    q=H@P; return (q[:2]/q[2]).T
centers={}
for n in R:
    c=np.full((NK,2),np.nan)
    for k in range(NK):
        q=quad(n,k)
        if q is not None: c[k]=q.mean(0)
    # smooth per EDL segment
    cs=c.copy()
    for sg in range(4):
        idx=[k for k in range(NK) if SEG(k)==sg and not np.isnan(c[k,0])]
        if len(idx)>3: cs[idx]=gaussian_filter1d(c[idx],sigma=10,axis=0,mode='nearest')
    centers[n]=cs
# ---------- camera scenes ----------
WIDE=dict(z=1.0,L=None,T=(540,960))
def scene(z,field,T=(540,760)): return dict(z=z,L=field,T=T)
# (start time, scene, transition duration into it)
CAMS=[(0.0,dict(z=1.0,L=None,T=(540,960)),0),
      (9.2,scene(1.28,'header',(540,640)),0.8),
      (12.9,scene(1.6,'iban'),0.6),
      (18.15,scene(1.6,'alici'),0.6),
      (23.55,scene(1.68,'odeme'),0.55),
      (26.3,scene(1.62,'tarih'),0.55),
      (30.45,scene(1.62,'tutar'),0.55),
      (35.85,scene(1.68,'aciklama'),0.6),
      (50.2,scene(1.22,'devam',(540,1060)),0.55),
      (52.5,scene(1.32,'c_block',(540,800)),0),
      (52.55,scene(1.55,'c_block',(540,800)),0.9),
      (56.75,scene(1.45,'onayla',(540,900)),0.6),
      (57.9,dict(z=1.0,L=None,T=(540,960)),0.9)]
def ease(u): # power3.inOut
    u=min(max(u,0),1); return 4*u**3 if u<0.5 else 1-(-2*u+2)**3/2
def look(sc,k):
    if sc['L'] is None: return np.array([232.0,416.0])
    c=centers[sc['L']][k]
    if np.isnan(c[0]):
        return np.array([232.0,416.0])
    return c
def cam_at(k):
    t=k/FPS
    i=max(j for j,(t0,_,_) in enumerate(CAMS) if t0<=t+1e-9)
    t0,sc,d=CAMS[i]
    zB,LB,TB=sc['z'],look(sc,k),np.array(sc['T'],float)
    if i>0 and d>0 and t<t0+d:
        u=ease((t-t0)/d); pa=CAMS[i-1][1]
        zA,LA,TA=pa['z'],look(pa,k),np.array(pa['T'],float)
        z=np.exp((1-u)*np.log(zA)+u*np.log(zB)); L=(1-u)*LA+u*LB; T=(1-u)*TA+u*TB
    else: z,L,T=zB,LB,TB
    s=BASE*z
    # clamp so view stays inside native frame
    xlo=L[0]-T[0]/s; xhi=L[0]+(OUTW-T[0])/s
    if xlo<0: L[0]-=xlo
    if xhi>464: L[0]-=(xhi-464)
    ylo=L[1]-T[1]/s; yhi=L[1]+(OUTH-T[1])/s
    if ylo<0: L=np.array([L[0],L[1]-ylo])
    if yhi>832: L=np.array([L[0],L[1]-(yhi-832)])
    A=np.array([[s,0,T[0]-s*L[0]],[0,s,T[1]-s*L[1]]])
    return A,z
# ---------- blur keyframes (output px sigma) ----------
BLUR=[(0,18),(4.3,18),(5.0,7),(9.0,7),(9.7,0),(57.9,0),(58.7,16),(DUR,16)]
def blur_at(t):
    for (a,va),(b,vb) in zip(BLUR,BLUR[1:]):
        if a<=t<=b: return va+(vb-va)*ease((t-a)/(b-a)) if b>a else vb
    return 0
if __name__=='__main__':
    preview=len(sys.argv)>1
    cap=cv2.VideoCapture('patched_cfr30.mkv'); frames=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        frames.append(f)
    fix=np.concatenate([np.load(f'fix_{k}.npy') for k in range(4)])
    for j in range(len(fix)): frames[1095+j]=fix[j]
    print('frames',len(frames),flush=True)
    boxes={n:{} for n in R}; cams=[]
    ks=[int(x) for x in sys.argv[1].split(',')] if preview else range(NK)
    if not preview:
        os.makedirs(PROJ+'/assets/footage',exist_ok=True)
        enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s',f'{OUTW}x{OUTH}','-r',str(FPS),'-i','-',
            '-c:v','libx264','-preset','slow','-crf','16','-g','30','-keyint_min','30','-pix_fmt','yuv420p','-movflags','+faststart',PROJ+'/assets/footage/ekran-kaydi-duzenlenmis.mp4'],stdin=subprocess.PIPE)
    for k in ks:
        s,scr=src_of(k); A,z=cam_at(k)
        f=frames[s]
        out=cv2.warpAffine(f,A,(OUTW,OUTH),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REPLICATE)
        if z>1.05:
            amt=min(0.45,0.5*(z-1))
            bl=cv2.GaussianBlur(out,(0,0),2.0); out=cv2.addWeighted(out,1+amt,bl,-amt,0)
        b=blur_at(k/FPS)
        if b>0.3: out=cv2.GaussianBlur(out,(0,0),b)
        cams.append(round(float(A[0,0]),4))
        for n in R:
            q=quad(n,k)
            if q is None: continue
            Q=(A[:,:2]@q.T).T+A[:,2]
            cx,cy=Q.mean(0); w=np.linalg.norm(Q[1]-Q[0])/2+np.linalg.norm(Q[2]-Q[3])/2; h=np.linalg.norm(Q[3]-Q[0])/2+np.linalg.norm(Q[2]-Q[1])/2
            ang=np.degrees(np.arctan2(Q[1,1]-Q[0,1],Q[1,0]-Q[0,0]))
            boxes[n][k]=[round(cx,1),round(cy,1),round(w,1),round(h,1),round(ang,2)]
        if preview: cv2.imwrite(f'bf_{k}.jpg',out,[cv2.IMWRITE_JPEG_QUALITY,90])
        else:
            enc.stdin.write(out.tobytes())
            if k%150==0: print(k,flush=True)
    if not preview:
        enc.stdin.close(); enc.wait()
        # smooth boxes temporally a little within segments, export
        T={'fps':FPS,'n':NK,'boxes':{}}
        for n,d in boxes.items():
            ks2=sorted(d)
            arr=np.array([d[k] for k in ks2]) if ks2 else np.zeros((0,5))
            T['boxes'][n]={'k0':ks2[0] if ks2 else 0,'v':arr.round(1).tolist()}
            # assert contiguous
            if ks2: assert ks2[-1]-ks2[0]+1==len(ks2),(n,ks2[0],ks2[-1],len(ks2))
        open(PROJ+'/assets/track.js','w').write('window.TRACK='+json.dumps(T,separators=(',',':'))+';\n')
        print('done')
