"""Tic-tac-toe: two player or against the computer, with or without the robot.

Every move shows on screen first, then (if the robot is on) the arm places
the piece. Moves can be clicked or typed (see moves.py).

Settings in the window apply when you press New game. The suction pump
checkbox applies immediately.
"""

import game
import moves
import ui

# The robot connects to the arm as soon as it's imported, so try it here:
# on a laptop with no arm, the game still runs on screen.
try:
    import robot
except Exception as error:  # no pymycobot, no serial port, no GPIO...
    robot = None
    print(f"Robot not available, playing on screen only: {error}")

COMPUTER_LEVELS = {1: "easy", 2: "hard"}

robot_active = False   # set on New game from the checkbox
computer = None        # game.X, game.O, or None for two player
level = None
game_over = False
busy = False


def player_name(player):
    if player == game.X:
        return "X"
    return "O"


def turn_message():
    name = player_name(game.current_player)
    if computer is None:
        return f"{name} to move"
    if game.current_player == computer:
        return f"Computer ({name}) thinking..."
    return f"Your move ({name})"


def set_busy(value):
    global busy
    busy = value
    ui.set_busy(value)


def play(square):
    """Make a move for whoever's turn it is. Returns True if it happened."""
    global game_over

    if not game.make_move(square):
        ui.set_status(f"Square {square + 1} is already taken.")
        return False

    ui.update_board(game.board)  # on screen first, so you see what's coming

    if robot_active:
        ui.set_status(f"Robot placing {player_name(game.current_player)} on {square + 1}...")
        set_busy(True)
        ui.refresh()
        try:
            robot.place_piece(square, game.current_player)
        except Exception as error:
            game.board[square] = game.EMPTY  # undo: the piece never got placed
            ui.update_board(game.board)
            ui.set_status(f"Robot problem: {error}")
            print(error)
            set_busy(False)
            return False
        set_busy(False)

    winner = game.check_winner()
    if winner != game.EMPTY:
        game_over = True
        if computer is None:
            ui.set_status(f"{player_name(winner)} wins!")
        elif winner == computer:
            ui.set_status("Computer wins!")
        else:
            ui.set_status("You win!")
        return True

    if game.is_full():
        game_over = True
        ui.set_status("Draw!")
        return True

    game.next_player()
    ui.set_status(turn_message())
    return True


def computer_turn():
    if game_over or game.current_player != computer:
        return
    set_busy(True)
    square = game.computer_move(computer, level)
    set_busy(False)
    if not play(square):
        ui.set_status(ui.status_label.cget("text") + " Press New game to restart.")


def human_move(square):
    if busy or game_over:
        return
    if game.current_player == computer:
        ui.set_status("Wait for the computer's move.")
        return
    if play(square) and not game_over and computer is not None:
        set_busy(True)
        ui.later(400, computer_turn)  # short pause so the move reads as a reply


def square_clicked(square):
    human_move(square)


def move_typed(text):
    square = moves.parse_move(text)
    if square is None:
        ui.set_status(f'Didn\'t understand "{text}". Try 1-9 or "top left".')
        return
    human_move(square)


def pump_toggled(on):
    if robot is not None:
        robot.set_pump_enabled(on)


def new_game():
    global robot_active, computer, level, game_over

    game.reset()
    game_over = False

    mode = ui.get_mode()
    if mode == 0:
        computer = None
        level = None
    else:
        level = COMPUTER_LEVELS[mode]
        computer = game.X if ui.computer_first() else game.O

    robot_active = robot is not None and ui.robot_on()
    ui.update_board(game.board)

    if robot_active:
        ui.set_status("Robot going home... put the pieces back in staging.")
        set_busy(True)
        ui.refresh()
        try:
            robot.reset()
        except Exception as error:
            robot_active = False
            ui.set_status(f"Robot problem, playing on screen: {error}")
            print(error)
            set_busy(False)
            return
        set_busy(False)

    ui.set_status(turn_message())
    if computer == game.X:
        set_busy(True)
        ui.later(400, computer_turn)


ui.build(
    on_square=square_clicked,
    on_text=move_typed,
    on_reset=new_game,
    on_pump=pump_toggled,
    robot_available=robot is not None,
    pump_on=robot is not None and robot.PUMP_ENABLED,
)

new_game()
ui.run()
