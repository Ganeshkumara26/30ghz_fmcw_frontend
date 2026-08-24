gds read lna_matching.gds
load LNA_MATCHING
extract do local
extract all
ext2sim labels on
ext2sim
ext2spice cthresh 0
ext2spice rthresh 0
ext2spice
quit -noprompt
