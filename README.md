# 30 GHz FMCW Radar Analog Frontend

**Process**: IHP SG13G2 (130nm SiGe BiCMOS)
**Application**: CSSR Body Detection Radar
**Frequency**: 30 GHz

Analog frontend for a 30 GHz FMCW radar system, including the VCO, LNA, PA, Mixer, IF Amplifier, and ADC.

## Repository Structure

```
analog_frontend/
├── docs/                          # Design documentation
│   ├── NETLISTS.md                # SPICE netlist documentation with design equations
│   └── GAP_ANALYSIS.md            # Gap analysis of current design
├── vco/                           # 30 GHz Voltage-Controlled Oscillator
│   ├── docs/                      # VCO design dossier (Razavi methodology)
│   ├── netlists/                  # SPICE netlists (vco_30ghz.cir, vco_30ghz_3bit.cir)
│   ├── sim/                       # Simulation scripts (Python)
│   ├── layout/                    # GDSII layout
│   └── figures/                   # Design figures (PNG/SVG)
├── lna/                           # Low Noise Amplifier
│   ├── netlists/                  # LNA schematics and testbenches
│   ├── testbenches/               # (reserved)
│   ├── layout/                    # GDSII layout with DRC runs
│   └── plots/                     # Simulation results (S-params, NF, etc.)
├── pa/                            # Power Amplifier
│   ├── netlists/                  # PA schematics (Class-E, Class-A)
│   └── testbenches/               # (reserved)
├── mixer/                         # Gilbert Cell Mixer
│   ├── netlists/                  # Mixer schematic
│   └── testbenches/               # Mixer testbench
├── adc/                           # SAR ADC (behavioral)
│   └── netlists/                  # Behavioral model
├── pex/                           # Parasitic Extraction
│   └── pex_runset.tcl             # PEX runset
├── schematic/                     # Top-level schematics
│   ├── afe_top_tb.cir             # Full AFE testbench
│   └── mixed_signal_top.cir       # Mixed-signal top-level
├── figures/                       # Architecture and block diagrams
└── complete_frontend.cir          # Complete frontend netlist (finalized, tapeout-ready)
```

## Key Design Files

| Block | File | Description |
|-------|------|-------------|
| VCO | `vco/netlists/vco_30ghz.cir` | 30 GHz LC-VCO, 0.95V supply |
| VCO | `vco/netlists/vco_30ghz_3bit.cir` | VCO with 3-bit tuning |
| VCO | `vco/docs/Razavi_30GHz_VCO_Design_Dossier.md` | Full design methodology |
| LNA | `lna/netlists/lna_comprehensive_tb.cir` | LNA comprehensive testbench |
| LNA | `lna/layout/lna_matching.gds` | LNA layout |
| PA | `pa/netlists/pa_classE.cir` | Class-E Power Amplifier |
| PA | `pa/netlists/pa_schematic.cir` | PA schematic |
| Mixer | `mixer/netlists/mixer_gilbert.cir` | Gilbert Cell Mixer |
| Mixer | `mixer/netlists/mixer_tb.cir` | Mixer testbench |
| ADC | `adc/netlists/adc_sar_behavioral.cir` | SAR ADC behavioral model |
| Top | `complete_frontend.cir` | Complete frontend netlist (finalized, tapeout-ready) |

## Simulation

VCO simulation scripts are in `vco/sim/` and include:
- `exp_phase_noise.py` - Phase noise analysis
- `exp_tuning.py` - Tuning range characterization
- `exp_startup.py` - Startup transient
- `exp_pvt.py` - PVT corners
- `exp_load_pull.py` - Load pull analysis

## PDK Reference

```
.lib "../pdk/IHP-Open-PDK/ihp-sg13g2/libs.tech/ngspice/models/cornerHBT.lib" hbt_typ
```
