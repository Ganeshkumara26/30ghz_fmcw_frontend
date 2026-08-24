"""
Experiment: 3-Bit Switched-Capacitor Tuning Curve Characterization
Sweeps all 8 digital states x 6 varactor voltages = 48 operating points.

Design rationale for cap sizing:
  Original 1-bit design: base=17.11u, switch=9.35u
    - Switch OFF: ~30.83 GHz
    - Switch ON:  ~29.84 GHz  (delta ~1 GHz from 9.35u cap)

  For 28-32 GHz coverage with 3-bit bank:
    - Base cap: l=16.0u (slightly reduced -> pushes f_max up to ~32 GHz)
    - Bit 0 (LSB): l=6.6u  (~0.5 GHz step)
    - Bit 1:       l=9.35u (~1.0 GHz step, matches proven original)
    - Bit 2 (MSB): l=13.2u (~2.0 GHz step)
    - Total bank ON: ~3.5 GHz shift -> 28.5 GHz
    - Varactor adds ~1 GHz continuous tuning within each sub-band
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

# PDK lib path (relative to PROJECT_ROOT)
PDK_HBT = "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib"
PDK_CAP = "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib"
PARAMS = "src/netlist/parameters.inc"

# Cap dimensions — sized for ~4 GHz total range (28-32 GHz)
# Original 1-bit: l=9.35u shifts ~1 GHz.
# Need total ~4 GHz from bank = 4x original.
# Binary: 1x + 2x + 4x = 7x ≈ 4 GHz at 1x ≈ 0.57 GHz
BASE_CAP_L = "16.5u"     # reduced from 17.11u to push f_max to ~32 GHz
BIT0_CAP_L = "9.35u"     # LSB ~0.6 GHz (proven original)
BIT1_CAP_L = "15.0u"     # ~1.3 GHz step (2× LSB area ratio)
BIT2_CAP_L = "21.0u"     # MSB ~2.6 GHz step (4× LSB area ratio)


def generate_netlist(bit2, bit1, bit0, v_ctrl, tag):
    """Generate a transient simulation netlist for one operating point."""
    d2 = 1.2 if bit2 else 0.0
    d1 = 1.2 if bit1 else 0.0
    d0 = 1.2 if bit0 else 0.0

    netlist = f"""* 3-Bit Tuning: state={bit2}{bit1}{bit0}, Vctrl={v_ctrl:.2f}
.lib "{PDK_HBT}" hbt_typ
.lib "{PDK_CAP}" cap_typ
.include "{PARAMS}"

.subckt spiral_ind_53ph p1 p2 sub
L_s p1 n_int 53p
R_s n_int p2 0.312
C_sub1 p1 sub 2f
C_sub2 p2 sub 2f
.ends spiral_ind_53ph

Vcc pad_vdd 0 {{VDD}}
V_half vcc_half 0 {{VDD/2}}
Vcont ctrl 0 {v_ctrl:.2f}

* Digital controls
V_d0 d_ctrl_0 0 {d0}
V_d1 d_ctrl_1 0 {d1}
V_d2 d_ctrl_2 0 {d2}

* Tank inductors
X_ind1 pad_vdd out_x 0 spiral_ind_53ph
X_ind2 pad_vdd out_y 0 spiral_ind_53ph

* Varactors (continuous tuning)
C_var1 out_x 0 C='40f - 30f * v(ctrl)'
C_var2 out_y 0 C='40f - 30f * v(ctrl)'

* Base capacitors (reduced for higher f_max)
X_cbase_x out_x 0 cap_cmim l={BASE_CAP_L} w={BASE_CAP_L}
X_cbase_y out_y 0 cap_cmim l={BASE_CAP_L} w={BASE_CAP_L}

* Bit 0 (LSB)
X_csw0_x out_x node_n0 cap_cmim l={BIT0_CAP_L} w={BIT0_CAP_L}
X_csw0_y out_y node_m0 cap_cmim l={BIT0_CAP_L} w={BIT0_CAP_L}
X_sw0 node_n0 d_ctrl_0 node_m0 0 npn13G2
R_pu0_n node_n0 vcc_half 10k
R_pu0_m node_m0 vcc_half 10k

* Bit 1
X_csw1_x out_x node_n1 cap_cmim l={BIT1_CAP_L} w={BIT1_CAP_L}
X_csw1_y out_y node_m1 cap_cmim l={BIT1_CAP_L} w={BIT1_CAP_L}
X_sw1 node_n1 d_ctrl_1 node_m1 0 npn13G2
R_pu1_n node_n1 vcc_half 10k
R_pu1_m node_m1 vcc_half 10k

* Bit 2 (MSB)
X_csw2_x out_x node_n2 cap_cmim l={BIT2_CAP_L} w={BIT2_CAP_L}
X_csw2_y out_y node_m2 cap_cmim l={BIT2_CAP_L} w={BIT2_CAP_L}
X_sw2 node_n2 d_ctrl_2 node_m2 0 npn13G2
R_pu2_n node_n2 vcc_half 10k
R_pu2_m node_m2 vcc_half 10k

* Cross-coupled core
X1 out_x out_y tail_node 0 npn13G2 m=4
X2 out_y out_x tail_node 0 npn13G2 m=4

* Ideal tail current
I_tail tail_node 0 1m

