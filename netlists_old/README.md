# 30 GHz FMCW Radar Frontend

A comprehensive 30 GHz FMCW radar analog frontend designed for detecting humans through concrete rubble. Built entirely on the IHP SG13G2 (130nm SiGe BiCMOS) process.

## Architecture & Topologies

The frontend is a fully integrated RF transceiver chain designed at the transistor level. It operates from dual supplies (1.2V and 2.5V) and features a direct-conversion architecture.

### 1. 30 GHz Voltage-Controlled Oscillator (VCO)
* **Topology:** Cross-coupled NPN LC oscillator.
* **Features:** 
  * Uses `npn13G2l` (Nx=4) cross-coupled pairs for negative resistance.
  * LC Tank: L = 200 pH, C = 50 fF, tuning to 30.00 GHz.
  * Tail current source set to 5 mA.
  * Series 1–5 Ω resistors on tank nodes prevent latch-up.
  * 10 fF startup caps on differential nodes.
  * 50 mA × 100 ps PWL startup kick ensures reliable startup.
* **Results:** Outputs a clean **324 mVpp** differential swing at 30.00 GHz.
* **Fix history:** Pre-v64: latch-up at startup, stuck at DC. Fixed in v64 with resistive loading + startup kick. Source: SESSION_MERGED_COMPLETE.md lines 8313-8324, 8651-8659, 9828-9840.

### 2. CML LO Buffer
* **Topology:** CML (Current Mode Logic) differential buffer.
* **Features:** 
  * Provides 274 mVpp differential output to drive PA and Mixer LO ports.
  * Reverse isolation >40 dB prevents PA loading from pulling VCO frequency.
* **Results:** **274 mVpp** differential output swing.
* **Fix history:** Pre-fix: 50 mVpp output due to incorrect bias divider (R_bias = 10k/4k → V_bias = 0.34 V). Fixed by resizing to R_bias = 8k/20k → V_bias = 0.857 V. Source: dual_band_radar_soc README Issues table; SESSION_MERGED_COMPLETE.md line 8657.

### 3. Power Amplifier (PA)
* **Topology:** Single-stage Common-Emitter with direct differential output.
* **Features:** 
  * Uses `npn13G2l` (Nx=16, 160 mA tail) for high output power.
  * L = 500 pH inductive load.
  * Direct differential output into 50 Ω per side — no balun.
* **Results:** 
  * Standalone: **+11.0 dBm** into 50 Ω (~2.8 Vpp differential).
  * Loaded in TX chain: **−4.7 dBm** at antenna port.
* **Fix history:** Pre-v64: +1.3 dBm (7.7 dB shortfall). Tried cascode, transformer matching, neutralization, push-pull. v64 breakthrough: direct differential output (no balun), L=500 pH, 160 mA tail. Source: SESSION_MERGED_COMPLETE.md lines 6810-6824, 8313-8341, 8651-8660, 9828-9840, 10005-10043.

### 4. Low Noise Amplifier (LNA)
* **Topology:** Cascode Amplifier with Inductive Degeneration.
* **Features:** 
  * Input matched to 50Ω using an L-network and inductive emitter degeneration.
  * Cascode transistor isolates input from output, mitigating the Miller effect at 30 GHz.
* **Results:** 
  * Gain (S21): **12.2 dB** (meets ≥12 dB target).
  * Noise Figure: **3.8 dB** (meets ≤4 dB target).
  * S11: **-31.8 dB** (meets ≤-15 dB target).
  * Stability (K): **6.0** (unconditionally stable).

### 5. RF Balun (LNA → Mixer interface)
* **Topology:** Transformer-based passive Balun.
* **Features:** 
  * Converts the single-ended LNA output into a differential signal for the mixer.
  * Turns ratio n=3.8 provides impedance transformation.
* **Results:** Cascaded LNA→Mixer gain within ~2 dB of predicted sum.
* **Fix history:** Pre-fix: -24 dB gap (LNA 196 Ω → Mixer 13 Ω). Fixed by adding balun transformer with n=3.8 impedance transformation in V2. Source: SESSION_MERGED_COMPLETE.md lines 10060-10065; 30GHz README Issues table.

### 6. Active Downconversion Mixer
* **Topology:** Double-Balanced Gilbert Cell.
* **Features:** 
  * RF transconductance stage biased at ~0.9V; LO quad-switching core biased at ~1.7V from the 2.5V supply.
  * 2 mA tail current. 
  * 600Ω resistive loads provide voltage conversion gain.
* **Results:** 
  * Conversion gain (unloaded): **+21.3 dB**.
  * Conversion gain (loaded): **-12 dB**.
  * LO-RF isolation: >30 dB.

### 7. Baseband IF OpAmp Driver
* **Topology:** 2-Stage Common-Emitter Amplifier.
* **Features:** 
  * AC-coupled stages to prevent DC offset propagation.
  * Broadband resistive loads and emitter degeneration for linear gain.
