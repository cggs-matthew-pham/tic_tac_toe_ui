"""Robot side of tic-tac-toe: turns a square number into a real pick and place.

Works with either end effector. Pick one in main.py:

    robot = Robot(end_effector="suction")   # suction pump (default)
    robot = Robot(end_effector="gripper")   # adaptive gripper

The game and UI never need to know which one is fitted. Only grab() and
release() change; every movement is the same.

CALIBRATE BEFORE USE: STAGING positions and DOWN_Z below are placeholders.
Find real values the same way test_mycobot_squares.py checks the board.
"""

import time

from pymycobot import MyCobot280

PORT = "/dev/ttyAMA0"
BAUD = "1000000"
SPEED = 40

START_ANGLES = [25, 20, -120, 10, 0, -65]

HOVER_Z = 170  # safe travel height, same as the square test
DOWN_Z = 120   # PLACEHOLDER: height to grab/release a piece. The gripper and
               # suction cup are different lengths, so this needs checking
               # for whichever one is fitted.

# Board squares, numbered like the UI:
#   0 | 1 | 2
#   3 | 4 | 5
#   6 | 7 | 8
# Only x and y matter here; height is set by HOVER_Z or DOWN_Z.
SQUARES = [
    (175, 30), (145, 30), (115, 30),
    (175, 0),  (145, 0),  (115, 0),
    (175, -30), (145, -30), (115, -30),
]

# PLACEHOLDER staging spots, where pieces wait before being placed.
# X moves first, so it can need up to 5 pieces; O needs at most 4.
STAGING = {
    1: [(200, 90), (170, 90), (140, 90), (110, 90), (80, 90)],   # X pieces
    2: [(200, -90), (170, -90), (140, -90), (110, -90)],          # O pieces
}

TOOL_DOWN = [180, 0, 0]  # rx, ry, rz: tool pointing straight down


class Robot:
    def __init__(self, end_effector="suction"):
        if end_effector not in ("gripper", "suction"):
            raise ValueError("end_effector must be 'gripper' or 'suction'")

        self.end_effector = end_effector
        self.mc = MyCobot280(PORT, BAUD)
        self.used = {1: 0, 2: 0}  # staging pieces taken so far, per player

        if end_effector == "suction":
            self._setup_suction()

        self.release()

    # ---- end effector: the only part that differs ----

    def _setup_suction(self):
        # On the myCobot 280 Pi the pump is driven from the Pi's GPIO pins.
        # Pin numbers and on/off levels are from Elephant Robotics' examples;
        # check them against your pump before the first run.
        import RPi.GPIO as GPIO

        self.GPIO = GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(20, GPIO.OUT)  # pump
        GPIO.setup(21, GPIO.OUT)  # release valve

    def grab(self):
        if self.end_effector == "gripper":
            self.mc.set_gripper_state(1, 50)  # 1 = close
        else:
            self.GPIO.output(20, 0)           # pump on
        time.sleep(1)

    def release(self):
        if self.end_effector == "gripper":
            self.mc.set_gripper_state(0, 50)  # 0 = open
        else:
            self.GPIO.output(20, 1)           # pump off
            self.GPIO.output(21, 0)           # open valve to drop the piece
            time.sleep(0.5)
            self.GPIO.output(21, 1)
        time.sleep(1)

    # ---- movement: identical for both end effectors ----

    def move_to(self, x, y, z, mode=0):
        target = [x, y, z] + TOOL_DOWN
        solution = self.mc.solve_inv_kinematics(target, self.mc.get_angles())

        if not solution or len(solution) != 6:
            raise RuntimeError(f"Can't reach {target}")

        self.mc.send_coords(target, SPEED, mode)
        time.sleep(2)

    def home(self):
        self.mc.send_angles(START_ANGLES, SPEED)
        time.sleep(3)

    def pick_from(self, x, y):
        self.move_to(x, y, HOVER_Z)
        self.move_to(x, y, DOWN_Z, mode=1)  # mode 1: straight line down
        self.grab()
        self.move_to(x, y, HOVER_Z, mode=1)

    def drop_at(self, x, y):
        self.move_to(x, y, HOVER_Z)
        self.move_to(x, y, DOWN_Z, mode=1)
        self.release()
        self.move_to(x, y, HOVER_Z, mode=1)

    def place_piece(self, square, player):
        slot = self.used[player]
        if slot >= len(STAGING[player]):
            raise RuntimeError(f"No staged pieces left for player {player}")

        self.pick_from(*STAGING[player][slot])
        self.drop_at(*SQUARES[square])
        self.used[player] += 1

    def reset(self):
        # Pieces go back to staging by hand, so just restart the count.
        self.used = {1: 0, 2: 0}
        self.home()