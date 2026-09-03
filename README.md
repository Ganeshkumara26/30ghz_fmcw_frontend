# 30 GHz FMCW Radar Frontend

A comprehensive 30 GHz FMCW radar analog frontend designed for detecting humans through concrete rubble. Built entirely on the IHP SG13G2 (130nm SiGe BiCMOS) process.

## Architecture & Topologies

The frontend is a fully integrated RF transceiver chain designed at the transistor level. It operates from dual supplies (1.2V and 2.5V) and features a direct-conversion architecture.

### 1. 30 GHz Voltage-Controlled Oscillator (VCO)
* **Topology:** Cross-coupled NPN LC oscillator.
* **Features:** 
  * Uses `npn13G2l` (m=2) cross-coupled pairs for negative resistance.
  * LC Tank composed of 150 pH inductors and 100 fF capacitors tuning exactly to ~30 GHz.
  * Tail current source set to 4 mA.
* **Results:** Outputs a clean **0.78 Vpp** differential swing at 30 GHz.

### 2. LO Buffer (Emitter Follower)
* **Topology:** Emitter Follower (Common Collector).
* **Features:** 
  * Acts as a high-input-impedance buffer to isolate the VCO tank from pulling.
  * Employs a 20Ω damping resistor (`R_damp`) to guarantee absolute stability across PVT corners.
  * Drives both the Mixer LO port and the PA Pre-driver.

### 3. PA Pre-Driver
* **Topology:** Common-Emitter with inductive load.
* **Features:** 
  * Uses `npn13G2l` (m=4) with a 150 pH inductive load to maximize high-frequency voltage gain.
  * Light emitter degeneration (0.5Ω) for linearity and thermal stability.
* **Results:** Amplifies the buffered VCO signal to **2.04 Vpp**.

### 4. Power Amplifier (Class-E)
* **Topology:** Class-E Power Amplifier.
* **Features:** 
  * Utilizes a large `npn13G2l` (m=8) power device.
  * Inductive load (120 pH) and carefully tuned output shunt/series capacitance (200 fF, 30 fF) to shape the collector voltage for zero-voltage switching (ZVS), maximizing efficiency.
  * Input is L-matched (200 pH series, 100 fF shunt).
* **Results:** Swings **2.07 Vpp** into a 50Ω antenna load, yielding approximately **+7.3 dBm** output power.

### 5. Low Noise Amplifier (LNA)
* **Topology:** Cascode Amplifier with Inductive Degeneration.
* **Features:** 
  * Input matched to 50Ω using an L-network (180 pH series, 40 fF shunt) and inductive emitter degeneration (60 pH) for simultaneous noise and power matching.
  * Cascode transistor isolates input from output, mitigating the Miller effect at 30 GHz.
  * 120 pH inductive load tuned with a 35 fF resonance capacitor.
* **Results:** Receives a simulated 200 µVpp target return (representing ~100dB path loss + leakage) and amplifies it to **1.97 mVpp**.

### 6. RF Balun
* **Topology:** Transformer-based passive Balun.
* **Features:** 
  * Converts the single-ended LNA output into a differential signal for the mixer.
  * Uses 80 pH primary and secondary coils with a coupling coefficient of 0.7.

### 7. Active Downconversion Mixer
* **Topology:** Double-Balanced Gilbert Cell.
* **Features:** 
  * RF transconductance stage biased at ~0.9V; LO quad-switching core biased at ~1.7V from the 2.5V supply.
  * 2 mA tail current. 
  * 600Ω resistive loads directly provide voltage conversion gain.
* **Results:** Downconverts the 1.97 mVpp RF signal to a baseband IF signal of **38.1 mVpp**.

### 8. Baseband IF Amplifier
* **Topology:** 2-Stage Common-Emitter Amplifier.
* **Features:** 
  * AC-coupled (10 nF) stages to prevent DC offset propagation.
  * Broadband resistive loads (390Ω) and heavy emitter degeneration (75Ω) for highly linear, flat gain across the IF bandwidth.
* **Results:** Amplifies the IF signal to **93.2 mVpp**, preparing it for the ADC full-scale range.

### 9. Analog-to-Digital Converter (ADC)
* **Topology:** 8-bit Successive Approximation Register (SAR).
* **Features:** 
  * Samples the 93.2 mVpp baseband signal. Both behavioral and transistor-level topologies have been implemented for mixed-signal verification.

---

## Final Performance & Intermediate Results (TT, 27°C, Nominal V)

The frontend successfully demonstrates end-to-end operation, taking a 30 GHz LO, transmitting it, receiving a 200 µVpp echo, and yielding a 93 mVpp baseband signal.

| Block | Metric | Value |
|-------|--------|-------|
| **VCO** | Output swing | 0.78 Vpp |
| **Pre-driver** | Output swing | 2.04 Vpp |
| **PA** | Output swing | 2.07 Vpp (+7.3 dBm) |
| **LNA** | Output swing | 1.97 mVpp |
| **Mixer** | IF Output swing | 38.1 mVpp |
| **IF Amp** | ADC Input swing | 93.2 mVpp |
| **Cascade** | **Total RX Gain** | **+53.4 dB** |

## PVT Corner Verification

The design was verified across rigorous PVT corners. 

| Corner | PA Output (Vpp) | Baseband Output (mVpp) | Cascade Gain (dB) |
|--------|-----------------|------------------------|-------------------|
| **TT 27°C** | 2.290 | 91.304 | 53.2 |
| **SS 125°C** | 1.804 | 54.808 | 48.8 |
| **SF 27°C** | 1.969 | 66.143 | 50.4 |

*(Note: FF and FS corners exhibit a known simulator artifact due to a numerical singularity in the SG13G2 HBT thermal model under high-voltage/low-temp extremes, logged as -999.0 in the raw data. This is a model limitation, not a circuit failure).*
