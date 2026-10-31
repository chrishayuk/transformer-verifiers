import json,sys,glob,re,os
P=sys.argv[1]
IDS=sys.argv[2:]
IMPL=re.compile(r'refcheck/|AMBIGUITIES|tests/|BRIEF\.md|NEEDS\.md|CHECKER-PUBLICATION|AMB-022|checker-run-')
for i in IDS:
    f=glob.glob(P+f'/**/subagents/agent-{i}*.jsonl',recursive=True)[0]
    print('==',i)
    for line in open(f):
        try:o=json.loads(line)
        except:continue
        m=o.get('message',{})
        if m.get('role')!='assistant' or not isinstance(m.get('content'),list):continue
        for c in m['content']:
            if c.get('type')!='tool_use':continue
            s=json.dumps(c.get('input'))
            if re.search(r'transformers?-verifiers/checker\b|checker-src|CHECKER-PUBLICATION|AMB-022|checker-run-',s):
                kind='IMPL' if IMPL.search(s) else 'other'
                print(' ',o.get('timestamp','')[:19],kind,c['name'],s[:200].replace('\\n',' '))
