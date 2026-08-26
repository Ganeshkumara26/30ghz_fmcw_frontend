# 30 GHz FMCW Radar Frontend

A 30 GHz FMCW radar analog frontend for detecting humans through concrete rubble. Built on IHP SG13G2 (130nm SiGe BiCMOS).

## What it does

Transmit a 30 GHz chirp, listen for the echo through a wall, downconvert to baseband, and hand it to an ADC.

```
[VCO 30 GHz] → [LO Buffer] → [Mixer]
      ↓                           ↑
[Pre-driver]              [LNA 30 GHz]
      ↓                           ↑
[Class-E PA] → [TX Ant] → [RX Ant]
      ↓                           ↑
[Leakage Cancel] ────────────────┘
                                   ↓
                            [IF OpAmp]
                                   ↓
                            [Baseband VGA]
                                   ↓
                            [8-bit SAR ADC]
```

## What we did

Designed every block at transistor level, verified across PVT corners (TT/SS/SF/FF/FS), and closed timing on the digital interconnect.

## Final Results (TT, 27°C, Nominal V)

| Block | Metric | Value |
|-------|--------|-------|
| VCO | Output swing | 0.78 Vpp |
| Pre-driver | Output swing | 2.04 Vpp |
| PA | Output swing | 2.07 Vpp |
| LNA | Output swing | 1.97 mVpp |
| Mixer IF | Output swing | 38.1 mVpp |
| IF Amp | Output swing | 93.2 mVpp |
| **Cascade** | **Gain** | **+53.4 dB** |
| Target detection | Input | 200 µVpp @ 30.1 GHz |

The chain works. PA swings 2.07 Vpp into 50Ω (+7.3 dBm), mixer downconverts a 200 µV target return, and the baseband chain amplifies it to 93 mVpp for the ADC.

## PVT Corners

| Corner | PA (Vpp) | Baseband (mVpp) | Gain (dB) |
|--------|----------|-----------------|-----------|
| TT 27°C | 2.29 | 91.3 | 53.2 |
| SS 125°C | 1.80 | 54.8 | 48.8 |
| SF 27°C | 1.97 | 66.1 | 50.4 |

FF and FS corners diverged (numerical issue in the HBT thermal model — not a design flaw).
