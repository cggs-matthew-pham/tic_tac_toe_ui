"""Robot side of tic-tac-toe: turns a square number into a real pick and place.

Plain functions, no classes. Use it from other files with:

    import robot
    robot.home()
    robot.place_piece(square, player)

Choose the end effector with END_EFFECTOR below. Only grab() and release()
care which one is fitted; every movement is the same.

CALIBRATE BEFORE USE: STAGING positions and DOWN_Z below are placeholders.
Check them with test_mycobot_squares.py.
"""

import time

from pymycobot import MyCobot280

PORT = "/dev/ttyAMA0"
BAUD = "1000000"
SPEED = 40

END_EFFECTOR = "suction"  # "suction" or "gripper"

START_ANGLES = [25, 20, -120, 10, 0, -65]

HOVER_Z = 190  # safe travel height, about 40 above DOWN_Z
DOWN_Z = 175   # height where the cup just touches a piece (measure at a
               # NEAR square, then use SAG_PER_MM to fix the far ones)

# The arm droops slightly at full reach, so far positions end up lower than
# asked. Beyond SAG_START_X, raise z by SAG_PER_MM for every mm further out.
# Example: if x=240 sits 8 mm lower than x=160, use 8 / (240 - 160) = 0.1
SAG_START_X = 160
SAG_PER_MM = 0.0  # start at 0, measure, then set

# ---- Board squares ----
# Numbered like the UI:
#   0 | 1 | 2
#   3 | 4 | 5
#   6 | 7 | 8
# (x, y) in mm. x is distance out from the robot, y is left/right.
# Height is set by HOVER_Z or DOWN_Z.
SQUARES = [
    (240, 40), (200, 40), (160, 40),
    (240, 0),  (200, 0),  (160, 0),
    (240, -40), (200, -40), (160, -40),
]

# ---- Staging spots ----
# Where blocks wait before being placed. X moves first, so it needs 5; O needs 4.
STAGING = {
    1: [(270, 70), (240, 70), (210, 70), (180, 70), (150, 70)],   # X blocks
    2: [(270, -70), (240, -70), (210, -70), (180, -70)],         # O blocks
}

TOOL_DOWN = [180, 0, 0]  # rx, ry, rz: tool pointing straight down


# ---- Connection (runs once, when this file is imported) ----

mc = MyCobot280(PORT, BAUD)

if END_EFFECTOR == "suction":
    # On the myCobot 280 Pi the pump is driven from the Pi's GPIO pins.
    # Pin numbers and on/off levels are from Elephant Robotics' examples;
    # check them against your pump before the first run.
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(20, GPIO.OUT)  # pump
    GPIO.setup(21, GPIO.OUT)  # release valve

pieces_used = {1: 0, 2: 0}  # staging pieces taken so far, per player


# ---- End effector: the only part that differs ----

def grab():
    if END_EFFECTOR == "gripper":
        mc.set_gripper_state(1, 50)  # 1 = close
    else:
        GPIO.output(20, 0)           # pump on
    time.sleep(1)


def release():
    if END_EFFECTOR == "gripper":
        mc.set_gripper_state(0, 50)  # 0 = open
    else:
        GPIO.output(20, 1)           # pump off
        GPIO.output(21, 0)           # open valve to drop the piece
        time.sleep(0.5)
        GPIO.output(21, 1)
    time.sleep(1)


# ---- Movement: identical for both end effectors ----

def move_to(x, y, z, mode=0):
    z = z + max(0, x - SAG_START_X) * SAG_PER_MM  # droop correction
    target = [x, y, z] + TOOL_DOWN
    solution = mc.solve_inv_kinematics(target, mc.get_angles())

    if not solution or len(solution) != 6:
        raise RuntimeError(f"Can't reach {target}")

    mc.send_coords(target, SPEED, mode)
    time.sleep(2)


def home():
    mc.send_angles(START_ANGLES, SPEED)
    time.sleep(3)


def pick_from(x, y):
    move_to(x, y, HOVER_Z)
    move_to(x, y, DOWN_Z, mode=1)  # mode 1: straight line down
    grab()
    move_to(x, y, HOVER_Z, mode=1)


def drop_at(x, y):
    move_to(x, y, HOVER_Z)
    move_to(x, y, DOWN_Z, mode=1)
    release()
    move_to(x, y, HOVER_Z, mode=1)


# ---- Game-level actions ----

def place_piece(square, player):
    slot = pieces_used[player]
    if slot >= len(STAGING[player]):
        raise RuntimeError(f"No staged pieces left for player {player}")

    pick_from(*STAGING[player][slot])
    drop_at(*SQUARES[square])
    pieces_used[player] += 1


def reset():
    # Pieces go back to staging by hand, so just restart the count.
    pieces_used[1] = 0
    pieces_used[2] = 0
    release()
    home()
