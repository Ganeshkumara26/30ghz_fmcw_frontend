import os
import numpy as np
import matplotlib.pyplot as plt
from exp_utils import DIR_NETLIST, DIR_RAW, DIR_FIGURES, run_ngspice

def run_cap_budget_experiment():
    print("Running Capacitance Budget Experiment...")
    
    stages = [
        {"name": "1_Core", "label": "Tank + Active Core"},
        {"name": "2_Base", "label": "+ Base Capacitors"},
        {"name": "3_Switch", "label": "+ Switch Network (OFF)"},
        {"name": "4_Buffer", "label": "+ Output Buffer (Final)"}
    ]
    
    base_netlist = """* Capacitance Budget - Stage: {stage_name}
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerCAP.lib" cap_typ
.include "02_NETLIST/parameters.inc"

.subckt spiral_ind_53ph p1 p2 sub
L_s p1 n_int 53p
R_s n_int p2 0.312
C_sub1 p1 sub 2f
C_sub2 p2 sub 2f
.ends spiral_ind_53ph

Vcc pad_vdd 0 {{VDD}}
V_half vcc_half 0 {{VDD/2}}
Vcont ctrl 0 0.5
V_dcont d_ctrl 0 0.0
I_ref vdd_ref ref_node {{IREF}}
V_dd vdd_ref 0 {{VDD}}

* 1. Tank Only (always present)
X_ind1 pad_vdd out_x 0 spiral_ind_53ph
X_ind2 pad_vdd out_y 0 spiral_ind_53ph
C_var1 out_x 0 C='40f - 30f * v(ctrl)'
C_var2 out_y 0 C='40f - 30f * v(ctrl)'

{extra_components}

* Startup Kick (if not active core, use ideal negative resistance)
{active_components}

.options method=gear reltol=1e-5
.tran 1p 2n

.control
run
meas tran t1 WHEN v(out_x)=v(out_y) FALL=30
meas tran t2 WHEN v(out_x)=v(out_y) FALL=31
let period = t2 - t1
let freq = 1.0 / period
wrdata 04_SIMULATION/raw_exp/budget_{stage_name}.txt freq
.endc
.end
"""

    components = {
        "1_Core": {
            "extra": "",
            "active": "X1 out_x out_y tail_node 0 npn13G2 m=4\nX2 out_y out_x tail_node 0 npn13G2 m=4\nI_kick out_x out_y PWL(0 0 1p 1m 2p 0)\nX_ref ref_node ref_node 0 0 npn13G2 m={{MREF}}\nX_tail tail_node ref_node 0 0 npn13G2 m={{MT}}"
        },
        "2_Base": {
            "extra": "X_cbase_x out_x 0 cap_cmim l=17.11u w=17.11u\nX_cbase_y out_y 0 cap_cmim l=17.11u w=17.11u",
            "active": "X1 out_x out_y tail_node 0 npn13G2 m=4\nX2 out_y out_x tail_node 0 npn13G2 m=4\nI_kick out_x out_y PWL(0 0 1p 1m 2p 0)\nX_ref ref_node ref_node 0 0 npn13G2 m={{MREF}}\nX_tail tail_node ref_node 0 0 npn13G2 m={{MT}}"
        },
        "3_Switch": {
            "extra": "X_cbase_x out_x 0 cap_cmim l=17.11u w=17.11u\nX_cbase_y out_y 0 cap_cmim l=17.11u w=17.11u\n"
                     "X_cswitch_x out_x node_n cap_cmim l=9.35u w=9.35u\nX_cswitch_y out_y node_m cap_cmim l=9.35u w=9.35u\n"
                     "X_switch node_n d_ctrl node_m 0 npn13G2\nR_pullup_n node_n vcc_half 10k\nR_pullup_m node_m vcc_half 10k",
            "active": "X1 out_x out_y tail_node 0 npn13G2 m=4\nX2 out_y out_x tail_node 0 npn13G2 m=4\nI_kick out_x out_y PWL(0 0 1p 1m 2p 0)\nX_ref ref_node ref_node 0 0 npn13G2 m={{MREF}}\nX_tail tail_node ref_node 0 0 npn13G2 m={{MT}}"
        },
        "4_Buffer": {
            "extra": "X_cbase_x out_x 0 cap_cmim l=17.11u w=17.11u\nX_cbase_y out_y 0 cap_cmim l=17.11u w=17.11u\n"
                     "X_cswitch_x out_x node_n cap_cmim l=9.35u w=9.35u\nX_cswitch_y out_y node_m cap_cmim l=9.35u w=9.35u\n"
                     "X_switch node_n d_ctrl node_m 0 npn13G2\nR_pullup_n node_n vcc_half 10k\nR_pullup_m node_m vcc_half 10k\n"
                     "C_ac_x out_x buf_in_x {{C_AC_COUPLING}}\nC_ac_y out_y buf_in_y {{C_AC_COUPLING}}\n"
                     "R_fb_x buf_in_x buf_out_x {{R_FB}}\nR_fb_y buf_in_y buf_out_y {{R_FB}}\n"
                     "X_buf_x buf_out_x buf_in_x 0 0 npn13G2 m=1\nX_buf_y buf_out_y buf_in_y 0 0 npn13G2 m=1\n"
                     "R_load_x pad_vdd buf_out_x {{R_LOAD}}\nR_load_y pad_vdd buf_out_y {{R_LOAD}}",
            "active": "X1 out_x out_y tail_node 0 npn13G2 m=4\nX2 out_y out_x tail_node 0 npn13G2 m=4\nI_kick out_x out_y PWL(0 0 1p 1m 2p 0)\nX_ref ref_node ref_node 0 0 npn13G2 m={{MREF}}\nX_tail tail_node ref_node 0 0 npn13G2 m={{MT}}"
        }
    }
    
    freqs = []
    labels = []
    
    for stage in stages:
        name = stage["name"]
        content = base_netlist.format(
            stage_name=name,
            extra_components=components[name]["extra"],
            active_components=components[name]["active"]
        )
        cir_path = os.path.join(DIR_NETLIST, f"exp_budget_{name}.cir")
        with open(cir_path, "w") as f:
            f.write(content)
            
        run_ngspice(f"02_NETLIST/experiments/exp_budget_{name}.cir")
        try:
            data = np.loadtxt(os.path.join(DIR_RAW, f"budget_{name}.txt"))
            f_val = data[1] if data.ndim == 1 else data[0, 1]
            freqs.append(f_val / 1e9) # GHz
            labels.append(stage["label"])
        except Exception as e:
            print(f"Failed to read data for {name}: {e}")

    if freqs:
        plt.figure(figsize=(10, 6))
        # Plot a waterfall / bar chart
        bars = plt.bar(labels, freqs, color='tab:blue', alpha=0.8)
        
        # Add values on top of bars
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f'{yval:.2f} GHz', ha='center', va='bottom', fontweight='bold')
            
        plt.ylim(25, max(freqs) + 5)
        plt.ylabel('Oscillation Frequency (GHz)')
        plt.title('Capacitance Budget: Frequency Shift as Components are Added')
        plt.xticks(rotation=15, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(os.path.join(DIR_FIGURES, "fig_cap_budget.png"), dpi=300)
        plt.close()

if __name__ == "__main__":
    run_cap_budget_experiment()
