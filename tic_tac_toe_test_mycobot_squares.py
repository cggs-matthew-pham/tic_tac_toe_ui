from pymycobot import MyCobot280
import time

start_angles = [25, 20, -120, 10, 0, -65]

# Existing 3x3 tic-tac-toe grid coordinates.
coords_list = [
    [175, 30, 170, 180, 0, 0],
    [145, 30, 170, 180, 0, 0],
    [115, 30, 170, 180, 0, 0],
    [175, 0, 170, 180, 0, 0],
    [145, 0, 170, 180, 0, 0],
    [115, 0, 170, 180, 0, 0],
    [175, -30, 170, 180, 0, 0],
    [145, -30, 170, 180, 0, 0],
    [115, -30, 170, 180, 0, 0],
]

mc = MyCobot280("/dev/ttyAMA0", "1000000")


def check_and_move(target, mode=0):
    solution = mc.solve_inv_kinematics(target, mc.get_angles())

    if solution and len(solution) == 6:
        print(f"Moving to: {target}")
        mc.send_coords(target, 40, mode)
        time.sleep(2)
        return True

    print(f"Invalid target: {target}")
    return False


def move_to_grid(index):
    target = coords_list[index]
    return check_and_move(target)


def test_all_squares():
    print("Tic-Tac-Toe physical grid test")
    print()
    print("Square numbering:")
    print("0 | 1 | 2")
    print("--+---+--")
    print("3 | 4 | 5")
    print("--+---+--")
    print("6 | 7 | 8")
    print()

    for square in range(9):
        command = input(
            f"Press Enter to move to square {square}, or type q to quit: "
        ).strip().lower()

        if command == "q":
            print("Test stopped.")
            return

        if not move_to_grid(square):
            print(f"Could not move to square {square}.")
            return

        result = input(
            f"Is square {square} correctly aligned? (y/n/q): "
        ).strip().lower()

        if result == "q":
            print("Test stopped.")
            return

        if result != "y":
            print()
            print(f"Check calibration for square {square}.")
            print(f"Current target: {coords_list[square]}")
            return

    print()
    print("All 9 squares manually verified.")


if __name__ == "__main__":
    print("Moving to safe start position...")
    mc.send_angles(start_angles, 40)
    time.sleep(3)

    test_all_squares()
