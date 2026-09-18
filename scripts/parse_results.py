#!/usr/bin/env python3
"""Parse ALL Xyce .mt0 files and compute final RF metrics for the 30GHz blocks."""
import os, re, math

BLOCK_DIR = '/mnt/d/Desktop/Vault/03 Projects/Ganeshas projects/dual_band_radar_soc/netlists/v65_xyce/30ghz_blocks'

def parse_mt0(filename):
    results = {}
    filepath = os.path.join(BLOCK_DIR, filename)
    if not os.path.exists(filepath):
        return results
    with open(filepath) as f:
        for line in f:
            m = re.match(r'\s*(\w+)\s*=\s*([+-]?\d+\.?\d*[eE][+-]?\d+)', line)
            if m:
                results[m.group(1).upper()] = float(m.group(2))
    return results

def vpp_to_dbm(vpp, r=50):
    vrms = vpp / (2 * math.sqrt(2))
    p = vrms**2 / r
    return 10 * math.log10(p / 1e-3) if p > 0 else -999

def gain_db(vout, vin):
    return 20 * math.log10(vout / vin) if vin > 0 and vout > 0 else -999

# === VCO ===
d = parse_mt0('30ghz_vco_standalone.cir.mt0')
if d:
    per = d.get('VCO_PER', 0)
    freq = 2 / per if per > 0 else 0
    vx = d.get('VCO_VPP_X', 0)
    vy = d.get('VCO_VPP_Y', 0)
    idc = abs(d.get('VCO_IDC', 0))
    pdc = 1.2 * idc
    print(f"\n{'─'*72}")
    print(f"  30 GHz VCO (standalone)")
    print(f"{'─'*72}")
    print(f"  Frequency:      {freq/1e9:.2f} GHz  (target: 30.0)")
    print(f"  Vpp (out_x):    {vx*1e3:.1f} mV   (target: >300)")
    print(f"  Vpp (out_y):    {vy*1e3:.1f} mV")
    print(f"  Diff Vpp:       {(vx+vy)*1e3:.1f} mV")
    print(f"  DC Current:     {idc*1e3:.2f} mA")
    print(f"  DC Power:       {pdc*1e3:.2f} mW")
    Q, F = 8.0, 4.0
    df = 10e6
    vs = (vx+vy)/2
    if vs > 0 and freq > 0:
        Ps = vs**2 / (8*50)
        kT = 4.14e-21
        pn = 10*math.log10(2*F*kT/Ps * (freq/(2*Q*df))**2)
        print(f"  PN @10MHz:      {pn:.1f} dBc/Hz (Leeson, Q={Q})")
    status = "✅ PASS" if abs(freq/1e9 - 30.0) < 0.5 and vx > 0.3 else "❌ FAIL"
    print(f"  Status:         {status}")

# === LNA ===
d = parse_mt0('30ghz_lna_standalone.cir.mt0')
if d:
    vout = d.get('LNA_VPP_OUT', 0)
    vin = d.get('LNA_VIN', 0)
    vb = d.get('LNA_VBASE', 0)
    vc = d.get('LNA_VCOLL', 0)
    ve = d.get('LNA_VEMIT', d.get('LNA_VTAIL', 0))
    vdc = d.get('LNA_VOUT_DC', 0)
    g = gain_db(vout, vin)
    print(f"\n{'─'*72}")
    print(f"  30 GHz LNA (standalone)")
    print(f"{'─'*72}")
    print(f"  Vout (PP):      {vout*1e6:.1f} µV")
    print(f"  Vin (PP):       {vin*1e6:.1f} µV")
    print(f"  Voltage Gain:   {g:.1f} dB  (target: >12)")
    print(f"  Vbase (DC):     {vb:.4f} V")
    print(f"  Vcoll_CE (DC):  {vc:.4f} V")
    print(f"  Vemit (DC):     {ve:.4f} V")
    print(f"  Vout (DC):      {vdc:.4f} V")
    status = "✅ PASS" if g > 10 else "❌ NEEDS WORK"
    print(f"  Status:         {status}")