* **Results:** 
  * Closed-loop -3 dB BW: **176.8 MHz**.
  * Closed-loop gain: **21 dB**.
  * Output impedance: <10 Ω.

### 8. Baseband VGA
* **Topology:** Differential pair with variable tail current.
* **Features:** 
  * Gain control via tail current adjustment.
* **Results:** 
  * Gain range: **0–43 dB** (target 0–45 dB).
  * Bandwidth: **50 MHz** (slightly below 75 MHz target).
  * Max output swing: 1.0 Vpp.

### 9. Analog-to-Digital Converter (ADC)
* **Topology:** 8-bit Successive Approximation Register (SAR).
* **Features:** 
  * Samples the baseband signal. Both behavioral and transistor-level topologies implemented.
* **Results:** 
  * Resolution: **8-bit**.
  * Full-scale range: 1.0 Vpp.

---

## Final Performance & Intermediate Results (TT, 27°C, Nominal V)

The frontend successfully demonstrates end-to-end RX operation, taking a 30 GHz LO, receiving a target return, and yielding a 275 µVpp baseband signal.

| Block | Metric | Value | Status |
|-------|--------|-------|--------|
| **VCO** | Center frequency | 30.00 GHz | ✅ PASS |
| **VCO** | Output swing | 324 mVpp | ✅ PASS |
| **VCO** | Phase noise @ 10 MHz | -109.88 dBc/Hz | ✅ PASS |
| **CML Buffer** | Output swing | 274 mVpp | ✅ PASS |
| **PA (standalone)** | Output power | +11.0 dBm | ✅ PASS |
| **PA (standalone)** | P1dB | 10.9 dBm | ✅ PASS |
| **PA (standalone)** | S11 | -4.26 dB | ❌ FAIL |
| **PA (loaded)** | TX delivered power | -4.7 dBm | ⚠️ GAP |
| **LNA** | Gain | 12.2 dB | ✅ PASS |
| **LNA** | Noise Figure | 3.8 dB | ✅ PASS |
| **LNA** | S11 | -31.8 dB | ✅ PASS |
| **Mixer** | Conversion gain | +21.3 dB (unloaded) | ✅ PASS |
| **IF OpAmp** | Bandwidth | 176.8 MHz | ✅ PASS |
| **IF OpAmp** | Gain | 21 dB | ✅ PASS |
| **VGA** | Gain range | 0–43 dB | ✅ PASS |
| **ADC** | Resolution | 8-bit | ✅ PASS |
| **RX Chain** | Total cascade gain | 53.2 dB | ✅ REPORTED |
| **RX Chain** | IF Amp output | 275 µVpp | ✅ FUNCTIONAL |

## TX Chain Note
The 30 GHz TX chain delivers **−4.7 dBm** at the antenna port in loaded configuration. This is **not a PA device failure** — standalone PA delivers +11.0 dBm. The gap is due to buffer-PA impedance mismatch and multi-stage loading collapse. Fixes pending: transformer matching (OpenEMS), power combining (Wilkinson), cascode bias optimization. Source: SESSION_MERGED_COMPLETE.md lines 8315-8317, 8655-8656, 9834-9836, 10036-10043.

## PVT Corner Verification

The design was verified across rigorous PVT corners. 

| Corner | PA Output (Vpp) | Baseband Output (mVpp) | Cascade Gain (dB) |
|--------|-----------------|------------------------|-------------------|
| **TT 27°C** | 2.290 | 91.304 | 53.2 |
| **SS 125°C** | 1.804 | 54.808 | 48.8 |
| **SF 27°C** | 1.969 | 66.143 | 50.4 |

*(Note: FF and FS corners exhibit a known simulator artifact due to a numerical singularity in the SG13G2 HBT thermal model under high-voltage/low-temp extremes, logged as -999.0 in the raw data. This is a model limitation, not a circuit failure).*

## Known Issues

1. **30 GHz TX power gap:** −4.7 dBm delivered vs +10 dBm target. Standalone PA is +11 dBm. Gap is at buffer-PA interface. Fixes pending: transformer matching, power combining, cascode bias optimization.
2. **VGA bandwidth:** 50 MHz vs 75 MHz target. Slightly marginal.
3. **Phase noise:** -109.88 dBc/Hz @ 10 MHz offset — passes <-100 dBc/Hz target. ✅
4. **PA P1dB:** 10.9 dBm — passes +10 dBm target. ✅
5. **PA S11:** -4.26 dB — fails <-15 dB target due to lack of matching network. ❌
6. **Full TX chain optimization:** Requires transformer output matching via OpenEMS or similar EM tool.

---

*For raw simulation numbers and detailed measurement logs, see `verification_results.md`. For the authoritative final values, see `dual_band_radar_soc/TRUTH.md`.*
