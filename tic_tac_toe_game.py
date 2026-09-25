class TicTacToeGame:
    EMPTY = 0
    X = 1
    O = 2

    def __init__(self):
        self.board = [self.EMPTY] * 9
        self.current_player = self.X

    def is_valid_move(self, square):
        return 0 <= square < 9 and self.board[square] == self.EMPTY

    def make_move(self, square):
        if not self.is_valid_move(square):
            return False

        self.board[square] = self.current_player
        return True

    def check_winner(self):
        winning_lines = [
            (0, 1, 2),
            (3, 4, 5),
            (6, 7, 8),
            (0, 3, 6),
            (1, 4, 7),
            (2, 5, 8),
            (0, 4, 8),
            (2, 4, 6),
        ]

        for a, b, c in winning_lines:
            if (
                self.board[a] != self.EMPTY
                and self.board[a] == self.board[b] == self.board[c]
            ):
                return self.board[a]

        return self.EMPTY

    def is_full(self):
        return self.EMPTY not in self.board

    def next_player(self):
        if self.current_player == self.X:
            self.current_player = self.O
        else:
            self.current_player = self.X

    def reset(self):
        self.board = [self.EMPTY] * 9
        self.current_player = self.X
