import gdstk
import math
import os

# IHP SG13G2 Layer Definitions
# TM2 (Top Metal 2) is used for the thick inductor coils
layer_tm2 = (11, 0)
layer_tm1 = (7, 0)
layer_via_tm1_tm2 = (10, 0)
layer_mim = (36, 0) # MIM Top plate

def create_spiral_inductor(cell, x, y, turns=2, width=10, spacing=5, inner_radius=30):
    """
    Creates an octagonal spiral inductor on TM2.
    """
    path = gdstk.RobustPath((x, y), width, layer=layer_tm2[0], datatype=layer_tm2[1])
    
    current_radius = inner_radius
    current_angle = 0
    
    # Generate octagonal segments
    num_segments = turns * 8
    
    # Starting lead
    path.segment((x - current_radius - 20, y), width)
    path.segment((x - current_radius, y), width)
    
    cx, cy = x, y
    for i in range(num_segments):
        angle_rad = current_angle * math.pi / 180
        
        # Calculate next point
        nx = cx + current_radius * math.cos(angle_rad)
        ny = cy + current_radius * math.sin(angle_rad)
        
        path.segment((nx, ny), width)
        
        current_angle += 45
        if current_angle % 360 == 0:
            current_radius += (width + spacing)
            
    # Exit lead on TM1 using via
    path.segment((nx + 20, ny), width)
    cell.add(path)
    
    # Add Via TM1 to TM2 at the center for the underpass
    via = gdstk.rectangle((x-5, y-5), (x+5, y+5), layer=layer_via_tm1_tm2[0], datatype=layer_via_tm1_tm2[1])
    underpass = gdstk.rectangle((x-20, y-5), (x+5, y+5), layer=layer_tm1[0], datatype=layer_tm1[1])
    cell.add(via, underpass)
    
    return cell

def create_mim_capacitor(cell, x, y, length=50, width=50):
    """
    Creates a MIM capacitor using TM1 and MIM layer.
    """
    bottom_plate = gdstk.rectangle((x, y), (x+length, y+width), layer=layer_tm1[0], datatype=layer_tm1[1])
    top_plate = gdstk.rectangle((x+2, y+2), (x+length-2, y+width-2), layer=layer_mim[0], datatype=layer_mim[1])
    
    # Connect top plate to TM2
    via = gdstk.rectangle((x+5, y+5), (x+15, y+15), layer=layer_via_tm1_tm2[0], datatype=layer_via_tm1_tm2[1])
    top_contact = gdstk.rectangle((x, y), (x+length, y+width), layer=layer_tm2[0], datatype=layer_tm2[1])
    
    cell.add(bottom_plate, top_plate, via, top_contact)
    return cell

print("Generating RF Matching Network GDSII (30 GHz)...")
lib = gdstk.Library()
lna_match_cell = lib.new_cell("LNA_MATCHING")

# Instantiate 300pH Inductor
create_spiral_inductor(lna_match_cell, 0, 0, turns=2, width=8, spacing=4, inner_radius=25)

# Instantiate 200fF MIM Capacitor
create_mim_capacitor(lna_match_cell, -100, 0, length=40, width=40)

# Save GDSII
out_dir = "layout"
os.makedirs(out_dir, exist_ok=True)
lib.write_gds(os.path.join(out_dir, "lna_matching.gds"))
print(f"Saved: {os.path.join(out_dir, 'lna_matching.gds')}")
