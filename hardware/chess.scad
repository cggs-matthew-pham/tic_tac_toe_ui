// Chess board with self-centring pockets, for the myCobot 280. PROTOTYPE.
//
// Each square is a tapered pocket: a narrow flat floor, walls sloping up
// to a thin flat ridge shared with the neighbouring squares. A piece
// dropped a few mm off-centre lands on a wall and slides to the centre.
// Pieces taper gently (narrow base, wider flat top for the suction cup)
// so they stay clear of the walls once seated and can't wedge.
//
//   capture range = (square - flat - floor) / 2   (how far off a drop can be)
//   floor         = piece_base + clearance
//
// PRINT THE TEST TILE FIRST: open chess_test.scad (short print). Two 2x2
// patches, one with each flat width in test_flats, plus 3 pieces. Check the
// fit by hand, then on the arm, before printing the full board from this file.
// All sizes are set here; chess_test.scad uses them, so the two always match.
//
// Open in OpenSCAD: F5 preview, F6 render, File > Export > STL.
// Window > Customizer shows every value below as a slider.
//
// Layout, seen from White's side with the robot beyond rank 8:
//
//                ROBOT
//   [captured] a8 ... h8 [captured]
//              ...
//              a1 ... h1
//
// Captured-piece pockets are separate strips (PART = "graveyard"; print
// two), so the board fits a 180 mm bed.

/* [What to show / export] */
PART = "board";  // "board", "graveyard", "pieces", "all" (preview only). Test tile: chess_test.scad

/* [Squares and pockets] */
square     = 20;    // square size = pocket spacing
flat       = 1;     // flat ridge between pockets; ~1 mm prints cleanly, 0 is too sharp to print
depth      = 5;     // pocket depth
thickness  = 7;     // board thickness (floor under pockets = thickness - depth)
clearance  = 1.0;   // floor = piece_base + this. 0.6-1.0 for FDM; less wedges, more rattles.

/* [Pieces] */
piece_base = 12;    // width at the bottom
piece_top  = 15;    // width of the flat top (suction cup lands here)
piece_h    = 15;    // all pieces the same height, so one drop height fits all
letters    = true;  // engrave K Q R B N P on one side (never on top: spoils suction)

/* [Board] */
margin       = 5;   // border around the 8x8 grid
labels       = true;
label_size   = 3.5; // square names (a1..h8) on the pocket floors
label_depth  = 0.4;

/* [Graveyard strips] */
grave_cols = 2;     // pockets across each strip
grave_rows = 8;     // pockets along each strip (2 x 8 = 16, enough for every capture)

/* [Test tile] */
test_flats = [1, 2];  // one 2x2 patch per value

$fn = 32;

floor_w   = piece_base + clearance;
opening_w = square - flat;
capture   = (opening_w - floor_w) / 2;
wall_angle = atan(depth / capture);   // from horizontal

assert(opening_w > floor_w + 1, "No room for a slope: lower piece_base or raise square");
assert(depth < thickness - 1, "Pocket too deep for the board thickness");
assert(wall_angle >= 40, "Walls under 40 deg from horizontal: PLA may not slide. Deepen or narrow.");
// Seated piece must stay narrower than the pocket at the rim.
assert(piece_base + (piece_top - piece_base) * depth / piece_h < opening_w - 1,
       "Piece too wide at the rim: it will rest on the walls");

board_w = 8 * square + 2 * margin;
board_l = 8 * square + 2 * margin;

echo(str("Floor ", floor_w, " mm, opening ", opening_w, " mm, capture +/-", capture,
         " mm, walls ", round(wall_angle), " deg."));
echo(str("Board ", board_w, " x ", board_l, " mm. Graveyard strip ",
         grave_cols * square + 2 * margin, " x ", grave_rows * square + 2 * margin, " mm."));

