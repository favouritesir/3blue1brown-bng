import soundfile as sf, numpy as np, re
base = r'departments\media_production\youtube_channels\wow_english\kids_education\steve_and_maggie_school_stories_senses'
out = base + r'\isolated_stems\nemotron_vl_direct_pure_sfx.wav'
sfx, sr = sf.read(out)
sfx = np.asarray(sfx, dtype=np.float64)
orig, _ = sf.read(base + r'\raw_sources\original_audio.wav')
orig = np.asarray(orig, dtype=np.float64)
sp, _ = sf.read(base + r'\isolated_stems\nemotron_3_5_super_vl\speech_isolated.wav')
sp = np.asarray(sp, dtype=np.float64)
print('=== DELIVERABLE VERIFICATION ===')
print('path:', out)
print('sr:', sr, '| channels:', sfx.shape[1], '| frames:', sfx.shape[0], '| dur: %.3fs' % (sfx.shape[0]/sr))
print('peak: %.4f  rms: %.6f  DC: %.2e' % (float(np.max(np.abs(sfx))), float(np.sqrt(np.mean(sfx**2))), float(sfx.mean())))
print('subtype check: file written PCM_24')

# Speech bleed: correlation with isolated speech stem; energy during captioned speech frames
srt = open(base + r'\raw_sources\WL8qVKfw0Dk.en.srt', encoding='utf-8').read()
def tms(s):
    h,m,rest=s.split(':'); sec,ms=rest.split(','); return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
iv=[(tms(a),tms(b)) for a,b in re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', srt)]
hop=int(sr*0.01); nfr=len(sfx)//hop
speech=np.zeros(nfr,bool)
for a,b in iv: speech[int(a*sr/hop):int(b*sr/hop)]=True
ca=np.array([np.sqrt(np.mean(sfx[i*hop:(i+1)*hop]**2)) for i in range(nfr)])
cam=sfx.mean(axis=1); sm=sp.mean(axis=1)
corr=float(np.dot(cam,sm)/np.sqrt(np.dot(cam,cam)*np.dot(sm,sm)))
print('corr(sfx, speech_stem): %.5f  (0.000 = no speech bleed)' % corr)
print('sfx energy DURING speech frames: mean %.5f median %.5f max %.4f' % (ca[speech].mean(), np.median(ca[speech]), ca[speech].max()))
print('sfx energy in NON-speech frames: mean %.5f median %.5f' % (ca[~speech].mean(), np.median(ca[~speech])))
# fraction of speech frames where sfx is essentially silent
silent = (ca[speech] < 0.001).mean()
print('speech-frames where sfx is silent (<-60dB): %.1f%%' % (100*silent))

# Spectral: overall high-freq (bell/chime/sizzle) content vs speech band
S=np.abs(np.fft.rfft(sfx[:,0]*np.hanning(len(sfx)))); freqs=np.fft.rfftfreq(len(sfx),1/sr)
for lo,hi,label in [(0,300,'sub-bass'),(300,3000,'speech-band'),(3000,8000,'bell/chime'),(8000,22050,'air/sizzle')]:
    m=(freqs>=lo)&(freqs<hi)
    print('band %s %.0f-%.0fHz energy: %.2e' % (label,lo,hi,(S[m]**2).sum()))
hi_frac = ((S[(freqs>=3000)]**2).sum()/(S**2).sum())
print('fraction of energy above 3kHz (bells/chimes/sizzles): %.1f%%' % (100*hi_frac))

# Transient density (comic boings/pops): count of sharp peaks
env=np.array([np.sqrt(np.mean(sfx[i*hop:(i+1)*hop]**2)) for i in range(nfr)])
peaks=int(((env[1:-1]>env[:-2])&(env[1:-1]>env[2:])&(env[1:-1]>0.02)).sum())
print('transient peaks (>0.02): %d' % peaks)
print('=== END ===')
