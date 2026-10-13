"""Calibration checks for the tic-tac-toe robot.

Uses the same positions and movement code as the game (robot.py), so
anything you fix here is automatically what main.py uses.

Run on the Pi, no window needed (fine over SSH):

    python3 test_mycobot_squares.py
"""

import robot
from robot import SQUARES, STAGING, HOVER_Z, DOWN_Z


def ask(message):
    return input(message).strip().lower()


def find_spot(name):
    """Turn '4' into square 4, or 'x2' / 'o0' into a staging slot."""
    if name.isdigit():
        index = int(name)
        if index < len(SQUARES):
            return f"square {index}", SQUARES[index]
        return None

    players = {"x": 1, "o": 2}
    if name[:1] in players and name[1:].isdigit():
        slots = STAGING[players[name[0]]]
        index = int(name[1:])
        if index < len(slots):
            return f"{name[0].upper()} slot {index}", slots[index]

    return None


def test_go_to():
    print("Squares:")
    print("  0 | 1 | 2")
    print("  3 | 4 | 5")
    print("  6 | 7 | 8")
    print(f"Staging: x0-x{len(STAGING[1]) - 1}, o0-o{len(STAGING[2]) - 1}")
    print("Then: d = down, h = hover, q = back to menu")

    spot = None    # (x, y) the arm is currently over
    down = False

    while True:
        command = ask("> ")

        if command == "q":
            if down:
                robot.move_to(*spot, HOVER_Z, mode=1)
            return

        try:
            if command in ("d", "h"):
                if spot is None:
                    print("Choose a square or staging slot first.")
                    continue
                height = DOWN_Z if command == "d" else HOVER_Z
                robot.move_to(*spot, height, mode=1)  # straight up or down
                down = command == "d"
                print(f"At {spot}, z = {height}")
                continue

            found = find_spot(command)
            if found is None:
                print("Unknown spot. Try 4, x2 or o0.")
                continue

            if down:  # always lift before moving sideways
                robot.move_to(*spot, HOVER_Z, mode=1)
                down = False

            label, spot = found
            robot.move_to(*spot, HOVER_Z)
            print(f"Over {label} at {spot}, z = {HOVER_Z}")

        except RuntimeError as error:
            print(error)


def test_end_effector():
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

    slots = STAGING[player]
    try:
        slot = int(ask(f"Which staging slot? (0-{len(slots) - 1}): "))
        square = int(ask(f"Which square to place it on? (0-{len(SQUARES) - 1}): "))
        slots[slot], SQUARES[square]  # check both numbers exist
    except (ValueError, IndexError):
        print("That slot or square doesn't exist.")
        return

    try:
        robot.pick_from(*slots[slot])
        robot.drop_at(*SQUARES[square])
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
        choice = ask("Choose a test, or q to quit: ")

        if choice == "q":
            robot.home()
            return
        if choice in tests:
            tests[choice][1]()


if __name__ == "__main__":
    main()