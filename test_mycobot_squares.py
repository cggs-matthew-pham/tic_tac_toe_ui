"""Calibration checks for the tic-tac-toe robot.

Uses the same positions and movement code as the game (robot.py), so
anything you fix here is automatically what main.py uses.

Run on the Pi, no window needed (fine over SSH):

    python3 test_mycobot_squares.py
"""

from robot import Robot, SQUARES, STAGING, HOVER_Z, DOWN_Z


def ask(message):
    return input(message).strip().lower()


def test_squares(robot):
    print("Square numbering:")
    print("0 | 1 | 2")
    print("--+---+--")
    print("3 | 4 | 5")
    print("--+---+--")
    print("6 | 7 | 8")
    print()

    for square in range(9):
        if ask(f"Enter to hover over square {square}, q to stop: ") == "q":
            return

        x, y = SQUARES[square]
        try:
            robot.move_to(x, y, HOVER_Z)
        except RuntimeError as error:
            print(error)
            return

        if ask(f"Is square {square} correctly aligned? (y/n): ") != "y":
            print(f"Fix SQUARES[{square}] in robot.py (currently {SQUARES[square]})")
            return

    print("All 9 squares checked.")


def test_staging(robot):
    names = {1: "X", 2: "O"}

    for player, spots in STAGING.items():
        for slot, (x, y) in enumerate(spots):
            label = f"{names[player]} slot {slot}"
            if ask(f"Enter to check {label}, q to stop: ") == "q":
                return

            try:
                robot.move_to(x, y, HOVER_Z)
                robot.move_to(x, y, DOWN_Z, mode=1)  # down to grab height
            except RuntimeError as error:
                print(error)
                return

            answer = ask(f"Is the cup just touching the {label} piece? (y/n): ")
            robot.move_to(x, y, HOVER_Z, mode=1)

            if answer != "y":
                print(f"Fix STAGING[{player}][{slot}] or DOWN_Z in robot.py")
                print(f"Currently {(x, y)}, DOWN_Z = {DOWN_Z}")
                return

    print("All staging spots checked.")


def test_end_effector(robot):
    print(f"Testing the {robot.end_effector}. Hold a piece against it.")
    ask("Enter to grab: ")
    robot.grab()
    ask("Did it grab? Enter to release: ")
    robot.release()
    print("Done.")


def main():
    robot = Robot()  # same end effector default as the game
    print("Moving to safe start position...")
    robot.home()

    tests = {
        "1": ("Squares (hover check)", test_squares),
        "2": ("Staging spots (grab height check)", test_staging),
        "3": ("Grab and release", test_end_effector),
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
            tests[choice][1](robot)


if __name__ == "__main__":
    main()