# === IF Amp ===
d = parse_mt0('30ghz_if_amp_standalone.cir.mt0')
if d:
    vout = d.get('IF_VOUT', 0)
    vin = d.get('IF_VIN', 0)
    vb = d.get('IF_VBASE', 0)
    vc = d.get('IF_VCOLL', 0)
    ve = d.get('IF_VEMIT', 0)
    g = gain_db(vout, vin)
    ic = (1.2 - vc) / 1000
    print(f"\n{'─'*72}")
    print(f"  30 GHz IF Amplifier (standalone)")
    print(f"{'─'*72}")
    print(f"  Vout (PP):      {vout*1e3:.2f} mV")
    print(f"  Vin (PP):       {vin*1e3:.3f} mV")
    print(f"  Voltage Gain:   {g:.1f} dB  (target: ~21)")
    print(f"  Vbase (DC):     {vb:.4f} V")
    print(f"  Vcoll (DC):     {vc:.4f} V")
    print(f"  Ic:             {ic*1e3:.2f} mA")
    print(f"  -3dB BW:        estimated from gm={ic/0.026:.1f}mS, R_L=1kΩ")
    status = "✅ PASS" if g > 20 else "❌ FAIL"
    print(f"  Status:         {status}")

# === Mixer ===
d = parse_mt0('30ghz_mixer_standalone.cir.mt0')
if d:
    ifp = d.get('MIX_IF_VPP_P', 0)
    ifn = d.get('MIX_IF_VPP_N', 0)
    lo = d.get('MIX_LO_VPP', 0)
    leak = d.get('MIX_LO_LEAK', 0)
    rfin = d.get('MIX_RF_IN', 0)
    cg = gain_db(ifp, rfin) if rfin > 0 else gain_db(ifp, 0.02)
    iso = -gain_db(leak, lo) if lo > 0 and leak > 0 else 0
    print(f"\n{'─'*72}")
    print(f"  30 GHz Gilbert Mixer (standalone)")
    print(f"{'─'*72}")
    print(f"  IF Vpp (P):     {ifp*1e3:.1f} mV")
    print(f"  IF Vpp (N):     {ifn*1e3:.1f} mV")
    print(f"  RF input Vpp:   {rfin*1e3:.1f} mV")
    print(f"  Conv. Gain:     {cg:.1f} dB  (target: >20)")
    print(f"  LO buf swing:   {lo*1e3:.1f} mV")
    print(f"  LO leakage:     {leak*1e3:.1f} mV")
    print(f"  LO-RF isol:     {iso:.1f} dB  (target: >30)")
    status = "✅ PASS" if cg > 10 else "❌ FAIL"
    print(f"  Status:         {status}")

# === PA ===
d = parse_mt0('30ghz_pa_standalone.cir.mt0')
if d:
    vp = d.get('PA_VPP_P', 0)
    vn = d.get('PA_VPP_N', 0)
    vin = d.get('PA_VIN_PP', 0)
    idc = abs(d.get('PA_IDC', 0))
    pdc = 3.0 * idc
    pout_p = vpp_to_dbm(vp)
    pout_diff = vpp_to_dbm(vp + vn, 100)
    g = gain_db(vp, vin)
    pin_w = (vin/(2*math.sqrt(2)))**2 / 50
    pout_w = (vp/(2*math.sqrt(2)))**2 / 50
    pae = (pout_w - pin_w) / pdc * 100 if pdc > 0 else 0
    print(f"\n{'─'*72}")
    print(f"  30 GHz PA (standalone, Nx=8 scaled)")
    print(f"{'─'*72}")
    print(f"  Vout_p (PP):    {vp*1e3:.1f} mV")
    print(f"  Vout_n (PP):    {vn*1e3:.1f} mV")
    print(f"  Pout (per side):{pout_p:.1f} dBm  (target: +10)")
    print(f"  Pout (diff):    {pout_diff:.1f} dBm")
    print(f"  Vin (PP):       {vin*1e3:.1f} mV")
    print(f"  Gain:           {g:.1f} dB")
    print(f"  PA DC current:  {idc*1e3:.1f} mA")
    print(f"  PA DC power:    {pdc*1e3:.1f} mW")
    print(f"  PAE:            {pae:.2f}%")

