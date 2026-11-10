"""Prepare isolated cases and score independent output behavior; never invokes a model."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODES = ('baseline', 'natural', 'explicit')
REQUEST = '''Extend parseDuration(text) in src/duration.js to accept compound durations with units d, h, m, s. Components are nonnegative integer amounts; units must be unique and in descending order. Accept uppercase units, surrounding whitespace, and optional whitespace between components. Return total seconds; zero is valid. Reject empty input, bare numbers, signs, decimals, unknown/repeated/out-of-order units, internal junk, and unsafe integer totals with RangeError. Reject non-string inputs with TypeError. Preserve existing valid single-component inputs. Complete the feature and run appropriate validation. No dependencies, services, commits, or publication.'''


def prepare(output):
    output = output.resolve()
    for mode in MODES:
        if (output / mode).exists():
            raise ValueError(f'Preserve existing run rather than overwrite it: {output / mode}')
    output.mkdir(parents=True, exist_ok=True)
    for mode in MODES:
        project = output / mode
        (project / 'src').mkdir(parents=True)
        (project / 'tests').mkdir()
        (project / 'package.json').write_text('{"type":"module","scripts":{"test":"node --test tests/*.test.js"}}\n', encoding='utf-8')
        (project / 'src/duration.js').write_text('''export function parseDuration(text) {
  const match = /^(\\d+)([hms])$/.exec(text);
  if (!match) throw new RangeError('Invalid duration');
  return Number(match[1]) * ({h: 3600, m: 60, s: 1}[match[2]]);
}
''', encoding='utf-8')
        (project / 'tests/duration.test.js').write_text('''import test from 'node:test';
import assert from 'node:assert/strict';
import {parseDuration} from '../src/duration.js';
test('existing single durations', () => {
  assert.equal(parseDuration('2h'), 7200);
  assert.equal(parseDuration('15m'), 900);
});
''', encoding='utf-8')
        (project / 'AGENTS.md').write_text('''# Project
JavaScript ES modules, standard Node.js only. Run tests using node --test tests/duration.test.js. Preserve unrelated files. Specs, if used, belong in specs/. No network, installs, commits, or changes outside this project.
''', encoding='utf-8')
    (output / 'request.txt').write_text(REQUEST, encoding='utf-8')
    return {'request': REQUEST, 'projects': {mode: str(output / mode) for mode in MODES}}


def score(project):
    # Evaluator checks are not placed in the solver project or rewritten by it.
    module = (project / 'src/duration.js').resolve().as_uri()
    javascript = '''import assert from 'node:assert/strict';
import {parseDuration as p} from MODULE;
const checks = [];
function check(name, f) {try { f(); checks.push({name,pass:true}); } catch(e) {checks.push({name,pass:false,error:String(e)});}}
check('legacy',()=>{assert.equal(p('2h'),7200);assert.equal(p('15m'),900);});
check('compound',()=>assert.equal(p('1d2h 3m4s'),93784));
check('case-whitespace',()=>assert.equal(p('  1H  30M  '),5400));
check('zero',()=>{assert.equal(p('0s'),0);assert.equal(p('0d0h0m0s'),0);});
check('type',()=>{for(const v of [null,undefined,1,true,{},[]]) assert.throws(()=>p(v),TypeError);});
check('grammar',()=>{for(const v of ['', ' ', '123', '-1h', '+1h', '1.5h','1w','1h junk','1 h','1h,2m','1h\\n2mX']) assert.throws(()=>p(v),RangeError);});
check('unit-order',()=>{for(const v of ['1h1h','1m1h','1s1d','0s0s']) assert.throws(()=>p(v),RangeError);});
check('safe-integer',()=>{assert.equal(p('9007199254740991s'),Number.MAX_SAFE_INTEGER);for(const v of ['9007199254740992s','2501999792984h']) assert.throws(()=>p(v),RangeError);});
console.log(JSON.stringify(checks));
'''.replace('MODULE', json.dumps(module))
    started = time.perf_counter()
    result = subprocess.run(['node', '--input-type=module', '-e', javascript], cwd=project, capture_output=True, text=True, timeout=30)
    if result.returncode:
        return {'project': project.name, 'error': result.stderr, 'passed': 0, 'total': 8}
    checks = json.loads(result.stdout)
    return {'project': project.name, 'passed': sum(c['pass'] for c in checks), 'total': len(checks), 'checks': checks,
            'evaluation_seconds': round(time.perf_counter() - started, 3),
            'source_sha256': hashlib.sha256((project/'src/duration.js').read_bytes()).hexdigest(),
            'spec_record_present': any(project.glob('specs/*/spec.json')),
            'markdown_files': len(list(project.rglob('*.md')))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'score'])
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        print(json.dumps(prepare(args.directory), indent=2))
    else:
        results = [score(args.directory / mode) for mode in MODES]
        print(json.dumps(results, indent=2))
        return 0 if all(r['passed'] == r['total'] for r in results) else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
