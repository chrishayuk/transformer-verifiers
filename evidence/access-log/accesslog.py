import json,sys,glob,re,os
P=sys.argv[1]
FORBID=[r'transformers?-verifiers/checker\b', r'checker-src', r'CHECKER-PUBLICATION', r'AMB-022', r'checker-run-\d+\.log', r'scoring/run-\d+/(fieldmap|fieldnames)', r'transformer-verifiers-eval']
WRITE_REV=re.compile(r'transformer-verifiers-reviewer')
for f in sorted(glob.glob(P+'/**/subagents/*.jsonl',recursive=True)):
    calls=[];first=None;ts=[]
    for line in open(f):
        try:o=json.loads(line)
        except:continue
        if o.get('timestamp'):ts.append(o['timestamp'])
        m=o.get('message',{})
        if first is None and m.get('role')=='user':
            c=m.get('content'); first=(c if isinstance(c,str) else json.dumps(c))[:160]
        if m.get('role')=='assistant' and isinstance(m.get('content'),list):
            for c in m['content']:
                if c.get('type')=='tool_use': calls.append((c['name'],json.dumps(c.get('input'))))
    rev=sum(1 for n,s in calls if WRITE_REV.search(s))
    hits=[(n,s) for n,s in calls if any(re.search(p,s) for p in FORBID)]
    recursive=[(n,s) for n,s in calls if WRITE_REV.search(s) and (n in('Grep','Glob') or re.search(r'grep -r|grep -R|rg |find |ls -R|xargs',s))]
    print('==',os.path.basename(f),'calls',len(calls),'reviewer-repo calls',rev,'span',ts[0][:16] if ts else '',ts[-1][:16] if ts else '')
    print('   task:',first.replace('\n',' ')[:150])
    for n,s in hits: print('   HIT',n,s[:260])
    for n,s in recursive: print('   RECURSIVE',n,s[:200])