# === TX Chain ===
d = parse_mt0('30ghz_tx_chain.cir.mt0')
if d:
    per = d.get('VCO_PER', 0)
    freq = 2 / per if per > 0 else 0
    vco = d.get('VCO_VPP', 0)
    buf = d.get('BUF3_VPP', 0)
    txp = d.get('TX_VPP_P', 0)
    txn = d.get('TX_VPP_N', 0)
    idc = abs(d.get('PA_IDC', 0))
    print(f"\n{'─'*72}")
    print(f"  30 GHz TX Chain (VCO→Buffer→PA)")
    print(f"{'─'*72}")
    print(f"  VCO freq:       {freq/1e9:.2f} GHz")
    print(f"  VCO Vpp:        {vco*1e3:.1f} mV")
    print(f"  Buffer Vpp:     {buf*1e3:.1f} mV")
    print(f"  TX out Vpp (P): {txp*1e3:.1f} mV")
    print(f"  TX out Vpp (N): {txn*1e3:.1f} mV")
    print(f"  TX Pout (P):    {vpp_to_dbm(txp):.1f} dBm")
    print(f"  PA DC current:  {idc*1e3:.1f} mA")

# === RX Chain ===
d = parse_mt0('30ghz_rx_chain.cir.mt0')
if d:
    lna = d.get('LNA_VPP', 0)
    mix = d.get('MIX_IF_VPP', 0)
    ifa = d.get('IFAMP_VPP', 0)
    vin = d.get('RX_VIN', 0)
    print(f"\n{'─'*72}")
    print(f"  30 GHz RX Chain (LNA→Mixer→IF Amp)")
    print(f"{'─'*72}")
    print(f"  RF input Vpp:   {vin*1e3:.2f} mV")
    print(f"  LNA out Vpp:    {lna*1e3:.2f} mV")
    print(f"  Mixer IF Vpp:   {mix*1e3:.2f} mV")
    print(f"  IF Amp out Vpp: {ifa*1e6:.1f} µV")
    if vin > 0:
        lna_g = gain_db(lna, vin)
        total_g = gain_db(ifa, vin)
        print(f"  LNA gain:       {lna_g:.1f} dB")
        print(f"  Total RX gain:  {total_g:.1f} dB")

# === Full Frontend ===
d = parse_mt0('30ghz_frontend_v65.cir.mt0')
if d:
    tx_diff = d.get('TX_VPP_DIFF', 0)
    tx_p = d.get('TX_VPP_P', 0)
    vco = d.get('VCO_VPP', 0)
    rx_lna = d.get('RX_LNA_VPP', 0)
    rx_mix = d.get('RX_MIX_VPP', 0)
    rx_if = d.get('RX_IF_VPP', 0)
    print(f"\n{'─'*72}")
    print(f"  30 GHz Full Frontend Integration (v65)")
    print(f"{'─'*72}")
    print(f"  VCO Vpp:        {vco*1e3:.1f} mV")
    print(f"  TX out Vpp (P): {tx_p*1e3:.1f} mV")
    print(f"  TX out Diff:    {tx_diff*1e3:.1f} mV")
    print(f"  TX Pout (Diff): {vpp_to_dbm(tx_diff, 100):.1f} dBm")
    print(f"  LNA out Vpp:    {rx_lna*1e3:.1f} mV")
    print(f"  Mixer IF Vpp:   {rx_mix*1e3:.1f} mV")
    print(f"  IF Amp out Vpp: {rx_if*1e6:.1f} µV")

print(f"\n{'='*72}")
print("  END OF RESULTS")
print(f"{'='*72}")
