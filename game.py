"""Tic-tac-toe rules. Plain functions, no classes.

Another game (Connect 4, chess) can be its own file with the same function
names, so main.py only needs a different import.
"""

import random

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


def winner_of(squares):
    for a, b, c in WINNING_LINES:
        if squares[a] != EMPTY and squares[a] == squares[b] == squares[c]:
            return squares[a]

    return EMPTY


def check_winner():
    return winner_of(board)


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


# ---- Computer player ----

def other(player):
    if player == X:
        return O
    return X


def empty_squares(squares):
    return [s for s in range(9) if squares[s] == EMPTY]


def minimax(squares, to_move, me):
    """Score this position for `me`, assuming both sides play perfectly.

    +10 is a win for me, -10 a loss, 0 a draw. Each move made subtracts 1,
    so a quicker win (or a slower loss) scores better.
    """
    winner = winner_of(squares)
    if winner == me:
        return 10
    if winner != EMPTY:
        return -10
    moves = empty_squares(squares)
    if not moves:
        return 0

    scores = []
    for square in moves:
        squares[square] = to_move
        scores.append(minimax(squares, other(to_move), me))
        squares[square] = EMPTY  # undo, so the board is unchanged afterwards

    if to_move == me:
        return max(scores) - 1
    return min(scores) + 1


def best_move(player):
    """Hard: the best square for `player`. Never loses."""
    squares = list(board)
    scored = []
    for square in empty_squares(squares):
        squares[square] = player
        scored.append((minimax(squares, other(player), player), square))
        squares[square] = EMPTY

    top = max(score for score, _ in scored)
    # Several squares can be equally good; pick one at random for variety.
    return random.choice([square for score, square in scored if score == top])


def easy_move(player):
    """Easy: takes a win if one is there, otherwise plays anywhere."""
    squares = list(board)
    for square in empty_squares(squares):
        squares[square] = player
        if winner_of(squares) == player:
            return square
        squares[square] = EMPTY
    return random.choice(empty_squares(board))


def computer_move(player, level):
    if level == "hard":
        return best_move(player)
    return easy_move(player)
