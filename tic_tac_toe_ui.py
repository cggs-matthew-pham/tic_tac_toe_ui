import tkinter as tk


class TicTacToeUI:
    def __init__(self, on_square):
        self.on_square = on_square

        self.root = tk.Tk()
        self.root.title("Tic-Tac-Toe")

        self.buttons = []

        board_frame = tk.Frame(self.root)
        board_frame.pack(padx=20, pady=20)

        for square in range(9):
            button = tk.Button(
                board_frame,
                text="",
                width=8,
                height=4,
                font=("Arial", 20),
                command=lambda s=square: self.on_square(s),
            )

            row = square // 3
            column = square % 3
            button.grid(row=row, column=column, padx=3, pady=3)

            self.buttons.append(button)

        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 12),
        )
        self.status_label.pack(pady=(0, 10))

        self.reset_button = tk.Button(
            self.root,
            text="Reset",
            command=self._request_reset,
        )
        self.reset_button.pack(pady=(0, 20))

        self.on_reset = None

    def _request_reset(self):
        if self.on_reset is not None:
            self.on_reset()

    def update_board(self, board):
        symbols = {
            0: "",
            1: "X",
            2: "O",
        }

        for square in range(9):
            self.buttons[square].config(text=symbols[board[square]])

    def set_status(self, message):
        self.status_label.config(text=message)

    def run(self):
        self.root.mainloop()
