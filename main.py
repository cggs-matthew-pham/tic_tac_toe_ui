from tic_tac_toe_game import TicTacToeGame
from tic_tac_toe_ui import TicTacToeUI


game = TicTacToeGame()


def player_name(player):
    if player == TicTacToeGame.X:
        return "X"
    return "O"


def square_clicked(square):
    if not game.make_move(square):
        ui.set_status("That square is already occupied.")
        return

    # Later, this is the obvious robot-arm integration point:
    #
    # robot.place_piece(square, game.current_player)

    ui.update_board(game.board)

    winner = game.check_winner()

    if winner != TicTacToeGame.EMPTY:
        ui.set_status(f"{player_name(winner)} wins!")
        return

    if game.is_full():
        ui.set_status("Draw!")
        return

    game.next_player()
    ui.set_status(f"{player_name(game.current_player)} to move")


def reset_game():
    game.reset()
    ui.update_board(game.board)
    ui.set_status("X to move")


ui = TicTacToeUI(on_square=square_clicked)
ui.on_reset = reset_game

reset_game()
ui.run()
