"""Run geometry dubbing build scripts sequentially, logging each to its own file."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path('departments/learning_paths/stem_mathematics/3blue1brown_courses')

lessons = [int(x) for x in sys.argv[1:]] or list(range(1, 7))
for n in lessons:
    nn = f'{n:02d}'
    script = (ROOT / 'geometry' / f'lesson_{nn}' / 'dubbing_pipeline' /
              'experiments' / 'clean_timesync_v2' / f'build_geo{nn}_clean.py')
    log = Path(f'temp_geo_build_{nn}.log')
    print(f'=== START L{nn} {script} ===', flush=True)
    t0 = time.time()
    with open(log, 'wb') as fh:
        p = subprocess.Popen([sys.executable, str(script)], stdout=fh,
                             stderr=subprocess.STDOUT, cwd=str(Path.cwd()))
        rc = p.wait()
    dt = time.time() - t0
    print(f'=== END L{nn} rc={rc} elapsed={dt:.1f}s log={log} ===', flush=True)
    if rc != 0:
        print(f'!!! L{nn} FAILED, tail of log:', flush=True)
        print('\n'.join(log.read_text(encoding='utf-8', errors='ignore').splitlines()[-30:]), flush=True)
print('ALL REQUESTED BUILDS FINISHED', flush=True)
