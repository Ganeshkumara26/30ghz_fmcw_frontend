#!/usr/bin/env python3
import os
import sys
import numpy as np

# Add parent path to use openems_wrapper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from openems_wrapper import PassiveExtractor

def generate_spiral(ext, name, turns, width, spacing, inner_radius):
    """
    Generate a true rectangular spiral inductor using center-point path routing.
    This guarantees zero short-circuits and exact geometry.
    """
    z_height = 9.0
    z_under = 6.0
    pitch = width + spacing
    r = inner_radius

    ext.add_metal('TopMetal2')
    ext.add_metal('TopMetal1')
    ext.add_metal('Vias')
    
    def draw_seg(seg_name, layer, pa, pb, z_base, thickness=2.0):
        x_min = min(pa[0], pb[0]) - width/2
        x_max = max(pa[0], pb[0]) + width/2
        y_min = min(pa[1], pb[1]) - width/2
        y_max = max(pa[1], pb[1]) + width/2
        ext.add_rectangle(seg_name, layer, (x_min, x_max), (y_min, y_max), z_base)
        
    def draw_via(via_name, pa, z_start, z_stop):
        x_min = pa[0] - width/2
        x_max = pa[0] + width/2
        y_min = pa[1] - width/2
        y_max = pa[1] + width/2
        ext.add_via(via_name, 'Vias', (x_min, x_max), (y_min, y_max), z_start, z_stop)

    # Generate TopMetal2 spiral points
    pts = [(r, -r)]
    for t in range(turns):
        pts.append((r + t*pitch, r + t*pitch))                     # Right
        pts.append((-r - (t+1)*pitch, r + t*pitch))                # Top
        pts.append((-r - (t+1)*pitch, -r - (t+1)*pitch))           # Left
        pts.append((r + (t+1)*pitch, -r - (t+1)*pitch))            # Bottom

    # Draw TopMetal2 segments
    for i in range(len(pts)-1):
        draw_seg(f'{name}_seg{i}', 'TopMetal2', pts[i], pts[i+1], z_height)

    # Outer terminal is the last point
    out_pt = pts[-1]
    
    # Via down to TopMetal1 at outer terminal
    draw_via(f'{name}_via_out', out_pt, z_under, z_height+2.0)
    
    # Route underpass on TopMetal1 back to center
    # Point 1: (out_x, out_y) -> (0, out_y)
    draw_seg(f'{name}_underpass_x', 'TopMetal1', out_pt, (0, out_pt[1]), z_under)
    # Point 2: (0, out_y) -> (0, -r)
    draw_seg(f'{name}_underpass_y', 'TopMetal1', (0, out_pt[1]), (0, -r), z_under)

    # PORT CONTACT WALLS
    # Terminal 1: (0, -r) (from underpass)
    draw_via(f'{name}_port_wall_left', (0, -r), z_under, z_height+2.0)
    # Terminal 2: (r, -r) (inner spiral start)
    draw_via(f'{name}_port_wall_right', (r, -r), z_under, z_height+2.0)
    
    # Port across the inner gap: X from (0 + width/2) to (r - width/2)
    ext.add_port(1, [width/2, -r - width/2, z_under], 
                    [r - width/2, -r + width/2, z_height+2.0], 50, 'x', excite=True)
    
    # Mesh
    r_max = max(abs(out_pt[0]), abs(out_pt[1])) + 50
    x_mesh = np.arange(-r_max, r_max+1, 2.0)
    y_mesh = np.arange(-r_max, r_max+1, 2.0)
    z_mesh = np.array([0, z_under-2, z_under, z_under+2.0, z_height, z_height+2, z_height+4, 20.0])
    
    ext.CSX.GetGrid().AddLine('x', x_mesh)
    ext.CSX.GetGrid().AddLine('y', y_mesh)
    ext.CSX.GetGrid().AddLine('z', z_mesh)

def run_extraction(target_name, turns, inner_radius_um):
    print(f"--- Extracting {target_name} ---")
    ext = PassiveExtractor(freq_start=10e9, freq_stop=50e9, unit='um')
    generate_spiral(ext, target_name, turns=turns, width=5.0, spacing=2.0, inner_radius=inner_radius_um)
    
    # Setup excitation
    f0 = 30e9
    fc = 50e9
    ext.FDTD.SetGaussExcite(f0, fc)
    
    out_dir = os.path.abspath(f'./{target_name}_em')
    
    cwd = os.getcwd()
    s_params = ext.run(out_dir)
    os.chdir(cwd)
    
    if s_params and 'S11' in s_params:
        from sparam_wrapper import TouchstoneHandler
        ts_file = f"{target_name}.s2p"
        TouchstoneHandler.write(ts_file, s_params['freq'], 
                                s_params['S11'], s_params.get('S12', s_params['S11']), 
                                s_params.get('S21', s_params['S11']), s_params.get('S22', s_params['S11']))
        print(f"Generated {ts_file}")
    else:
        print(f"Failed {target_name}")

if __name__ == '__main__':

    # Run for different approximate geometries
    # LNA Degeneration: ~60pH
    run_extraction("ind_60pH", turns=1, inner_radius_um=30)
    
    # LNA Load: ~100pH
    run_extraction("ind_100pH", turns=1, inner_radius_um=40)
    
    # PA Load: ~125pH
    run_extraction("ind_125pH", turns=2, inner_radius_um=25)
    
    # LNA Match: ~180pH
    run_extraction("ind_180pH", turns=2, inner_radius_um=35)
    
    # VCO: ~200pH
    run_extraction("ind_200pH", turns=2, inner_radius_um=40)
    
    # PA Load: ~500pH
    run_extraction("ind_500pH", turns=3, inner_radius_um=45)
