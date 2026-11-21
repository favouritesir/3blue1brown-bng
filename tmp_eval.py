import soundfile as sf, numpy as np, re
base = r'departments\media_production\youtube_channels\wow_english\kids_education\steve_and_maggie_school_stories_senses'
orig, sr = sf.read(base + r'\raw_sources\original_audio.wav')
orig = np.asarray(orig, dtype=np.float64)
srt = open(base + r'\raw_sources\WL8qVKfw0Dk.en.srt', encoding='utf-8').read()
def tms(s):
    h, m, rest = s.split(':'); sec, ms = rest.split(',')
    return int(h)*3600 + int(m)*60 + int(sec) + int(ms)/1000
iv = [(tms(a), tms(b)) for a, b in re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', srt)]
hop = int(sr*0.01); nfr = len(orig)//hop
speech = np.zeros(nfr, bool)
for a, b in iv:
    speech[int(a*sr/hop):int(b*sr/hop)] = True
stems = ['nemotron_3_5_super_vl','nemotron_3_ultra_550b','nemotron_3_nano_omni','mistral_large_4','gh_auto_omniroute']
print('%-28s %12s %10s %12s %12s %8s' % ('model','corr(orig,sp)','candA rms','spchFRM mean','corr(candA,sp)','peak'))
best = None
for m in stems:
    try:
        sp, _ = sf.read(base + '\\isolated_stems\\' + m + '\\speech_isolated.wav')
        sp = np.asarray(sp, dtype=np.float64)
        cand = orig - sp
        cam = cand.mean(axis=1); sm = sp.mean(axis=1); om = orig.mean(axis=1)
        c1 = float(np.dot(om, sm)/np.sqrt(np.dot(om, om)*np.dot(sm, sm)))
        rms = float(np.sqrt(np.mean(cand**2)))
        ca = np.array([np.sqrt(np.mean(cand[i*hop:(i+1)*hop]**2)) for i in range(nfr)])
        sfm = float(ca[speech].mean())
        c2 = float(np.dot(cam, sm)/np.sqrt(np.dot(cam, cam)*np.dot(sm, sm)))
        pk = float(np.max(np.abs(cand)))
        print('%-28s %12.4f %10.4f %12.5f %12.4f %8.3f' % (m, c1, rms, sfm, c2, pk))
        if best is None or c2 < best[1]:
            best = (m, c2, rms, sfm, c1, cand)
    except Exception as e:
        print(m, 'ERR', e)
print('BEST:', best[0], 'candA-speech corr', best[1])
np.save('/tmp/best_candA.npy', best[5])
import json
json.dump(best[0], open('/tmp/best_model.txt','w'))
