import cv2, numpy as np, json, subprocess, sys
from multiprocessing import Process
import patch as P
N=1831; K=4
def worker(k,lo,hi):
    cap=cv2.VideoCapture('cfr30.mkv'); cap.set(cv2.CAP_PROP_POS_FRAMES,lo)
    # verify seek by reading sequentially from 0 if needed
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgr24','-s','464x832','-r','30','-i','-','-c:v','ffv1','-level','3',f'seg{k}.mkv'],stdin=subprocess.PIPE)
    trk=P.make_trackers(); diags={}
    for i in range(lo,hi):
        ok,f=cap.read()
        if not ok: break
        out,diag=P.process_frame(trk,i,f)
        enc.stdin.write(out.tobytes())
        diags[i]={n:(v if not isinstance(v,dict) else {kk:vv for kk,vv in v.items()}) for n,v in diag.items()}
        if (i-lo)%50==0: print(k,i,flush=True)
    enc.stdin.close(); enc.wait()
    json.dump(diags,open(f'diag{k}.json','w'),default=float)
if __name__=='__main__':
    # seek check
    cap=cv2.VideoCapture('cfr30.mkv'); cap.set(cv2.CAP_PROP_POS_FRAMES,1000); ok,a=cap.read()
    cap2=cv2.VideoCapture('cfr30.mkv')
    for i in range(1001): ok,b=cap2.read()
    print('seek exact:',np.array_equal(a,b),flush=True)
    bounds=[0,460,920,1380,N]
    ps=[Process(target=worker,args=(k,bounds[k],bounds[k+1])) for k in range(K)]
    [p.start() for p in ps]; [p.join() for p in ps]
    open('segs.txt','w').write(''.join(f"file 'seg{k}.mkv'\n" for k in range(K)))
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i','segs.txt','-c','copy','patched_cfr30.mkv'],check=True)
    print('done')
