import numpy as np, json
d=dict(np.load('tracks.npz')); T=json.load(open('targets.json'))
def proj(H,p):
    q=H@[p[0],p[1],1]; return q[:2]/q[2]
rep={}
for key,tg,(lo,hi) in [('Hform','form_amt',(0,1204)),('Hconf','conf_amt',(1214,1830))]:
    H=d[key].copy()
    for i in range(len(H)):
        if not np.isnan(H[i]).any(): H[i]/=H[i][2,2]
    c=np.array(T[tg]['p'][:2])+[20,-3]
    c2=np.array(T[tg]['p'][:2])+[20,-60]
    bad=[]
    P=np.array([np.r_[proj(H[i],c),proj(H[i],c2)] if not np.isnan(H[i]).any() else [np.nan]*4 for i in range(len(H))])
    for i in range(lo,hi+1):
        if np.isnan(P[i]).any(): bad.append(i); continue
        nb=[j for j in range(i-4,i+5) if j!=i and lo<=j<=hi and not np.isnan(P[j]).any()]
        med=np.median(P[nb],0)
        if np.abs(P[i]-med).max()>5: bad.append(i)
    good=[i for i in range(lo,hi+1) if i not in bad]
    for i in bad:
        prv=max([g for g in good if g<i],default=None); nxt=min([g for g in good if g>i],default=None)
        if prv is None: H[i]=H[nxt]
        elif nxt is None: H[i]=H[prv]
        else:
            t=(i-prv)/(nxt-prv); H[i]=(1-t)*H[prv]+t*H[nxt]
    d[key]=H; rep[key]=bad
    print(key,'repaired',len(bad),bad)
np.savez('tracks_fixed.npz',**d)
