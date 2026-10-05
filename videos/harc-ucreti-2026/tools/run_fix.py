import os
os.environ['OMP_NUM_THREADS']='1'
import cv2, numpy as np, json, subprocess
from multiprocessing import Process
def worker(k,lo,hi):
    import patch as P
    cap=cv2.VideoCapture('cfr30.mkv'); cap.set(cv2.CAP_PROP_POS_FRAMES,lo)
    trk={n:P.Tracker(n) for n in ['form_date','form_amt']}
    outs=[]; diags={}
    for i in range(lo,hi):
        ok,f=cap.read(); out,diag=P.process_frame(trk,i,f); outs.append(out); diags[i]=diag
    np.save(f'fix_{k}.npy',np.stack(outs)); json.dump(diags,open(f'fixdiag_{k}.json','w'),default=float)
if __name__=='__main__':
    b=[1095,1123,1150,1178,1205]
    ps=[Process(target=worker,args=(k,b[k],b[k+1])) for k in range(4)]
    [p.start() for p in ps]; [p.join() for p in ps]; print('ok')