// ---- One pocket, cut from the top surface ----
module pocket(open_w, label = "") {
    translate([0, 0, thickness - depth]) {
        linear_extrude(height = depth + 0.01, scale = open_w / floor_w)
            square(floor_w, center = true);
        if (labels && label != "")
            translate([0, 0, -label_depth])
                linear_extrude(height = label_depth + 0.01)
                    text(label, size = label_size, halign = "center", valign = "center",
                         font = "Liberation Sans:style=Bold");
    }
}

// A cols x rows grid of pockets at `square` spacing, on a plate with `margin`.
module pocket_plate(cols, rows, open_w, names = undef, edge_text = "") {
    difference() {
        cube([cols * square + 2 * margin, rows * square + 2 * margin, thickness]);
        for (c = [0:cols - 1], r = [0:rows - 1])
            translate([margin + (c + 0.5) * square, margin + (r + 0.5) * square, 0])
                pocket(open_w, names == undef ? "" : names[c][r]);
        if (labels && edge_text != "")
            translate([(cols * square + 2 * margin) / 2,
                       rows * square + 2 * margin - margin / 2, thickness - label_depth])
                linear_extrude(height = label_depth + 0.01)
                    text(edge_text, size = min(3.5, margin * 0.7), halign = "center",
                         valign = "center", font = "Liberation Sans:style=Bold");
    }
}

FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];

module board() {
    names = [for (f = [0:7]) [for (r = [0:7]) str(FILES[f], r + 1)]];
    pocket_plate(8, 8, opening_w, names, "ROBOT");
}

module graveyard() {
    pocket_plate(grave_cols, grave_rows, opening_w);
}

module test_tile() {
    for (i = [0:len(test_flats) - 1]) {
        f = test_flats[i];
        translate([i * (2 * square + 2 * margin + 5), 0, 0])
            difference() {
                pocket_plate(2, 2, square - f);
                // flat width engraved on the front edge, so you know which is which
                translate([square + margin, margin / 2, thickness - label_depth])
                    linear_extrude(height = label_depth + 0.01)
                        text(str(f, "mm"), size = min(3.5, margin * 0.7), halign = "center",
                             valign = "center", font = "Liberation Sans:style=Bold");
            }
    }
    // three pieces to try in them
    for (i = [0:2])
        translate([i * (piece_top + 5) + piece_top / 2, -piece_top, 0]) piece(["K", "N", "P"][i]);
}

// ---- Piece: tapered, flat top, optional letter on one side ----
module piece(letter = "") {
    side_tilt = atan(((piece_top - piece_base) / 2) / piece_h);
    difference() {
        hull() {
            translate([0, 0, 0.005]) cube([piece_base, piece_base, 0.01], center = true);
            translate([0, 0, piece_h - 0.005]) cube([piece_top, piece_top, 0.01], center = true);
        }
        if (letters && letter != "")
            translate([0, -(piece_base + piece_top) / 4, piece_h / 2])
                rotate([side_tilt, 0, 0]) rotate([90, 0, 0])
                    linear_extrude(height = 1, center = true)
                        text(letter, size = piece_h * 0.45, halign = "center", valign = "center",
                             font = "Liberation Sans:style=Bold");
    }
}

SET = ["K", "Q", "R", "R", "B", "B", "N", "N", "P", "P", "P", "P", "P", "P", "P", "P"];

module pieces() {
    // One side's set. Print twice, in two colours. Add an extra Q per side
    // if you want promotion spares.
    for (i = [0:len(SET) - 1])
        translate([(i % 4) * (piece_top + 5), floor(i / 4) * (piece_top + 5), 0])
            piece(SET[i]);
}

if (PART == "test") test_tile();
else if (PART == "board") board();
else if (PART == "graveyard") graveyard();
else if (PART == "pieces") pieces();
else {
    board();
    translate([-(grave_cols * square + 2 * margin) - 6, 0, 0]) graveyard();
    translate([board_w + 6, 0, 0]) graveyard();
    translate([piece_top / 2, -4 * (piece_top + 5), 0]) color("orange") pieces();
}
