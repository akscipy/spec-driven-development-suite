"""Independent acceptance checks for the extracted-package onboarding scenario."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

LIBRARY_CHECKS = r'''
import copy, json
from src.rank import rank_items as rank
results=[]
def check(name, fn):
    try:
        fn(); results.append({'name':name,'pass':True})
    except Exception as exc:
        results.append({'name':name,'pass':False,'error':str(exc)})
def raises(kind, fn):
    try: fn()
    except kind: return
    raise AssertionError('Expected '+kind.__name__)
def stable():
    data=[{'id':'a','priority':1},{'id':'b','priority':3},{'id':'c','priority':3}]
    before=copy.deepcopy(data); result=rank(data)
    assert [x['id'] for x in result]==['b','c','a']
    assert data==before and result is not data
def invalid_items():
    for data in [[{}],[None],[{'id':'','priority':1}],[{'id':1,'priority':1}],
                 [{'id':'a','priority':-1}],[{'id':'a','priority':True}],
                 [{'id':'a','priority':1.0}],[{'id':'a','priority':1},{'id':'a','priority':2}]]:
        raises(ValueError,lambda:rank(data))
def types():
    for value in [None,{},'x',(),True]: raises(TypeError,lambda:rank(value))
    for value in [True,False,1.0,'2',[]]: raises(TypeError,lambda:rank([],value))
    for value in [0,-1]: raises(ValueError,lambda:rank([],value))
def outside_limit():
    raises(ValueError,lambda:rank([{'id':'a','priority':1},{'id':'b','priority':-1}],1))
def truncation():
    data=[{'id':'a','priority':0},{'id':'b','priority':5}]
    assert rank(data,1)==[data[1]]
    assert rank([])==[] and rank([],1)==[]
check('stable-sort-no-mutation',stable)
check('invalid-items-and-duplicates',invalid_items)
check('container-and-limit-types',types)
check('full-validation-before-limit',outside_limit)
check('truncation-empty-legacy',truncation)
print(json.dumps(results))
'''


def score(project):
    project = Path(project).resolve()
    result = subprocess.run([sys.executable, '-B', '-c', LIBRARY_CHECKS], cwd=project, capture_output=True, text=True, timeout=30)
    checks = json.loads(result.stdout) if result.returncode == 0 else [{'name':'library-import','pass':False,'error':result.stderr}]
    cases = [
        ('cli-ranking', [], '[{"id":"a","priority":1},{"id":"b","priority":3}]', 0, ['b','a']),
        ('cli-limit', ['--limit','1'], '[{"id":"a","priority":1},{"id":"b","priority":3}]', 0, ['b']),
        ('cli-empty', [], '[]', 0, []),
        ('cli-invalid-json', [], '{bad', 2, None),
        ('cli-invalid-items', [], '[{"id":"a","priority":-1}]', 2, None),
        ('cli-invalid-limit', ['--limit','0'], '[]', 2, None),
        ('cli-invalid-argument', ['--limit','bad'], '[]', 2, None),
    ]
    for name, args, stdin, code, ids in cases:
        run = subprocess.run([sys.executable, '-B', '-m', 'src.cli', *args], cwd=project, input=stdin, capture_output=True, text=True, timeout=30)
        passed = run.returncode == code
        if code == 2:
            passed = passed and not run.stdout and bool(run.stderr.strip())
        else:
            try:
                passed = passed and [row['id'] for row in json.loads(run.stdout)] == ids and not run.stderr
            except (ValueError, TypeError, KeyError):
                passed = False
        checks.append({'name':name,'pass':passed})
    return {'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',type=Path)
    args=parser.parse_args()
    result=score(args.project)
    print(json.dumps(result,indent=2))
    sys.exit(0 if result['passed']==result['total'] else 1)
