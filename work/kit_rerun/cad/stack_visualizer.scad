/*
R0 sodium-birnessite symmetric cell — exploded stack visualizer.

IMPORTANT:
- This is a component-layout illustration, NOT a fabrication drawing.
- The source paper reports 15 mm Toray carbon-paper discs and identifies a
  cellulose separator, but does not publish all thicknesses/diameters,
  spring force, gasket geometry, sealing details or the exact slurry layer.
- Only 15 mm electrode/current-collector diameter is paper-reported.
- All other dimensions below are explicitly illustrative visualization values.
- Do not manufacture, seal, pressurize or electrically operate a cell from this file.
  Use the specified commercial research fixture and its current manufacturer drawings.
*/

$fn = 96;
paper_electrode_diameter_mm = 15.0; // reported in 2019 paper

// Visualization-only dimensions; not approved for fabrication.
carbon_paper_thickness_mm = 0.20;
active_coating_thickness_mm = 0.05;
separator_diameter_mm = 17.0;
separator_thickness_mm = 0.20;
contact_plate_diameter_mm = 18.0;
contact_plate_thickness_mm = 1.00;
exploded_gap_mm = 4.0;
show_labels = true;

module disc(d, t, z, c) {
    color(c) translate([0,0,z]) cylinder(d=d, h=t, center=false);
}
module label3d(txt, z, x=10) {
    if (show_labels) color("black") translate([x, -2, z])
        linear_extrude(height=0.15) text(txt, size=1.4, font="Liberation Sans");
}

z0 = 0;
z1 = contact_plate_thickness_mm + exploded_gap_mm;
z2 = z1 + carbon_paper_thickness_mm + exploded_gap_mm;
z3 = z2 + active_coating_thickness_mm + exploded_gap_mm;
z4 = z3 + separator_thickness_mm + exploded_gap_mm;
z5 = z4 + active_coating_thickness_mm + exploded_gap_mm;
z6 = z5 + carbon_paper_thickness_mm + exploded_gap_mm;

disc(contact_plate_diameter_mm, contact_plate_thickness_mm, z0, [0.72,0.74,0.77]);
label3d("Bottom contact (illustrative)", z0);
disc(paper_electrode_diameter_mm, carbon_paper_thickness_mm, z1, [0.12,0.12,0.13]);
label3d("Toray paper: 15 mm reported", z1);
disc(paper_electrode_diameter_mm, active_coating_thickness_mm, z2, [0.45,0.62,0.28]);
label3d("Na0.27MnO2 + carbon layer", z2);
disc(separator_diameter_mm, separator_thickness_mm, z3, [0.92,0.88,0.58]);
label3d("Cellulose separator (dimensions assumed)", z3);
disc(paper_electrode_diameter_mm, active_coating_thickness_mm, z4, [0.45,0.62,0.28]);
label3d("Na0.27MnO2 + carbon layer", z4);
disc(paper_electrode_diameter_mm, carbon_paper_thickness_mm, z5, [0.12,0.12,0.13]);
label3d("Toray paper: 15 mm reported", z5);
disc(contact_plate_diameter_mm, contact_plate_thickness_mm, z6, [0.72,0.74,0.77]);
label3d("Top contact (illustrative)", z6);

// Axis marker
color("red") translate([-12,0,0]) cube([0.15,0.15,z6+contact_plate_thickness_mm]);
color("green") translate([-12,0,0]) cube([8,0.15,0.15]);
color("blue") translate([-12,0,0]) cube([0.15,0.15,8]);
