import game
import ui
import robot


def player_name(player):
    if player == game.X:
        return "X"
    return "O"


def square_clicked(square):
    if not game.make_move(square):
        ui.set_status("That square is already occupied.")
        return

    robot.place_piece(square, game.current_player)

    ui.update_board(game.board)

    winner = game.check_winner()

    if winner != game.EMPTY:
        ui.set_status(f"{player_name(winner)} wins!")
        return

    if game.is_full():
        ui.set_status("Draw!")
        return

    game.next_player()
    ui.set_status(f"{player_name(game.current_player)} to move")


def reset_game():
    game.reset()
    robot.reset()
    ui.update_board(game.board)
    ui.set_status("X to move")


ui.build(on_square=square_clicked, on_reset=reset_game)

reset_game()
ui.run()