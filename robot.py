"""Robot side of tic-tac-toe: turns a square number into a real pick and place.

Plain functions, no classes. Use it from other files with:

    import robot
    robot.home()
    robot.place_piece(square, player)

Choose the end effector with END_EFFECTOR below. Only grab() and release()
care which one is fitted; every movement is the same.

CALIBRATE BEFORE USE: STAGING positions and DOWN_Z below are placeholders.
Check them with test_mycobot_squares.py, which can nudge the arm into the
right spot and save it to calibration.json. If that file exists it
overrides the defaults below, per square and per staging stack.
"""

import json
import os
import time

from pymycobot import MyCobot280

CALIBRATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.json")

PORT = "/dev/ttyAMA0"
BAUD = "1000000"
SPEED = 40

END_EFFECTOR = "suction"  # "suction" or "gripper"

# False = the arm still moves through every pick and place, but the pump
# never switches on (quiet, for calibrating). Toggle while testing with
# 'pump' in test_mycobot_squares.py. Set True to actually pick up blocks.
PUMP_ENABLED = False

START_ANGLES = [25, 20, -120, 10, 0, -65]

HOVER_Z = 190  # safe travel height; clears a 2-high stack of thin blocks
DOWN_Z = 175   # height where the cup just touches a block sitting on the table
BLOCK_HEIGHT = 5  # mm; a stacked block is grabbed this much higher

# Safety: move_to refuses anything below this, so a wrong number can't
# drive the cup into the board. Low enough to leave room for nudging
# while calibrating; raise it once DOWN_Z is known.
MIN_Z = DOWN_Z - 15

# The arm droops slightly at full reach, so far positions end up lower than
# asked. Beyond SAG_START_X, raise z by SAG_PER_MM for every mm further out.
# Example: if x=240 sits 8 mm lower than x=160, use 8 / (240 - 160) = 0.1
# Not needed if you calibrate each square's z with test_mycobot_squares.py;
# leave it at 0 then, or the saved z values will be off by the correction.
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
# One (x, y) per stack of blocks, nearest-to-use first.
STAGING = {
    1: [(240, 70), (210, 70), (180, 70)],   # X stacks
    2: [(240, -70), (210, -70)],            # O stacks
}

# How many blocks start in each stack above. X: 2 + 2 + 1 = 5, O: 2 + 2 = 4.
# This is the only place stacking is described.
STACK_SIZES = {
    1: [2, 2, 1],
    2: [2, 2],
}

# Table height at each spot. One number per square and per staging stack,
# starting as DOWN_Z everywhere. Measured values from calibration.json
# replace these, which handles sag and an unlevel board without modelling it.
SQUARE_Z = [DOWN_Z] * 9
STAGING_Z = {player: [DOWN_Z] * len(stacks) for player, stacks in STAGING.items()}

TOOL_DOWN = [180, 0, 0]  # rx, ry, rz: tool pointing straight down


# ---- Calibration file ----
# {"squares": {"4": [x, y, z]}, "staging": {"x1": [x, y, z], "o0": [x, y, z]}}
# Only spots present in the file are overridden.

PLAYER_LETTER = {1: "x", 2: "o"}


def load_calibration():
    if not os.path.exists(CALIBRATION_FILE):
        return
    with open(CALIBRATION_FILE) as f:
        data = json.load(f)

    for key, (x, y, z) in data.get("squares", {}).items():
        SQUARES[int(key)] = (x, y)
        SQUARE_Z[int(key)] = z

    for key, (x, y, z) in data.get("staging", {}).items():
        player = {"x": 1, "o": 2}[key[0]]
        stack = int(key[1:])
        STAGING[player][stack] = (x, y)
        STAGING_Z[player][stack] = z


def save_calibration():
    data = {
        "squares": {str(i): [*SQUARES[i], SQUARE_Z[i]] for i in range(9)},
        "staging": {
            f"{PLAYER_LETTER[player]}{i}": [*STAGING[player][i], STAGING_Z[player][i]]
            for player in STAGING
            for i in range(len(STAGING[player]))
        },
    }
    with open(CALIBRATION_FILE, "w") as f:
        json.dump(data, f, indent=2)


load_calibration()


# ---- Connection (runs once, when this file is imported) ----

mc = MyCobot280(PORT, BAUD)

if END_EFFECTOR == "suction":
    # On the myCobot 280 Pi the pump is driven from the Pi's GPIO pins.
    # Pin numbers and on/off levels are from Elephant Robotics' examples;
    # check them against your pump before the first run.
    import RPi.GPIO as GPIO

    GPIO.setmode(GPIO.BCM)
    # initial=HIGH: an output pin starts LOW otherwise, which here means
    # pump running from the moment this file is imported.
    GPIO.setup(20, GPIO.OUT, initial=GPIO.HIGH)  # pump (LOW = on)
    GPIO.setup(21, GPIO.OUT, initial=GPIO.HIGH)  # release valve (LOW = open)

