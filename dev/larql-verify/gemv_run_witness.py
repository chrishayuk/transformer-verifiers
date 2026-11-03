import json,os,sys,time,hashlib
sys.path.insert(0,os.getcwd())
import numpy as np
from refcheck import gemv
W=os.environ['TMPDIR']+'/gemvw/w'; m=json.load(open(W+'/witness.json')); out=[]
rd=lambda s:(lambda b:(hashlib.sha256(b).hexdigest()==s['sha256'] or sys.exit('digest'),b)[1])(open(os.path.join(W,s['file']),'rb').read())
t0=time.time()
for idx,r in enumerate(m['records']):
    n,k=r['rows'],r['columns']; b=rd(r['blocks']); x=np.frombuffer(rd(r['x']),dtype='<u4'); y=np.frombuffer(rd(r['y']),dtype='<u4')
    s=gemv.check_seq(b,x,y,n,k); o=gemv.check_b1(b,x,y,n,k)
    out.append(dict(tensor=r['tensor'],call=r['call'],n=n,k=k,seq=s.status,seq_viol=s.rows_violating if hasattr(s,'rows_violating') else None,seq_reasons=list(s.reasons),b1=o.status,b1_reasons=list(o.reasons),worst_ratio=o.worst_ratio,worst_row=o.worst_ratio_row))
    print(idx,r['tensor'],n,k,s.status,o.status,o.worst_ratio[:12],f"{time.time()-t0:.0f}s",flush=True)
json.dump(dict(witness={k:m[k] for k in m if k!='records'},reference='refcheck.gemv at checker f599589',results=out),open(sys.argv[1],'w'),indent=1)
print('DONE',{ 'seq':sorted({x['seq'] for x in out}),'b1':sorted({x['b1'] for x in out}),'worst':max(float(x['worst_ratio']) for x in out)})
