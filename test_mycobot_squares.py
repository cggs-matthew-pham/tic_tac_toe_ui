"""Calibration checks for the tic-tac-toe robot.

Uses the same positions and movement code as the game (robot.py), so
anything you fix here is automatically what main.py uses.

Run on the Pi, no window needed (fine over SSH):

    python3 test_mycobot_squares.py
"""

import re
import time

import robot
from robot import SQUARES, STAGING, SQUARE_Z, STAGING_Z, HOVER_Z, BLOCK_HEIGHT


def ask(message):
    return input(message).strip().lower()


def find_spot(name):
    """Turn '4' into square 4, or 'x1' / 'o0' into a staging stack.

    Returns (label, key) where key is ("square", 4) or ("staging", 1, 0),
    or None if the name doesn't match anything.
    """
    if name.isdigit():
        index = int(name)
        if index < len(SQUARES):
            return f"square {index}", ("square", index)
        return None

    players = {"x": 1, "o": 2}
    if name[:1] in players and name[1:].isdigit():
        player = players[name[0]]
        index = int(name[1:])
        if index < len(STAGING[player]):
            return f"{name[0].upper()} stack {index}", ("staging", player, index)

    return None


def get_spot(key):
    """(x, y, table_z) currently stored for a spot."""
    if key[0] == "square":
        x, y = SQUARES[key[1]]
        return x, y, SQUARE_Z[key[1]]
    _, player, index = key
    x, y = STAGING[player][index]
    return x, y, STAGING_Z[player][index]


def set_spot(key, x, y, table_z):
    if key[0] == "square":
        SQUARES[key[1]] = (x, y)
        SQUARE_Z[key[1]] = table_z
    else:
        _, player, index = key
        STAGING[player][index] = (x, y)
        STAGING_Z[player][index] = table_z


def show_position(x, y, z):
    print(f"  Sent:     x={x:g}  y={y:g}  z={z:g}")
    coords = robot.read_coords()
    if coords:
        print("  Reported: x={:.1f}  y={:.1f}  z={:.1f}  rx={:.1f}  ry={:.1f}  rz={:.1f}".format(*coords))
    else:
        print("  Reported: (no answer from arm)")
    angles = robot.read_angles()
    if angles:
        print("  Angles:   " + "  ".join(f"J{i + 1}={a:.1f}" for i, a in enumerate(angles)))


def pump_command(command):
    """Handle 'pump', 'pump on', 'pump off'. Returns True if it was one."""
    if command not in ("pump", "pump on", "pump off"):
        return False
    if robot.END_EFFECTOR != "suction":
        print("  No pump fitted (END_EFFECTOR is the gripper).")
        return True
    if command == "pump":
        on = not robot.PUMP_ENABLED
    else:
        on = command == "pump on"
    robot.set_pump_enabled(on)
    print(f"  Pump {'ENABLED: grab will switch it on' if on else 'disabled: moves only, no suction'}.")
    return True


MAX_NUDGE = 10  # mm; stops a typo like x+40 swinging the arm across the board
NUDGE = re.compile(r"^([xyz])([+-])(\d+(?:\.\d+)?)?$")


