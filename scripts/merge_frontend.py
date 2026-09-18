import re

tx = open("30ghz_tx_chain.cir").read()
rx = open("30ghz_rx_chain.cir").read()

# Strip dot commands from TX except libs and options
tx_lines = []
for line in tx.split("\n"):
    if line.startswith(".ic") or line.startswith(".tran") or line.startswith(".measure") or line.startswith(".print") or line.startswith(".end"):
        continue
    tx_lines.append(line)

# Strip dot commands from RX and libraries
rx_lines = []
rx_capture = False
for line in rx.split("\n"):
    if "=== LNA" in line:
        rx_capture = True
    if line.startswith(".tran"):
        rx_capture = False
        
    if rx_capture:
        if line.startswith("V_lo_p") or line.startswith("V_lo_n"):
            # Replace ideal LO with tapping from VCO buffer
            continue
        rx_lines.append(line)

out = "\n".join(tx_lines) + "\n\n* === RX SECTION ===\n" + "\n".join(rx_lines)

# Connect LO to Mixer
out += """
* Connect LO from VCO Buffer to Mixer
* In TX chain, we have buf2_n and buf2_p. We'll use those.
E_lo_p lo_p 0 buf2_p 0 1.0
E_lo_n lo_n 0 buf2_n 0 1.0

* Analysis
.tran 0.5p 20n 0 0.5p

.measure tran tx_vpp_diff PP v(out_p, out_n) FROM=15n TO=20n
.measure tran tx_vpp_p PP v(out_p) FROM=15n TO=20n
.measure tran vco_vpp PP v(out_x) FROM=15n TO=20n
.measure tran rx_lna_vpp PP v(lna_out) FROM=15n TO=20n
.measure tran rx_mix_vpp PP v(if_p) FROM=15n TO=20n
.measure tran rx_if_vpp PP v(if_out) FROM=15n TO=20n

.print tran v(out_x) v(out_p) v(out_n) v(lna_out) v(if_p) v(if_out)

.end
"""

# Need to add RX Vdds
rx_vdds = """
Vdd_rx vdd 0 1.2
Vdd_if vdd_if 0 1.2
Vdd_lna vdd_lna 0 3.0
V_rx rx_in 0 SIN(0 0.001 30G)
"""
out = out.replace("Vdd_30 vdd_30 0 1.2", "Vdd_30 vdd_30 0 1.2\n" + rx_vdds)

# Also need to make sure models are included
if ".include ind_180pH_model.cir" not in out:
    out = out.replace(".include ind_125pH_model.cir", ".include ind_125pH_model.cir\n.include ind_180pH_model.cir\n.include ind_60pH_model.cir\n.include ind_100pH_model.cir\n")

open("30ghz_frontend_v65.cir", "w").write(out)
