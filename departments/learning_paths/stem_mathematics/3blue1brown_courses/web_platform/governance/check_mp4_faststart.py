"""Check whether MP4 moov atom is near start (faststart) or at end (seek may fail)."""
import glob, os, struct
W='departments/learning_paths/stem_mathematics/3blue1brown_courses/web_platform/media_vault'
for p in sorted(glob.glob(W+'/**/*full_dubbed*.mp4',recursive=True))[:12]:
    with open(p,'rb') as f:
        head=f.read(200000)
        moov_head=b'moov' in head
        size=os.path.getsize(p)
        f.seek(max(0,size-200000)); tail=f.read()
        moov_tail=b'moov' in tail
    print(f'{"FASTSTART" if moov_head else "MOOV-AT-END":<12} {os.path.relpath(p,W)}')