* Startup kick
I_kick out_x out_y PWL(0 0 1p 1m 2p 0)

.options method=gear reltol=1e-5
.tran 1p 2n

.control
run
meas tran t1 WHEN v(out_x)=v(out_y) FALL=30
meas tran t2 WHEN v(out_x)=v(out_y) FALL=31
let period = t2 - t1
let freq = 1.0 / period
wrdata sim/raw_results/raw_exp/tuning3b_{tag}.txt freq
.endc
.end
"""
    cir_path = os.path.join(NETLIST_DIR, f'exp_tuning3b_{tag}.cir')
    with open(cir_path, 'w') as f:
        f.write(netlist)
    return cir_path


def run_ngspice(cir_path):
    try:
        result = subprocess.run(
            ['ngspice', '-b', cir_path],
            capture_output=True, text=True, timeout=120,
            cwd=PROJECT_ROOT
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  Exception: {e}")
        return False


def main():
    print("=" * 60)
    print(" 3-Bit Switched-Capacitor Tuning Curve Characterization")
    print("=" * 60)
    print(f" Base cap:  l={BASE_CAP_L}")
    print(f" Bit 0:     l={BIT0_CAP_L}")
    print(f" Bit 1:     l={BIT1_CAP_L}")
    print(f" Bit 2:     l={BIT2_CAP_L}")
    print()

    v_ctrl_list = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    states = []
    for code in range(8):
        b2 = (code >> 2) & 1
        b1 = (code >> 1) & 1
        b0 = code & 1
        states.append((b2, b1, b0))

    results = {}
    total = len(states) * len(v_ctrl_list)
    count = 0

    for (b2, b1, b0) in states:
        state_key = f"{b2}{b1}{b0}"
        results[state_key] = {'v_ctrl': [], 'freq': []}

        for v_ctrl in v_ctrl_list:
            count += 1
            tag = f"s{state_key}_v{int(v_ctrl * 10)}"
            print(f"  [{count:2d}/{total}] State={state_key}, Vctrl={v_ctrl:.1f}V ... ",
                  end='', flush=True)

            cir_path = generate_netlist(b2, b1, b0, v_ctrl, tag)
            success = run_ngspice(cir_path)

            if success:
                try:
                    data_path = os.path.join(RAW_DIR, f'tuning3b_{tag}.txt')
                    data = np.loadtxt(data_path)
                    freq = data[1] if data.ndim == 1 else data[0, 1]
                    if freq > 10e9:
                        results[state_key]['v_ctrl'].append(v_ctrl)
                        results[state_key]['freq'].append(freq / 1e9)
                        print(f"{freq / 1e9:.2f} GHz")
                    else:
                        print("FAILED (no oscillation)")
                except Exception as e:
                    print(f"FAILED ({e})")
            else:
                print("FAILED (ngspice)")

    # ===== Plotting =====
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3',
              '#ff7f00', '#a65628', '#f781bf', '#999999']
    markers = ['o', 's', '^', 'v', 'D', 'p', 'h', '*']

    fig, ax = plt.subplots(figsize=(10, 6))

    all_freqs = []
    for i, (b2, b1, b0) in enumerate(states):
        state_key = f"{b2}{b1}{b0}"
        vc = results[state_key]['v_ctrl']
        fr = results[state_key]['freq']
        if vc:
            ax.plot(vc, fr, linewidth=2, marker=markers[i], color=colors[i],
                    label=f'Sub-band {i} ({state_key})', markersize=7)
            all_freqs.extend(fr)

    if all_freqs:
        f_min = min(all_freqs)
        f_max = max(all_freqs)
        # Target band
        ax.axhspan(28, 32, color='green', alpha=0.08, label='Target: 28–32 GHz')
        ax.axhline(y=30, color='gray', linestyle=':', alpha=0.4)

    ax.set_xlabel('Varactor Control Voltage $V_{ctrl}$ (V)', fontsize=12)
    ax.set_ylabel('Oscillation Frequency (GHz)', fontsize=12)
    ax.set_title('3-Bit Switched-Capacitor VCO Tuning Curves', fontsize=14)
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9)
    ax.grid(True, alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, 'fig_tuning_3bit.png'), dpi=300,
                bbox_inches='tight')
    plt.close()

    # Summary
    print("\n" + "=" * 60)
    print(" TUNING SUMMARY")
    print("=" * 60)
    if all_freqs:
        print(f"  Minimum frequency: {min(all_freqs):.2f} GHz")
        print(f"  Maximum frequency: {max(all_freqs):.2f} GHz")
        print(f"  Total range:       {max(all_freqs) - min(all_freqs):.2f} GHz")
        f_center = (max(all_freqs) + min(all_freqs)) / 2
        ftr = (max(all_freqs) - min(all_freqs)) / f_center * 100
        print(f"  Center frequency:  {f_center:.2f} GHz")
        print(f"  Fractional range:  {ftr:.1f}%")

    for i, (b2, b1, b0) in enumerate(states):
        state_key = f"{b2}{b1}{b0}"
        fr = results[state_key]['freq']
        if fr:
            print(f"  Sub-band {i} ({state_key}): {min(fr):.2f} – {max(fr):.2f} GHz"
                  f"  (span {max(fr)-min(fr):.2f} GHz)")


if __name__ == '__main__':
    main()
