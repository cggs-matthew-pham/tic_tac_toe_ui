"""Tic-tac-toe rules. Plain functions, no classes.

Another game (Connect 4, chess) can be its own file with the same function
names, so main.py only needs a different import.
"""

EMPTY = 0
X = 1
O = 2

WINNING_LINES = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]

board = [EMPTY] * 9
current_player = X


def is_valid_move(square):
    return 0 <= square < 9 and board[square] == EMPTY


def make_move(square):
    if not is_valid_move(square):
        return False

    board[square] = current_player
    return True


def check_winner():
    for a, b, c in WINNING_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]

    return EMPTY


def is_full():
    return EMPTY not in board


def next_player():
    global current_player

    if current_player == X:
        current_player = O
    else:
        current_player = X


def reset():
    global current_player

    for square in range(9):
        board[square] = EMPTY
    current_player = X