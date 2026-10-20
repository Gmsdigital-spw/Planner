#!/usr/bin/env python3
"""Original, royalty-free background music for the Starship's videos (numpy only, no samples, no downloads).

Every track is synthesized from scratch (piano-like arpeggios, a soft pad and a bass), so there is
nothing to license and nothing that can trigger a copyright claim.

  python3 yt/build/music.py --mood emotional --seconds 48 --out music.wav [--seed 7]

Moods:
  emotional  slow minor piano (vi-IV-I-V), for sad / heartfelt / underdog stories
  tense      darker, pulsing, for mystery / drama / revenge build-ups
  uplifting  brighter major progression, for wholesome / happy payoffs
  cozy       soft warm jazz-tinged chords, for the shop's product videos
"""
import argparse, wave
import numpy as np

SR = 44100
A4 = 440.0
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def hz(name, octave):
    n = NOTE[name] + 12 * (octave + 1)  # MIDI number
    return A4 * 2 ** ((n - 69) / 12)


# chord = (root name, intervals above root)
MOODS = {
    "emotional": dict(bpm=70, prog=[("A", [0, 3, 7]), ("F", [0, 4, 7]), ("C", [0, 4, 7]), ("G", [0, 4, 7])],
                      piano=0.55, pad=0.22, bass=0.28, bright=0.55, octave=4),
    "tense": dict(bpm=84, prog=[("D", [0, 3, 7]), ("Bb", [0, 4, 7]), ("G", [0, 3, 7]), ("A", [0, 4, 7])],
                  piano=0.45, pad=0.30, bass=0.36, bright=0.40, octave=3),
    "uplifting": dict(bpm=92, prog=[("C", [0, 4, 7]), ("G", [0, 4, 7]), ("A", [0, 3, 7]), ("F", [0, 4, 7])],
                      piano=0.55, pad=0.20, bass=0.26, bright=0.70, octave=4),
    "cozy": dict(bpm=80, prog=[("F", [0, 4, 7, 11]), ("E", [0, 3, 7, 10]), ("D", [0, 3, 7, 10]), ("C", [0, 4, 7, 11])],
                 piano=0.50, pad=0.18, bass=0.22, bright=0.50, octave=4),
}


def piano_note(f, dur, vel, bright):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 7):  # harmonics with faster decay up high = soft felt-piano tone
        amp = (bright ** (k - 1)) / k
        fk = f * k * (1 + 0.0004 * k * k)  # slight stretch like a real string
        out += amp * np.sin(2 * np.pi * fk * t) * np.exp(-t * (1.6 + 0.9 * k))
    att = np.minimum(1, t / 0.006)
    return vel * out * att


def pad_chord(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.6, 0.0, 0.6):  # three slightly detuned voices = warm chorus
            out += np.sin(2 * np.pi * (f + det) * t) + 0.25 * np.sin(2 * np.pi * 2 * (f + det) * t)
    env = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.0)
    return out / (len(freqs) * 3) * np.clip(env, 0, 1)


def bass_note(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 1.2) * np.minimum(1, t / 0.02)


def reverb(x, seconds=2.4, mix=0.32, seed=1):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 3.2)
    ir[0] = 0
    ir /= np.sqrt((ir ** 2).sum())
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return (1 - mix) * x + mix * wet


def make(mood="emotional", seconds=48.0, seed=7):
    m = MOODS.get(mood, MOODS["emotional"])
    rng = np.random.default_rng(seed)
    beat = 60.0 / m["bpm"]
    bar = beat * 4
    total = int((seconds + 3) * SR)
    mix = np.zeros(total)
    patterns = [[0, 1, 2, 3, 2, 1, 0, 2], [0, 2, 1, 3, 0, 2, 1, 2], [0, 1, 2, 1, 3, 2, 1, 2]]
    pat = patterns[rng.integers(len(patterns))]
    t0 = 0.0
    i = 0
    while t0 < seconds + 1:
        root, ivs = m["prog"][i % len(m["prog"])]
        base = hz(root, m["octave"])
        tones = [base * 2 ** (iv / 12) for iv in ivs]
        arp = tones + [base * 2]  # root, 3rd, 5th, (7th), octave
        s = int(t0 * SR)
        # pad (whole bar, a little overlap)
        p = pad_chord([f / 2 for f in tones], bar + 0.6) * m["pad"]
        mix[s:s + len(p)] += p[: max(0, total - s)]
        # bass on beat 1 and a softer one on beat 3
        for bt, v in ((0, 1.0), (2, 0.6)):
            bnote = bass_note(hz(root, 2), beat * 2) * m["bass"] * v
            bs = s + int(bt * beat * SR)
            mix[bs:bs + len(bnote)] += bnote[: max(0, total - bs)]
        # piano eighth-note arpeggio, gentle human timing and velocity
        for j, idx in enumerate(pat):
            f = arp[idx % len(arp)]
            vel = m["piano"] * (0.75 + 0.25 * rng.random()) * (1.0 if j % 4 == 0 else 0.8)
            jitter = rng.normal(0, 0.008)
            ns = s + int((j * beat / 2 + jitter) * SR)
            if ns < 0:
                continue
            note = piano_note(f, beat * 2.2, vel, m["bright"])
            mix[ns:ns + len(note)] += note[: max(0, total - ns)]
        # a soft melody note on top every other bar
        if i % 2 == 1:
            f = arp[rng.integers(len(arp))] * 2
            note = piano_note(f, bar, m["piano"] * 0.5, m["bright"])
            ns = s + int(beat * SR)
            mix[ns:ns + len(note)] += note[: max(0, total - ns)]
        t0 += bar
        i += 1
    mix = reverb(mix, seed=seed)
    n = int(seconds * SR)
    mix = mix[:n]
    t = np.arange(n) / SR
    mix *= np.clip(t / 1.5, 0, 1) * np.clip((seconds - t) / 2.0, 0, 1)
    peak = np.abs(mix).max() or 1
    return (mix / peak * 0.8).astype(np.float32)


def write_wav(path, x):
    stereo = np.stack([x, x], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mood", default="emotional", choices=sorted(MOODS))
    ap.add_argument("--seconds", type=float, default=48)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    write_wav(a.out, make(a.mood, a.seconds, a.seed))
    print(f"wrote {a.out}: {a.mood}, {a.seconds:.1f}s")