# Blocks left in each stack; refilled by reset().
blocks_left = {player: list(sizes) for player, sizes in STACK_SIZES.items()}


# ---- End effector: the only part that differs ----

def grab():
    if END_EFFECTOR == "gripper":
        mc.set_gripper_state(1, 50)  # 1 = close
    elif PUMP_ENABLED:
        GPIO.output(20, 0)           # pump on
    else:
        print("(pump disabled: skipping grab)")
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


def set_pump_enabled(on):
    """Allow or block the pump. Turning it off also stops it if running."""
    global PUMP_ENABLED
    PUMP_ENABLED = on
    if END_EFFECTOR == "suction" and not on:
        GPIO.output(20, 1)  # pump off


# ---- Talking to the arm ----
# Questions sent to the arm over the serial cable sometimes get no answer
# (None, -1 or []), especially while it is still moving. So: wait for each
# move to finish, remember what we already know, and retry only as a backup.

last_target = None   # where we last sent the arm
last_angles = None   # last good joint-angle reading


def wait_until_stopped(timeout=10):
    time.sleep(0.3)  # give the move time to start
    start = time.time()
    while time.time() - start < timeout:
        if mc.is_moving() == 0:  # 1 = moving, 0 = stopped, -1 = no answer
            return
        time.sleep(0.1)
    print("Warning: arm didn't report stopping; carrying on.")


def read_angles():
    global last_angles
    for _ in range(3):
        angles = mc.get_angles()
        if isinstance(angles, list) and len(angles) == 6:
            last_angles = angles
            return angles
        time.sleep(0.2)
    return last_angles  # fall back to the last good reading


def read_coords():
    """Where the arm says it is: [x, y, z, rx, ry, rz], or None if no answer."""
    for _ in range(3):
        coords = mc.get_coords()
        if isinstance(coords, list) and len(coords) == 6:
            return coords
        time.sleep(0.2)
    return None


def can_reach(target):
    angles = read_angles()
    if angles is None:
        raise RuntimeError("Couldn't read the arm's joint angles. Check the connection.")

    for _ in range(3):
        solution = mc.solve_inv_kinematics(target, angles)
        if isinstance(solution, list) and len(solution) == 6:
            return True
        time.sleep(0.2)
    return False


# ---- Movement: identical for both end effectors ----

def move_to(x, y, z, mode=0):
    global last_target

    if z < MIN_Z:
        raise RuntimeError(f"Refusing to move to z={z}: below MIN_Z ({MIN_Z})")
    if mode not in (0, 1):
        raise RuntimeError(f"mode must be 0 or 1, got {mode}")

    z = z + max(0, x - SAG_START_X) * SAG_PER_MM  # droop correction
    target = [x, y, z] + TOOL_DOWN

    if target == last_target:
        return  # already there

    if not can_reach(target):
        raise RuntimeError(f"Can't reach {target}")

    mc.send_coords(target, SPEED, mode)
    wait_until_stopped()
    last_target = target


def home():
    global last_target, last_angles
    mc.send_angles(START_ANGLES, SPEED)
    wait_until_stopped()
    last_target = None
    last_angles = list(START_ANGLES)  # a known-good reading to start from


def pick_from(x, y, layer=0, table_z=DOWN_Z):
    grab_z = table_z + layer * BLOCK_HEIGHT  # higher for a stacked block
    move_to(x, y, HOVER_Z)
    move_to(x, y, grab_z, mode=1)  # mode 1: straight line down
    grab()
    move_to(x, y, HOVER_Z, mode=1)


def drop_at(x, y, table_z=DOWN_Z):
    move_to(x, y, HOVER_Z)
    move_to(x, y, table_z, mode=1)
    release()
    move_to(x, y, HOVER_Z, mode=1)


# ---- Game-level actions ----

def place_piece(square, player):
    stacks = blocks_left[player]

    for stack, count in enumerate(stacks):
        if count > 0:
            layer = count - 1  # top block of this stack (0 = on the table)
            pick_from(*STAGING[player][stack], layer, STAGING_Z[player][stack])
            drop_at(*SQUARES[square], SQUARE_Z[square])
            stacks[stack] -= 1
            return

    raise RuntimeError(f"No staged blocks left for player {player}")


def reset():
    # Pieces go back to staging by hand, so just restart the count.
    for player, sizes in STACK_SIZES.items():
        blocks_left[player] = list(sizes)
    release()
    home()