def test_go_to():
    print("Squares:")
    print("  0 | 1 | 2")
    print("  3 | 4 | 5")
    print("  6 | 7 | 8")
    print(f"Staging: x0-x{len(STAGING[1]) - 1}, o0-o{len(STAGING[2]) - 1}")
    print("Then:")
    print("  d = down to the table, d2 = one block up, h = hover")
    print("  x+ x- y+ y- z+ z- = nudge 1 mm; add mm for more, up to 10 (x+4, z-0.5)")
    print("  teach = go limp, you hold the cup on the spot, Enter to read it")
    print("  pump / pump on / pump off = allow the suction pump (off by default)")
    print("  w = show where the arm is, save = keep this spot, q = back to menu")
    print("Save at d (cup just touching the table) to record height too;")
    print("save at h records only x and y.")

    key = None       # which spot we're working on
    x = y = z = None  # where the arm was last sent
    level = None     # "h", "d" or "d2"

    while True:
        command = ask("> ")

        if command == "q":
            if level in ("d", "d2"):
                robot.move_to(x, y, HOVER_Z, mode=1)
            return

        if pump_command(command):
            continue

        try:
            if command in ("d", "d2", "h"):
                if key is None:
                    print("Choose a square or staging stack first.")
                    continue
                table_z = get_spot(key)[2]
                z = {"d": table_z, "d2": table_z + BLOCK_HEIGHT, "h": HOVER_Z}[command]
                robot.move_to(x, y, z, mode=1)  # straight up or down
                level = command
                show_position(x, y, z)
                continue

            nudge = NUDGE.match(command)
            if nudge:
                if key is None:
                    print("Choose a square or staging stack first.")
                    continue
                axis, sign, amount = nudge.groups()
                step = float(amount or 1)
                if step > MAX_NUDGE:
                    print(f"  Max {MAX_NUDGE:g} mm per nudge; repeat it to go further.")
                    continue
                if sign == "-":
                    step = -step
                new = {"x": x, "y": y, "z": z}
                new[axis] += step
                # Small moves in a straight line so it can't swing into the board.
                robot.move_to(new["x"], new["y"], new["z"], mode=1)
                x, y, z = new["x"], new["y"], new["z"]
                show_position(x, y, z)
                continue

            if command == "teach":
                if key is None:
                    print("Choose a square or staging stack first.")
                    continue
                print("  Servos releasing - HOLD THE ARM, it will drop.")
                ask("  Enter to release: ")
                robot.mc.release_all_servos()
                ask("  Hold the cup on the centre of the spot, pointing down. Enter when there: ")
                robot.mc.power_on()
                time.sleep(1)
                coords = robot.read_coords()
                if coords is None:
                    print("  Couldn't read the arm's position. Try again.")
                    level = None
                    robot.last_target = None
                    continue
                tx, ty, tz = (round(c, 1) for c in coords[:3])
                print(f"  Taught: x={tx:g}  y={ty:g}  z={tz:g}")
                if tz < robot.MIN_Z:
                    print(f"  z is below MIN_Z ({robot.MIN_Z}); using {robot.MIN_Z}. "
                          "Lower DOWN_Z in robot.py if the table really is that low.")
                    tz = robot.MIN_Z
                # A limp arm sags and tilts, so drive there properly under power
                # (tool straight down) and check before saving.
                robot.last_target = None
                robot.move_to(tx, ty, tz, mode=1)
                x, y, z = tx, ty, tz
                level = "d"
                show_position(x, y, z)
                print("  Now nudge until the cup just touches dead centre, then save.")
                continue

            if command == "w":
                if key is None:
                    print("Choose a square or staging stack first.")
                    continue
                show_position(x, y, z)
                continue

            if command == "save":
                if key is None:
                    print("Choose a square or staging stack first.")
                    continue
                old_x, old_y, old_z = get_spot(key)
                if level == "d":
                    table_z = z
                elif level == "d2":
                    table_z = z - BLOCK_HEIGHT
                else:
                    table_z = old_z  # at hover: keep the old height
                set_spot(key, x, y, table_z)
                robot.save_calibration()
                print(f"  Saved: was ({old_x:g}, {old_y:g}, z={old_z:g}), "
                      f"now ({x:g}, {y:g}, z={table_z:g}) -> calibration.json")
                continue

            found = find_spot(command)
            if found is None:
                print("Unknown command. Try 4, x1, o0, d, h, x+2, w, save or q.")
                continue

            if level in ("d", "d2"):  # always lift before moving sideways
                robot.move_to(x, y, HOVER_Z, mode=1)

            label, key = found
            x, y, _ = get_spot(key)
            z = HOVER_Z
            level = "h"
            robot.move_to(x, y, z)
            print(f"Over {label}")
            show_position(x, y, z)

        except RuntimeError as error:
            print(error)
            print("  (Position unchanged.)")


def test_end_effector():
    if robot.END_EFFECTOR == "suction" and not robot.PUMP_ENABLED:
        print("The pump is disabled. Turn it on from the menu (p) first.")
        return
    print(f"Testing the {robot.END_EFFECTOR}. Hold a piece against it.")
    ask("Enter to grab: ")
    robot.grab()
    ask("Did it grab? Enter to release: ")
    robot.release()
    print("Done.")


def test_pick_and_place():
    names = {"x": 1, "o": 2}

    player = names.get(ask("Pick an X or an O block? (x/o): "))
    if player is None:
        print("Type x or o.")
        return

    stacks = STAGING[player]
    try:
        stack = int(ask(f"Which staging stack? (0-{len(stacks) - 1}): "))
        layer = int(ask("Which block? (1 = bottom, 2 = top of a stack): ")) - 1
        square = int(ask(f"Which square to place it on? (0-{len(SQUARES) - 1}): "))
        stacks[stack], SQUARES[square]  # check both numbers exist
        if layer not in (0, 1):
            raise ValueError
    except (ValueError, IndexError):
        print("That stack, block or square doesn't exist.")
        return

    try:
        robot.pick_from(*stacks[stack], layer, STAGING_Z[player][stack])
        robot.drop_at(*SQUARES[square], SQUARE_Z[square])
    except RuntimeError as error:
        print(error)
        robot.release()  # don't keep holding a block after a failed move
        return

    print("Done. Did the block land in the middle of the square?")


def main():
    print("Moving to safe start position...")
    robot.home()

    tests = {
        "1": ("Go to a square or staging spot (hover/down)", test_go_to),
        "2": ("Grab and release", test_end_effector),
        "3": ("Pick and place (staging slot to square)", test_pick_and_place),
    }

    while True:
        print()
        for key, (name, _) in tests.items():
            print(f"{key}. {name}")
        if robot.END_EFFECTOR == "suction":
            state = "ON" if robot.PUMP_ENABLED else "off"
            print(f"p. Toggle suction pump (currently {state})")
        choice = ask("Choose a test, or q to quit: ")

        if choice == "q":
            robot.set_pump_enabled(False)
            robot.home()
            return
        if choice == "p":
            pump_command("pump")
            continue
        if choice in tests:
            tests[choice][1]()


if __name__ == "__main__":
    main()