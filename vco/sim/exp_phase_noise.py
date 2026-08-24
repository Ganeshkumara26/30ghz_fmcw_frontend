"""
Phase Noise Estimation via Transient Noise Simulation (ngspice)

Method: Run the VCO with transient noise enabled on all resistive elements,
        extract zero-crossing times over many cycles, compute jitter statistics,
        and convert to single-sideband phase noise L(df).

This is the standard time-domain approach when PSS/Pnoise is unavailable.
It provides a physically meaningful estimate of phase noise that captures
the actual noise mechanisms in the circuit.

The relationship between cycle-to-cycle jitter and phase noise is:
    L(df) = (f0^2 * sigma_cc^2) / (2 * df^2)   [in V^2/Hz, linear]
    L(df) = 10*log10(f0^2 * sigma_cc^2 / (2 * df^2))  [in dBc/Hz]

Reference: A. Hajimiri and T. H. Lee, "A General Theory of Phase Noise
           in Electrical Oscillators," IEEE JSSC, Feb. 1998.
"""
import os
import sys
import subprocess
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..', '..'))
NETLIST_DIR = os.path.join(PROJECT_ROOT, 'src', 'netlist', 'experiments')
RAW_DIR = os.path.join(PROJECT_ROOT, 'sim', 'raw_results', 'raw_exp')
FIG_DIR = os.path.join(PROJECT_ROOT, 'docs', 'figures', 'experiments')

for d in [NETLIST_DIR, RAW_DIR, FIG_DIR]:
    os.makedirs(d, exist_ok=True)

def create_transient_noise_netlist():
    """Create a long-duration transient simulation with noise sources."""
    
    # For ngspice transient noise, we use resistor thermal noise (built-in)
    # and add explicit noise sources for shot noise contributions.
    # ngspice transient noise: use 'trnoise' on independent sources
    
    netlist = """* Phase Noise Extraction via Transient Noise Simulation
* Long transient with noise to extract zero-crossing jitter
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" cap_typ
.include "src/netlist/parameters.inc"

.subckt spiral_ind_53ph p1 p2 sub
L_s p1 n_int 53p
R_s n_int p2 0.312
C_sub1 p1 sub 2f
C_sub2 p2 sub 2f
.ends spiral_ind_53ph

* Supply with thermal noise
Vcc pad_vdd 0 DC {VDD} trnoise(10u 1p 0 0)
V_half vcc_half 0 {VDD/2}
Vcont ctrl 0 0.5
V_dcont d_ctrl 0 0.0

* Current reference with shot noise
I_ref vdd_ref ref_node {IREF} trnoise(1n 1p 0 0)
V_dd vdd_ref 0 {VDD}
X_ref ref_node ref_node 0 0 npn13G2 m={MREF}
X_tail tail_node ref_node 0 0 npn13G2 m={MT}

* Tank
X_ind1 pad_vdd out_x 0 spiral_ind_53ph
X_ind2 pad_vdd out_y 0 spiral_ind_53ph
C_var1 out_x 0 C='40f - 30f * v(ctrl)'
C_var2 out_y 0 C='40f - 30f * v(ctrl)'
X_cbase_x out_x 0 cap_cmim l=17.11u w=17.11u
X_cbase_y out_y 0 cap_cmim l=17.11u w=17.11u
X_cswitch_x out_x node_n cap_cmim l=9.35u w=9.35u
X_cswitch_y out_y node_m cap_cmim l=9.35u w=9.35u
X_switch node_n d_ctrl node_m 0 npn13G2
R_pullup_n node_n vcc_half 10k
R_pullup_m node_m vcc_half 10k

* Core
X1 out_x out_y tail_node 0 npn13G2 m=4
X2 out_y out_x tail_node 0 npn13G2 m=4

* Buffer
C_ac_x out_x buf_in_x {C_AC_COUPLING}
C_ac_y out_y buf_in_y {C_AC_COUPLING}
R_fb_x buf_in_x buf_out_x {R_FB}
R_fb_y buf_in_y buf_out_y {R_FB}
X_buf_x buf_out_x buf_in_x 0 0 npn13G2 m=1
X_buf_y buf_out_y buf_in_y 0 0 npn13G2 m=1
R_load_x pad_vdd buf_out_x {R_LOAD}
R_load_y pad_vdd buf_out_y {R_LOAD}

I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

* Long transient with tight tolerances for noise accuracy
* 50 ns gives us ~1500 cycles at 30 GHz
.options method=gear reltol=1e-6 abstol=1e-12 vntol=1e-9
.options trtol=1
.tran 0.2p 50n

.control
set noaskquit
run

* Save the differential output for post-processing
wrdata sim/raw_results/raw_exp/phase_noise_tran.txt v(out_x) v(out_y)
.endc
.end
"""
    cir_path = os.path.join(NETLIST_DIR, 'exp_phase_noise_tran.cir')
    with open(cir_path, 'w') as f:
        f.write(netlist)
    return cir_path

