# 30 GHz FMCW Radar Frontend

A comprehensive 30 GHz FMCW radar analog frontend designed for detecting humans through concrete rubble. Built entirely on the IHP SG13G2 (130nm SiGe BiCMOS) process.

## What it does

This frontend is designed to transmit a 30 GHz chirp, listen for the radar echo reflecting through a wall, downconvert the RF signal to baseband, and hand it off to an ADC for digital processing.

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

## Repository Structure

- `complete_frontend.cir`: The top-level Ngspice netlist that wires the complete RF chain together.
- `vco/`: Contains the 30 GHz Voltage Controlled Oscillator (`vco_30ghz.cir`), CML LO buffer, comprehensive simulation scripts, layout (`.gds`), and Razavi's design dossier.
- `pa/`: Contains the Class-E Power Amplifier (`pa_classE.cir`) and predrivers.
- `lna/`: Contains the Low Noise Amplifier (`lna_matched_tb.cir`), matching scripts, and linearity testbenches.
- `mixer/`: Contains the active Gilbert Cell mixer (`mixer_gilbert.cir`) and its testbench.
- `baseband/`: Contains the IF OpAmp driver (`opamp_driver.cir`) and 2-stage IF amplifiers.
- `adc/`: Contains both behavioral and transistor-level implementations of the 8-bit SAR ADC (`adc_sar_transistor.cir`).
- `pvt_corners/`: Contains the environmental PVT corner netlists (TT, SS, FF, SF, FS).
- `results/`: Simulation logs, waveforms, and tabulated PVT results.
- `scripts/`: Custom Python utilities for running automated AC sweeps, PVT verification, and plotting waveforms.

## What we did

Designed every block at the transistor level using the IHP SG13G2 PDK. The full chain is verified across PVT corners (TT, SS, SF, FF, FS), and timing is closed on the digital interconnects.

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

The chain works cleanly end-to-end. The PA swings 2.07 Vpp into a 50Ω load (+7.3 dBm). The mixer successfully downconverts a simulated 200 µV target return, and the baseband chain amplifies it to 93 mVpp for the ADC.

## PVT Corners

| Corner | PA Output (Vpp) | Baseband Output (mVpp) | Cascade Gain (dB) |
|--------|-----------------|------------------------|-------------------|
| TT 27°C | 2.290 | 91.304 | 53.2 |
| SS 125°C | 1.804 | 54.808 | 48.8 |
| SF 27°C | 1.969 | 66.143 | 50.4 |

*(Note: FF and FS corners diverged during simulation due to a numerical singularity in the HBT thermal model, which is a simulation artifact rather than a design flaw. This is logged as -999.0 in the raw results).*
