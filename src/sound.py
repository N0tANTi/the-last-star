"""Procedural stereo soundtrack & SFX synthesizer for 'The Last Star' (59.0s, 44.1kHz WAV)."""
import math
import os
import wave
import numpy as np


SR = 44100
DURATION = 59.0


def _midi_to_hz(midi):
    return 440.0 * (2.0 ** ((midi - 69.0) / 12.0))


def _add_note(buf_l, buf_r, t_start, midi, dur, amp=0.18, pan=0.0, timbre="harp"):
    """Synthesize a plucked harp/celesta or warm bowed string note into stereo buffers."""
    i0 = int(t_start * SR)
    n = int(dur * SR)
    if i0 >= len(buf_l) or n <= 0:
        return
    i1 = min(len(buf_l), i0 + n)
    actual = i1 - i0
    t = np.arange(actual, dtype=np.float64) / SR
    f = _midi_to_hz(midi)

    if timbre == "harp":
        # Rich plucked harp with warm fundamental + shimmering upper harmonics
        sig = (
            1.00 * np.sin(2 * math.pi * f * t) * np.exp(-t * 1.45)
            + 0.42 * np.sin(2 * math.pi * 2 * f * t) * np.exp(-t * 2.6)
            + 0.18 * np.sin(2 * math.pi * 3 * f * t) * np.exp(-t * 4.2)
            + 0.08 * np.sin(2 * math.pi * 4 * f * t) * np.exp(-t * 6.0)
        )
        attack = np.minimum(1.0, t / 0.008)
        env = attack * np.minimum(1.0, (dur - t) / 0.08)
        sig *= env
    elif timbre == "celesta":
        # Bell-like crystalline star chime
        sig = (
            1.00 * np.sin(2 * math.pi * f * t) * np.exp(-t * 1.8)
            + 0.35 * np.sin(2 * math.pi * 2.0 * f * t) * np.exp(-t * 3.0)
            + 0.20 * np.sin(2 * math.pi * 3.01 * f * t) * np.exp(-t * 4.5)
            + 0.12 * np.sin(2 * math.pi * 5.4 * f * t) * np.exp(-t * 7.5)
        )
        attack = np.minimum(1.0, t / 0.004)
        sig *= attack
    elif timbre == "pad":
        # Lush detuned warm cinematic string ensemble pad
        vibrato = 1.0 + 0.0025 * np.sin(2 * math.pi * 5.2 * t)
        sig = (
            0.55 * np.sin(2 * math.pi * f * vibrato * t)
            + 0.35 * np.sin(2 * math.pi * (f * 1.003) * t + 0.7)
            + 0.35 * np.sin(2 * math.pi * (f * 0.997) * t + 1.4)
            + 0.22 * np.sin(2 * math.pi * (2 * f) * t)
            + 0.09 * np.sin(2 * math.pi * (3 * f) * t)
        )
        attack = np.minimum(1.0, t / 1.1)
        release = np.minimum(1.0, np.maximum(0.0, (dur - t) / 1.4))
        sig *= attack * release
    elif timbre == "click":
        # Soft mechanical brass switch click
        rng = np.random.default_rng(int(t_start * 1000) + 7)
        noise = rng.standard_normal(actual)
        sig = (noise * 0.5 + np.sin(2 * math.pi * f * t)) * np.exp(-t * 42.0)
    else:
        sig = np.sin(2 * math.pi * f * t) * np.exp(-t * 2.0)

    gain_l = amp * math.cos((pan + 1.0) * math.pi * 0.25)
    gain_r = amp * math.sin((pan + 1.0) * math.pi * 0.25)
    buf_l[i0:i1] += sig * gain_l
    buf_r[i0:i1] += sig * gain_r


def _add_wind_and_ambience(buf_l, buf_r):
    """Synthesize twilight prairie breeze (0-4s, 33-52s) and deep observatory room hum (4-33s)."""
    n = len(buf_l)
    t = np.arange(n, dtype=np.float64) / SR
    rng = np.random.default_rng(42)
    white = rng.standard_normal(n)

    # Simple 1-pole low-pass filtered wind noise
    wind = np.zeros(n, dtype=np.float64)
    a = 0.025
    acc = 0.0
    # Vectorized moving-average approximation for speed
    kernel = np.exp(-np.arange(180) * 0.035)
    kernel /= kernel.sum()
    wind = np.convolve(white, kernel, mode="same")

    # Modulate wind envelope: exterior breeze at 0-4.2s and 33.5-53s
    env = np.zeros(n, dtype=np.float64)
    env += 0.22 * np.exp(-((t - 1.8) / 2.2) ** 2) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.35 * t))
    env += 0.10 * np.exp(-((t - 42.0) / 10.0) ** 2) * (0.7 + 0.3 * np.sin(2 * math.pi * 0.22 * t))

    buf_l += wind * env * 0.55
    buf_r += np.roll(wind, 220) * env * 0.55

    # Warm low room resonance inside observatory (4-33s)
    room_env = np.clip((t - 3.8) / 1.2, 0, 1) * np.clip((33.5 - t) / 1.0, 0, 1)
    drone = (0.045 * np.sin(2 * math.pi * 65.4 * t) + 0.025 * np.sin(2 * math.pi * 98.0 * t)) * room_env
    buf_l += drone
    buf_r += drone