def extract_phase_noise(data_path):
    """
    Extract phase noise from transient simulation data.
    
    Steps:
    1. Load v(out_x) and v(out_y) time series
    2. Compute v_diff = v(out_x) - v(out_y)
    3. Find positive zero-crossing times using linear interpolation
    4. Compute period deviations (jitter)
    5. Convert jitter to phase noise L(df)
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    print("Loading transient data...")
    data = np.loadtxt(data_path)
    t = data[:, 0]
    vx = data[:, 1]
    vy = data[:, 3]  # ngspice wrdata format: col0=x, col1=y_re, col2=y_im, col3=y2_re...
    
    v_diff = vx - vy
    
    # Skip startup transient (first 5 ns)
    startup_mask = t > 5e-9
    t = t[startup_mask]
    v_diff = v_diff[startup_mask]
    
    # Find positive zero crossings with linear interpolation
    crossings = []
    for i in range(len(v_diff) - 1):
        if v_diff[i] < 0 and v_diff[i+1] >= 0:
            # Linear interpolation for exact crossing time
            t_cross = t[i] + (-v_diff[i]) / (v_diff[i+1] - v_diff[i]) * (t[i+1] - t[i])
            crossings.append(t_cross)
    
    crossings = np.array(crossings)
    N = len(crossings)
    print(f"Found {N} zero crossings ({N-1} complete cycles)")
    
    if N < 100:
        print("ERROR: Not enough zero crossings for reliable phase noise extraction.")
        print("       Need at least 100 cycles. Increase simulation time.")
        return
    
    # Compute periods and jitter
    periods = np.diff(crossings)
    T_mean = np.mean(periods)
    f0 = 1.0 / T_mean
    
    # Cycle-to-cycle jitter
    period_deviations = periods - T_mean
    sigma_cc = np.std(period_deviations)
    
    # Long-term accumulated jitter (Allan deviation-like)
    # Phase deviation: phi(n) = 2*pi * sum(period_deviations[0:n]) / T_mean
    phase_dev = 2 * np.pi * np.cumsum(period_deviations) / T_mean
    
    print(f"\n{'='*60}")
    print(f" PHASE NOISE EXTRACTION RESULTS")
    print(f"{'='*60}")
    print(f"  Oscillation frequency:     {f0/1e9:.4f} GHz")
    print(f"  Mean period:               {T_mean*1e12:.4f} ps")
    print(f"  Cycle-to-cycle jitter:     {sigma_cc*1e15:.2f} fs (RMS)")
    print(f"  Number of cycles analyzed: {N-1}")
    
    # Convert jitter to phase noise at various offset frequencies
    # L(df) = f0^2 * sigma_cc^2 / (2 * df^2)  [linear power]
    df_offsets = np.array([1e3, 10e3, 100e3, 1e6, 10e6])  # 1kHz to 10MHz
    
    print(f"\n  Phase Noise Estimates:")
    print(f"  {'Offset':>10s}   {'L(df) [dBc/Hz]':>16s}")
    print(f"  {'-'*10}   {'-'*16}")
    
    L_values = []
    for df in df_offsets:
        L_linear = (f0**2 * sigma_cc**2) / (2 * df**2)
        L_dBc = 10 * np.log10(L_linear) if L_linear > 0 else -200
        L_values.append(L_dBc)
        
        if df >= 1e6:
            label = f"{df/1e6:.0f} MHz"
        elif df >= 1e3:
            label = f"{df/1e3:.0f} kHz"
        else:
            label = f"{df:.0f} Hz"
        print(f"  {label:>10s}   {L_dBc:>12.1f} dBc/Hz")
    
    # Leeson model prediction for comparison
    # L_leeson(df) = (2*F*k*T/Psig) * (f0 / (2*Q*df))^2
    # Assumptions: F=3 (noise factor), Q=32, Psig from measured swing
    k = 1.38e-23
    T = 300  # room temperature
    F = 3.0  # effective noise factor
    Q = 32   # tank quality factor
    V_swing = 0.35  # estimated Vpp differential
    R_p = 570  # parallel tank resistance
    P_sig = V_swing**2 / (8 * R_p)  # signal power in tank
    
    df_sweep = np.logspace(3, 8, 200)
    L_leeson = (2 * F * k * T / P_sig) * (f0 / (2 * Q * df_sweep))**2
    L_leeson_dBc = 10 * np.log10(L_leeson)
    
    # Phase noise from jitter
    L_jitter = (f0**2 * sigma_cc**2) / (2 * df_sweep**2)
    L_jitter_dBc = 10 * np.log10(np.maximum(L_jitter, 1e-30))
    
    print(f"\n  Leeson Model Parameters:")
    print(f"    F = {F:.1f}, Q = {Q}, Psig = {P_sig*1e6:.2f} uW, Rp = {R_p} Ohm")
    print(f"{'='*60}")
    
    # --- Plot 1: Phase noise spectrum ---
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.semilogx(df_sweep / 1e6, L_jitter_dBc, 'b-', linewidth=2,
                label='Transient Noise Extraction')
    ax.semilogx(df_sweep / 1e6, L_leeson_dBc, 'r--', linewidth=1.5,
                label='Leeson Model Prediction')
    
    # Mark specific offset points
    for i, df in enumerate(df_offsets):
        if L_values[i] > -200:
            ax.plot(df / 1e6, L_values[i], 'ko', markersize=6)
    
    ax.set_xlabel('Offset Frequency (MHz)', fontsize=12)
    ax.set_ylabel('Phase Noise $\\mathcal{L}(\\Delta f)$ (dBc/Hz)', fontsize=12)
    ax.set_title(f'Phase Noise Spectrum — {f0/1e9:.2f} GHz VCO', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, which='both', alpha=0.5)
    ax.set_xlim(1e-3, 100)
    ax.set_ylim(-160, -40)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_phase_noise.png'), dpi=300)
    plt.close()
    print(f"Phase noise plot saved.")
    
    # --- Plot 2: Jitter histogram ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    ax1.hist(period_deviations * 1e15, bins=50, color='steelblue', edgecolor='black', alpha=0.8)
    ax1.set_xlabel('Period Deviation (fs)', fontsize=11)
    ax1.set_ylabel('Count', fontsize=11)
    ax1.set_title(f'Cycle-to-Cycle Jitter Distribution\n$\\sigma_{{cc}}$ = {sigma_cc*1e15:.2f} fs', fontsize=12)
    ax1.axvline(x=0, color='r', linestyle='--', alpha=0.5)
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(np.arange(len(phase_dev)), np.rad2deg(phase_dev), 'b-', linewidth=0.5)
    ax2.set_xlabel('Cycle Number', fontsize=11)
    ax2.set_ylabel('Accumulated Phase Error (degrees)', fontsize=11)
    ax2.set_title('Phase Diffusion (Random Walk)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_jitter_analysis.png'), dpi=300)
    plt.close()
    print(f"Jitter analysis plot saved.")

def main():
    print("="*60)
    print(" Phase Noise Extraction via Transient Noise Simulation")
    print("="*60)
    
    # Step 1: Generate netlist
    cir_path = create_transient_noise_netlist()
    print(f"Netlist: {cir_path}")
    
    # Step 2: Run simulation
    print("\nRunning ngspice transient noise simulation (this may take several minutes)...")
    data_path = os.path.join(RAW_DIR, 'phase_noise_tran.txt')
    
    result = subprocess.run(
        ['ngspice', '-b', cir_path],
        capture_output=True, text=True, timeout=600,
        cwd=PROJECT_ROOT
    )
    
    if result.returncode != 0:
        print(f"ngspice failed: {result.stderr[:500]}")
        return
    
    print("Simulation complete.")
    
    # Step 3: Extract phase noise
    if os.path.exists(data_path):
        extract_phase_noise(data_path)
    else:
        print(f"ERROR: Output file not found: {data_path}")

if __name__ == '__main__':
    main()
