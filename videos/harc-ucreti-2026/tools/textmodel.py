import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache
FONTDIR='/tmp/claude-0/-home-user-videolar/382d2130-cacd-5747-84a8-97f4036a3749/scratchpad/fonts/'
HS=200  # high-res font size
@lru_cache(maxsize=256)
def hires(fontname, text):
    f=ImageFont.truetype(FONTDIR+fontname+'.ttf', HS)
    l,t,r,b=f.getbbox(text, anchor='ls')
    pad=20
    W=r-l+2*pad; H=b-t+2*pad
    im=Image.new('L',(W,H),0); d=ImageDraw.Draw(im)
    ox,oy=pad-l, pad-t   # baseline-left origin location in image
    d.text((ox,oy),text,font=f,fill=255,anchor='ls')
    a=np.asarray(im,np.float32)/255.
    return a,(ox,oy),f
def adv(fontname,text):
    f=ImageFont.truetype(FONTDIR+fontname+'.ttf', HS)
    return f.getlength(text)/HS
def render(fontname, text, M, out_shape, sigma, ss=4):
    """M: 2x3 affine mapping glyph em coords (x right, y down, baseline-left origin, units of em=1) -> native pixel coords.
    returns alpha map of out_shape (h,w) native"""
    a,(ox,oy),_=hires(fontname,text)
    # hires px -> em: (p - o)/HS
    A=np.array([[1/HS,0,-ox/HS],[0,1/HS,-oy/HS],[0,0,1]])
    S=np.array([[ss,0,(ss-1)/2.],[0,ss,(ss-1)/2.],[0,0,1]])  # native -> supersampled px centers
    Mf=np.vstack([M,[0,0,1]])
    T=S@Mf@A
    h,w=out_shape
    # pre-blur hires to avoid aliasing: scale factor
    scale=np.sqrt(abs(np.linalg.det(T[:2,:2])))
    k=max(0.0,0.5/scale)
    if k>0.6: a=cv2.GaussianBlur(a,(0,0),k)
    big=cv2.warpAffine(a,T[:2],(w*ss,h*ss),flags=cv2.INTER_LINEAR,borderValue=0)
    small=cv2.resize(big,(w,h),interpolation=cv2.INTER_AREA)
    if sigma>0.05: small=cv2.GaussianBlur(small,(0,0),sigma)
    return small
def affine(x0,y0,size,sx=1.0,rot=0.0,shear=0.0):
    c,s=np.cos(rot),np.sin(rot)
    R=np.array([[c,-s],[s,c]])
    K=np.array([[size*sx, size*shear],[0,size]])
    L=R@K
    return np.array([[L[0,0],L[0,1],x0],[L[1,0],L[1,1],y0]])
def fit_linear(img, alpha, mask=None):
    """img HxWx3 float, alpha HxW. fit img_c = a_c + b_c*alpha. returns params, residual"""
    X=np.stack([np.ones_like(alpha),alpha],-1).reshape(-1,2)
    Y=img.reshape(-1,3)
    if mask is not None:
        m=mask.reshape(-1); X=X[m]; Y=Y[m]
    coef,res,_,_=np.linalg.lstsq(X,Y,rcond=None)
    pred=X@coef
    return coef, float(((Y-pred)**2).sum())