def _add_star_riser(buf_l, buf_r):
    """Add shimmering ethereal swell during the dome vortex (27-33.5s)."""
    i0 = int(27.0 * SR)
    i1 = int(34.2 * SR)
    t = np.arange(i1 - i0, dtype=np.float64) / SR
    dur = (i1 - i0) / SR
    progress = t / dur
    # Rising harmonic shimmer chord peaking at 33.0s
    peak_env = np.clip(progress / 0.82, 0, 1) ** 2.2 * np.clip((1.0 - progress) / 0.18, 0, 1)
    shimmer = (
        0.35 * np.sin(2 * math.pi * (220.0 + 220.0 * progress) * t)
        + 0.25 * np.sin(2 * math.pi * (330.0 + 330.0 * progress) * t)
        + 0.18 * np.sin(2 * math.pi * (660.0 + 440.0 * progress) * t)
    )
    buf_l[i0:i1] += shimmer * peak_env * 0.16
    buf_r[i0:i1] += shimmer * peak_env * 0.16


def _apply_simple_reverb(buf_l, buf_r):
    """Add spacious multi-tap cathedral/starlight reverb tail."""
    out_l = buf_l.copy()
    out_r = buf_r.copy()
    taps = [
        (0.085, 0.28, 0.20),
        (0.165, 0.20, 0.26),
        (0.275, 0.16, 0.13),
        (0.410, 0.11, 0.14),
        (0.580, 0.08, 0.07),
    ]
    for delay_s, gl, gr in taps:
        d = int(delay_s * SR)
        out_l[d:] += buf_l[:-d] * gl + buf_r[:-d] * (gr * 0.4)
        out_r[d:] += buf_r[:-d] * gr + buf_l[:-d] * (gl * 0.4)
    return out_l, out_r


