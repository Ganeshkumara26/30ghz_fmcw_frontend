#!/usr/bin/env python3
"""
Post-process Xyce transient simulation output.
Reads the .prn file, extracts oscillation frequency, amplitude,
power consumption, and generates thesis-quality plots.
"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
FIG_DIR = os.path.join(PROJECT_ROOT, 'docs', 'figures', 'experiments')
os.makedirs(FIG_DIR, exist_ok=True)

# Xyce output file
PRN_FILE = os.path.join(PROJECT_ROOT, 'src', 'netlist', 'experiments',
                        'exp_xyce_hb_noise.cir.prn')


def load_xyce_prn(filepath):
    """Load Xyce .prn file. Returns dict of column arrays."""
    # Read line by line to handle "End of Xyce" footer
    rows = []
    with open(filepath, 'r') as f:
        header = f.readline().strip().split()
        for line in f:
            line = line.strip()
            if not line or line.startswith('End') or not line[0].isdigit():
                continue
            try:
                vals = [float(x) for x in line.split()]
                if len(vals) == len(header):
                    rows.append(vals)
            except ValueError:
                continue

    data = np.array(rows)
    result = {}
    for i, name in enumerate(header):
        if i < data.shape[1]:
            result[name.upper()] = data[:, i]
    return result


def main():
    if not os.path.exists(PRN_FILE):
        print(f"ERROR: {PRN_FILE} not found")
        return

    print(f"Loading Xyce data from: {PRN_FILE}")
    data = load_xyce_prn(PRN_FILE)

    t = data.get('TIME', data.get('INDEX'))
    vx = data.get('V(OUT_X)')
    vy = data.get('V(OUT_Y)')
    icc = data.get('I(VCC)')

    if t is None or vx is None:
        print("ERROR: Could not find TIME/V(OUT_X) columns")
        print(f"Available columns: {list(data.keys())}")
        return

    print(f"  Time range: {t[0]*1e9:.3f} – {t[-1]*1e9:.3f} ns")
    print(f"  Data points: {len(t)}")

    # Skip startup (first 1 ns)
    mask = t > 1e-9
    t_ss = t[mask]
    vx_ss = vx[mask]
    vy_ss = vy[mask] if vy is not None else None

    # --- Frequency extraction from zero crossings ---
    vdiff = vx_ss - vy_ss if vy_ss is not None else vx_ss - np.mean(vx_ss)
    crossings = []
    for i in range(len(vdiff) - 1):
        if vdiff[i] < 0 and vdiff[i+1] >= 0:
            tc = t_ss[i] + (-vdiff[i]) / (vdiff[i+1] - vdiff[i]) * (t_ss[i+1] - t_ss[i])
            crossings.append(tc)

    if len(crossings) > 2:
        periods = np.diff(crossings)
        f0 = 1.0 / np.mean(periods)
        jitter_rms = np.std(periods) * 1e15  # in fs
    else:
        f0 = 0
        jitter_rms = 0

    # --- Amplitude ---
    vpp_x = np.max(vx_ss) - np.min(vx_ss)
    vpp_diff = np.max(vdiff) - np.min(vdiff)

    # --- Power ---
    pdc = np.mean(np.abs(icc[mask])) * 0.95 if icc is not None else 0

    # --- FFT ---
    dt = np.mean(np.diff(t_ss))
    N = len(vdiff)
    freqs = np.fft.rfftfreq(N, dt)
    fft_mag = np.abs(np.fft.rfft(vdiff * np.hanning(N))) * 2.0 / N
    fft_db = 20 * np.log10(fft_mag / np.max(fft_mag) + 1e-15)

    # Find fundamental
    fund_idx = np.argmax(fft_mag[1:]) + 1
    f_fund = freqs[fund_idx]

    print(f"\n{'='*60}")
    print(f" XYCE TRANSIENT ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"  Oscillation Frequency (zero-crossing): {f0/1e9:.3f} GHz")
    print(f"  Oscillation Frequency (FFT peak):      {f_fund/1e9:.3f} GHz")
    print(f"  Single-ended swing (Vpp):              {vpp_x*1e3:.1f} mV")
    print(f"  Differential swing (Vpp):              {vpp_diff*1e3:.1f} mV")
    print(f"  DC Power:                              {pdc*1e3:.2f} mW")
    print(f"  DC Current:                            {pdc/0.95*1e3:.2f} mA")
    if jitter_rms > 0:
        print(f"  Cycle-to-cycle jitter:                 {jitter_rms:.2f} fs (RMS)")
    print(f"{'='*60}")

    # ===== PLOTS =====
    # 1. Time-domain waveform
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    t_plot = t * 1e9
    ax1.plot(t_plot, vx * 1e3, 'b-', lw=0.8, label='V(out_x)')
    if vy is not None:
        ax1.plot(t_plot, vy * 1e3, 'r-', lw=0.8, label='V(out_y)')
    ax1.set_ylabel('Voltage (mV)')
    ax1.set_title(f'Xyce Transient: 30 GHz VCO Output Waveforms')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    if icc is not None:
        ax2.plot(t_plot, np.abs(icc) * 1e3, 'g-', lw=0.8)
        ax2.set_ylabel('$|I_{DD}|$ (mA)')
    ax2.set_xlabel('Time (ns)')
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_xyce_waveform.png'), dpi=300)
    plt.close()
    print("Saved: fig_xyce_waveform.png")

    # 2. FFT spectrum
    fig, ax = plt.subplots(figsize=(10, 5))
    f_ghz = freqs / 1e9
    mask_plot = f_ghz < 150
    ax.plot(f_ghz[mask_plot], fft_db[mask_plot], 'b-', lw=1)
    ax.axvline(f_fund / 1e9, color='r', ls='--', alpha=0.5,
               label=f'Fundamental: {f_fund/1e9:.2f} GHz')

    # Mark harmonics
    for n in range(2, 5):
        h_idx = np.argmin(np.abs(freqs - n * f_fund))
        if h_idx < len(fft_db):
            ax.plot(freqs[h_idx]/1e9, fft_db[h_idx], 'ro', ms=5)
            ax.annotate(f'{n}×f₀\n{fft_db[h_idx]:.1f} dB',
                        xy=(freqs[h_idx]/1e9, fft_db[h_idx]),
                        xytext=(freqs[h_idx]/1e9 + 5, fft_db[h_idx] + 5),
                        fontsize=8)

    ax.set_xlabel('Frequency (GHz)')
    ax.set_ylabel('Normalized Magnitude (dB)')
    ax.set_title('Xyce FFT Spectrum')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-80, 5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_xyce_fft.png'), dpi=300)
    plt.close()
    print("Saved: fig_xyce_fft.png")

    # 3. Steady-state zoom (last 200 ps)
    mask_zoom = t > t[-1] - 200e-12
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(t[mask_zoom] * 1e12, vx[mask_zoom] * 1e3, 'b-', lw=1.5, label='V(out_x)')
    if vy is not None:
        ax.plot(t[mask_zoom] * 1e12, vy[mask_zoom] * 1e3, 'r-', lw=1.5, label='V(out_y)')
    ax.set_xlabel('Time (ps)')
    ax.set_ylabel('Voltage (mV)')
    ax.set_title(f'Steady-State Differential Output — f₀ = {f0/1e9:.2f} GHz')
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_xyce_steadystate.png'), dpi=300)
    plt.close()
    print("Saved: fig_xyce_steadystate.png")


if __name__ == '__main__':
    main()
