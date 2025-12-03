#!/usr/bin/env python3
"""Compare audio files: waveform correlation, MFCC distances, DTW, and spectrogram plots.

Saves PNGs to the same directory as the inputs (default `/app/output/`).
"""
from pathlib import Path
import argparse
import numpy as np
import soundfile as sf
import librosa
import librosa.display
import matplotlib.pyplot as plt
import itertools
from scipy.spatial.distance import cosine
import warnings


def load_mono(path, sr=None):
    y, orig_sr = sf.read(path)
    if y.ndim > 1:
        y = y.mean(axis=1)
    if sr is not None and orig_sr != sr:
        y = librosa.resample(y.astype(np.float32), orig_sr, sr)
        return y.astype(np.float32), sr
    return y.astype(np.float32), orig_sr


def save_spectrogram(y, sr, outpath, title=None):
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    Sdb = librosa.amplitude_to_db(S, ref=np.max)
    plt.figure(figsize=(8, 3.5))
    librosa.display.specshow(Sdb, sr=sr, hop_length=512, x_axis='time', y_axis='hz')
    plt.colorbar(format='%+2.0f dB')
    if title:
        plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


def compare_pair(a1, sr1, a2, sr2, name1, name2, outdir):
    # ensure same sr
    if sr1 != sr2:
        target_sr = max(sr1, sr2)
        a1 = librosa.resample(a1, sr1, target_sr)
        a2 = librosa.resample(a2, sr2, target_sr)
        sr = target_sr
    else:
        sr = sr1
    # trim to shortest
    n = min(len(a1), len(a2))
    a1 = a1[:n]
    a2 = a2[:n]

    # waveform pearson
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        corr = np.corrcoef(a1, a2)[0, 1]

    # MFCCs
    mfcc1 = librosa.feature.mfcc(y=a1, sr=sr, n_mfcc=20)
    mfcc2 = librosa.feature.mfcc(y=a2, sr=sr, n_mfcc=20)
    # mean MFCC vectors
    m1 = mfcc1.mean(axis=1)
    m2 = mfcc2.mean(axis=1)
    mfcc_cos = 1 - cosine(m1, m2)

    # DTW on MFCC (use cosine distances between frames)
    D, wp = librosa.sequence.dtw(X=mfcc1, Y=mfcc2, metric='cosine')
    dtw_cost = D[-1, -1] / D.shape[0]

    # spectrogram images side-by-side
    outpng = outdir / f"compare_{Path(name1).stem}_vs_{Path(name2).stem}.png"
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    S1 = librosa.amplitude_to_db(np.abs(librosa.stft(a1, n_fft=2048)), ref=np.max)
    librosa.display.specshow(S1, sr=sr, hop_length=512, x_axis='time', y_axis='hz')
    plt.title(name1)
    plt.colorbar(format='%+2.0f dB')
    plt.subplot(1, 2, 2)
    S2 = librosa.amplitude_to_db(np.abs(librosa.stft(a2, n_fft=2048)), ref=np.max)
    librosa.display.specshow(S2, sr=sr, hop_length=512, x_axis='time', y_axis='hz')
    plt.title(name2)
    plt.colorbar(format='%+2.0f dB')
    plt.tight_layout()
    plt.savefig(outpng, dpi=150)
    plt.close()

    return {
        'file1': name1,
        'file2': name2,
        'pearson': float(corr),
        'mfcc_cosine_similarity': float(mfcc_cos),
        'dtw_cost': float(dtw_cost),
        'spectrogram_png': str(outpng)
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--files', nargs='*', help='WAV files to compare (default: all WAVs in /app/output/)')
    p.add_argument('--outdir', default='/app/output', help='Directory to write PNGs (default /app/output)')
    p.add_argument('--sr', type=int, default=16000, help='Target sample rate for analysis (default 16000)')
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not args.files:
        files = sorted(list(outdir.glob('*.wav')))
    else:
        files = [Path(f) for f in args.files]

    if len(files) < 2:
        print('Need 2+ WAV files to compare. Found:', files)
        raise SystemExit(2)

    loaded = []
    for f in files:
        if not f.exists():
            print('MISSING', f)
            raise SystemExit(3)
        y, sr = load_mono(str(f), sr=args.sr)
        # normalize
        y = y / (np.max(np.abs(y)) + 1e-9)
        loaded.append((str(f.name), y, sr))

    results = []
    for (name1, a1, sr1), (name2, a2, sr2) in itertools.combinations(loaded, 2):
        r = compare_pair(a1=a1, sr1=sr1, a2=a2, sr2=sr2, name1=name1, name2=name2, outdir=outdir)
        results.append(r)

    # print summary
    print('\nComparison results:')
    for r in results:
        print(f"{r['file1']}  vs  {r['file2']}")
        print(f"  Pearson corr: {r['pearson']:.4f}")
        print(f"  MFCC cosine similarity: {r['mfcc_cosine_similarity']:.4f} (1.0 means identical)")
        print(f"  DTW cost (norm): {r['dtw_cost']:.4f}")
        print(f"  Saved spectrogram PNG: {r['spectrogram_png']}\n")


if __name__ == '__main__':
    main()