def generate_soundtrack(out_path):
    """Synthesize and save the complete 59-second stereo soundtrack."""
    n = int(DURATION * SR)
    buf_l = np.zeros(n, dtype=np.float64)
    buf_r = np.zeros(n, dtype=np.float64)

    _add_wind_and_ambience(buf_l, buf_r)
    _add_star_riser(buf_l, buf_r)

    # 1.2s: Soft window-light chime
    _add_note(buf_l, buf_r, 1.15, 72, 2.2, amp=0.09, pan=0.2, timbre="celesta")

    # 4.5s - 14.0s: Gentle curious exploration harp notes (C major / A minor nostalgic intervals)
    intro_notes = [
        (5.2, 64, 2.8, -0.2), (6.1, 67, 2.6, 0.15), (7.0, 72, 3.0, -0.1),
        (8.4, 71, 2.8, 0.2), (9.6, 69, 3.2, -0.15),
        (11.0, 67, 2.5, 0.1), (12.0, 72, 2.8, -0.2), (13.0, 76, 3.0, 0.2),
    ]
    for ts, midi, dur, pan in intro_notes:
        _add_note(buf_l, buf_r, ts, midi, dur, amp=0.14, pan=pan, timbre="harp")

    # 16.5s - 21.0s: Robot taps starball lens -> mechanical click + radiant starlight chime!
    _add_note(buf_l, buf_r, 16.7, 52, 0.18, amp=0.22, pan=-0.1, timbre="click")
    _add_note(buf_l, buf_r, 16.9, 84, 3.8, amp=0.22, pan=0.0, timbre="celesta")
    _add_note(buf_l, buf_r, 17.2, 79, 3.5, amp=0.16, pan=0.25, timbre="celesta")
    _add_note(buf_l, buf_r, 17.6, 91, 3.2, amp=0.12, pan=-0.25, timbre="celesta")

    # 21.5s - 27.0s: Whole planetarium waking up (warm chords + rising arpeggio)
    for m in (48, 55, 64):
        _add_note(buf_l, buf_r, 21.5, m, 6.2, amp=0.09, pan=0.0, timbre="pad")
    wake_arp = [60, 64, 67, 72, 67, 72, 76, 79, 72, 76, 79, 84]
    for idx, midi in enumerate(wake_arp):
        _add_note(buf_l, buf_r, 22.0 + idx * 0.42, midi, 2.5, amp=0.13 + idx * 0.005, pan=math.sin(idx) * 0.35, timbre="harp")

    # 27.2s - 33.2s: Dome vortex crescendo! Sweeping luminous harp runs
    vortex_scale = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84, 86, 88, 91]
    t_cur = 27.2
    step = 0.24
    idx = 0
    while t_cur < 32.9:
        midi = vortex_scale[idx % len(vortex_scale)]
        _add_note(buf_l, buf_r, t_cur, midi, 2.4, amp=0.14 + 0.06 * ((t_cur - 27.2) / 5.7), pan=math.sin(idx * 0.7) * 0.5, timbre="harp")
        if idx % 3 == 0:
            _add_note(buf_l, buf_r, t_cur, midi + 12, 2.0, amp=0.07, pan=-math.sin(idx * 0.7) * 0.4, timbre="celesta")
        t_cur += max(0.11, step)
        step *= 0.965
        idx += 1

    # 33.2s - 47.5s: Majestic Star Geyser & Star Whale theme (C -> G -> Am -> F -> C progression)
    chords = [
        (33.2, 3.6, [48, 55, 64, 72]),  # C
        (36.8, 3.6, [43, 55, 62, 71]),  # G
        (40.4, 3.6, [45, 57, 64, 72]),  # Am
        (44.0, 4.2, [41, 53, 60, 69]),  # F
    ]
    for ts, dur, notes in chords:
        for ni, midi in enumerate(notes):
            _add_note(buf_l, buf_r, ts, midi, dur + 1.2, amp=0.11 if ni < 2 else 0.08, pan=(ni - 1.5) * 0.25, timbre="pad")
        # Flowing harp melody over each chord
        for bi in range(8):
            m_note = notes[bi % len(notes)] + (12 if bi >= 4 else 0)
            _add_note(buf_l, buf_r, ts + bi * 0.44, m_note, 2.8, amp=0.14, pan=math.sin(bi) * 0.4, timbre="harp")
        # Sparkle celesta accent on downbeat
        _add_note(buf_l, buf_r, ts + 0.05, notes[-1] + 12, 3.2, amp=0.09, pan=0.3, timbre="celesta")

    # 48.0s - 58.2s: Tender balcony catch & handwritten title outro (gentle slowing harp + final warm C major chord)
    outro_melody = [
        (48.2, 79, 3.2, -0.15), (49.2, 76, 3.2, 0.15), (50.3, 72, 3.6, -0.1),
        (51.8, 74, 3.4, 0.1),   (53.0, 76, 3.8, -0.2), (54.4, 72, 4.6, 0.0),
    ]
    for ts, midi, dur, pan in outro_melody:
        _add_note(buf_l, buf_r, ts, midi, dur, amp=0.15, pan=pan, timbre="harp")
        _add_note(buf_l, buf_r, ts + 0.03, midi + 12, dur * 0.8, amp=0.06, pan=-pan, timbre="celesta")

    # Final peaceful warm resolution pad
    for m in (48, 60, 64, 67):
        _add_note(buf_l, buf_r, 53.0, m, 5.6, amp=0.075, pan=0.0, timbre="pad")

    # Apply reverb + soft mastering limiter + gentle fade-in/out
    out_l, out_r = _apply_simple_reverb(buf_l, buf_r)
    fade_in = np.minimum(1.0, np.arange(n) / (0.6 * SR))
    fade_out = np.minimum(1.0, np.arange(n)[::-1] / (1.8 * SR))
    out_l *= fade_in * fade_out
    out_r *= fade_in * fade_out

    peak = max(np.max(np.abs(out_l)), np.max(np.abs(out_r)), 1e-6)
    target_peak = 0.86
    out_l = np.tanh((out_l / peak) * 1.15) * target_peak
    out_r = np.tanh((out_r / peak) * 1.15) * target_peak

    interleaved = np.empty(n * 2, dtype=np.int16)
    interleaved[0::2] = np.clip(out_l * 32767.0, -32768, 32767).astype(np.int16)
    interleaved[1::2] = np.clip(out_r * 32767.0, -32768, 32767).astype(np.int16)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(interleaved.tobytes())
    print(f"[sound] Generated {out_path} ({DURATION:.1f}s stereo, 44.1kHz)")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "soundtrack.wav")
    generate_soundtrack(out)
