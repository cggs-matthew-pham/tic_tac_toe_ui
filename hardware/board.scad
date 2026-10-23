// Tic-tac-toe board with self-centring pockets, for the myCobot 280.
//
// A block dropped a couple of mm off-centre lands on a sloped wall and
// slides down onto the flat floor. Staging pockets do the same for
// pick-ups, so every block starts in exactly the same place.
//
// Open in OpenSCAD: F5 to preview, F6 to render, then File > Export > STL.
// Set PART below to export the board and the blocks separately.
//
// Layout, seen from the player's side with the robot at the far edge:
//
//            ROBOT
//    X1 |  1   2   3  | O1
//    X2 |  4   5   6  | O2
//    X3 |  7   8   9  | O3
//    X4 |             | O4
//    X5 |             | O5
//
// The engraved labels match the names in test_mycobot_squares.py, so
// calibrate "5" at the pocket labelled 5, "x1" at X1, and so on.
//
// robot.py uses the same layout for its starting positions. If you change
// pitch, staging_pitch, staging_gap or staging_count here, change the
// matching values in robot.py, and set GRID_NEAR_X there to the distance
// from the robot's base centre to the centre of the 0 1 2 row.

/* [What to show / export] */
PART = "both";          // "board", "blocks" or "both" (preview only)

/* [Block] */
block      = 15;        // block width (mm). Measure real blocks if not printing them.
block_h    = 15;        // block height
block_cham = 1.5;       // chamfer on the block's bottom edges, so it slides in

/* [Pockets] */
clearance  = 0.8;       // floor = block + this. 0.6-1.0 for FDM; less wedges, more rattles.
flare      = 3.5;       // extra opening width per side at the top = capture range
depth      = 5;         // pocket depth; keep well under block_h so the cup never touches

/* [Layout] */
pitch          = 25;    // centre-to-centre spacing of grid pockets
staging_pitch  = 25;    // spacing of staging pockets along each column
staging_gap    = 8;     // extra space between grid and staging columns
staging_count  = 5;     // pockets per player
margin         = 6;     // border around everything
thickness      = 7;     // board thickness (floor under pockets = thickness - depth)

/* [Labels] */
labels       = true;
label_size   = 5;       // text height on the pocket floor
label_depth  = 0.4;     // engraved depth; too deep and the block may rock

$fn = 48;

floor_w   = block + clearance;
opening_w = floor_w + 2 * flare;

// Board size. Grid sits at the robot end; staging columns run its full length.
grid_len  = 3 * pitch;
stage_len = staging_count * staging_pitch;
board_len = max(grid_len, stage_len) + 2 * margin;                    // robot -> player
board_w   = 3 * pitch + 2 * (staging_pitch + staging_gap) + 2 * margin; // left -> right

assert(opening_w < pitch - 2, "Pockets overlap: raise pitch or lower flare");
assert(opening_w < staging_pitch - 2, "Staging pockets overlap: raise staging_pitch or lower flare");
assert(depth < thickness - 1, "Pocket too deep for the board thickness");

echo(str("Board ", board_w, " x ", board_len, " mm. Floor ", floor_w,
         " mm, opening ", opening_w, " mm, capture range +/-", flare, " mm."));

// ---- Pocket: flat floor, walls sloping outward to the opening ----
module pocket(label = "") {
    translate([0, 0, thickness - depth]) {
        linear_extrude(height = depth + 0.01, scale = opening_w / floor_w)
            square(floor_w, center = true);
        if (labels && label != "")
            translate([0, 0, -label_depth])
                linear_extrude(height = label_depth + 0.01)
                    text(label, size = label_size, halign = "center", valign = "center",
                         font = "Liberation Sans:style=Bold");
    }
}

// Pocket centres. Origin = board corner at the player's left; +y towards the robot.
function grid_xy(i) = let(r = floor(i / 3), c = i % 3)
    [margin + staging_pitch + staging_gap + (c + 0.5) * pitch,
     board_len - margin - (r + 0.5) * pitch];

function staging_xy(side, i) =   // side 0 = X (left), 1 = O (right)
    [side == 0 ? margin + staging_pitch / 2 : board_w - margin - staging_pitch / 2,
     board_len - margin - (i + 0.5) * staging_pitch];

module board() {
    difference() {
        cube([board_w, board_len, thickness]);

        for (i = [0:8])
            translate(grid_xy(i)) pocket(str(i + 1));

        for (side = [0:1], i = [0:staging_count - 1])
            translate(staging_xy(side, i)) pocket(str(side == 0 ? "X" : "O", i + 1));

        // Arrow on the robot edge, so the board goes down the right way round.
        if (labels)
            translate([board_w / 2, board_len - margin / 2, thickness - label_depth])
                linear_extrude(height = label_depth + 0.01)
                    text("ROBOT", size = 3.5, halign = "center", valign = "center",
                         font = "Liberation Sans:style=Bold");
    }
}

// ---- Block: flat top for the suction cup, chamfered bottom edges ----
module block_piece() {
    hull() {
        translate([block_cham, block_cham, 0])
            cube([block - 2 * block_cham, block - 2 * block_cham, 0.01]);
        translate([0, 0, block_cham])
            cube([block, block, block_h - block_cham]);
    }
}

module blocks() {
    // 5 X + 5 O. Print each set in its own colour; keep the tops plain,
    // since a mark on top would spoil the suction seal.
    for (set = [0:1], i = [0:staging_count - 1])
        translate([i * (block + 5), set * (block + 5), 0]) block_piece();
}

if (PART == "board") board();
else if (PART == "blocks") blocks();
else {
    board();
    translate([0, -2 * (block + 5) - 10, 0]) color("orange") blocks();
}
