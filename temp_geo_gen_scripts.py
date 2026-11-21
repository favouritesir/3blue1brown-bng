from pathlib import Path

ROOT = Path('departments/learning_paths/stem_mathematics/3blue1brown_courses')
TPL = Path('temp_geo_build_template.py').read_text(encoding='utf-8')

LESSONS = [
    (1, 'GNcFjFmqEc8', "But why is a sphere's surface area four times its shadow?"),
    (2, 'pQa_tWZmlGs', 'Why slicing a cone gives an ellipse'),
    (3, 'fsLh-NYhOoU', 'The most underappreciated formula | Exploring high-dimensional spheres'),
    (4, 'd4EgbgTm0Bg', 'Visualizing quaternions (4d numbers) with stereographic projection'),
    (5, 'zjMuIxRvygQ', 'Quaternions and 3d rotation, explained interactively'),
    (6, 'zwAD6dRSVyI', 'Thinking outside the 10-dimensional box'),
]

for n, vid, title in LESSONS:
    nn = f'{n:02d}'
    out = (ROOT / 'geometry' / f'lesson_{nn}' / 'dubbing_pipeline' /
           'experiments' / 'clean_timesync_v2' / f'build_geo{nn}_clean.py')
    txt = (TPL.replace('@@NN@@', nn)
              .replace('@@N@@', str(n))
              .replace('@@VIDEO_ID@@', vid)
              .replace('@@TITLE@@', title))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(txt, encoding='utf-8')
    # syntax check
    import py_compile
    py_compile.compile(str(out), doraise=True)
    print(f'WROTE {out} ({len(txt)} chars)')
print('DONE')
