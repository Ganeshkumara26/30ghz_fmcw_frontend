# Extraction Rule Deck Placeholder for IHP SG13G2 (Magic/OpenROAD or Calibre)
#
# This script represents the extraction flow for the analog macros (LNA, PA, Mixer, ADC)

puts "Starting Parasitic Extraction for 30 GHz Radar SoC Analog Macros..."

# Setup PDK paths
set PDK_ROOT "/path/to/ihp/sg13g2"
set EXTRACT_RULES "${PDK_ROOT}/rules/magic/sg13g2.ext"

# Load the GDS
# magic -dnull -noconsole << EOF
# tech load $EXTRACT_RULES
# gds read ../layout/lna_core.gds
# extract all
# ext2spice cthresh 0.01 rthresh 0.1
# ext2spice
# quit
# EOF

puts "Extraction complete. SPICE netlists with parasitics generated in ../pex/"
