"""Tkinter window for the board. Plain functions, no classes.

Call build() once with the functions to run when a square or Reset is
clicked, then run() to show the window.
"""

import tkinter as tk

SYMBOLS = {0: "", 1: "X", 2: "O"}

root = None
buttons = []
status_label = None


def build(on_square, on_reset):
    global root, status_label

    root = tk.Tk()
    root.title("Tic-Tac-Toe")

    board_frame = tk.Frame(root)
    board_frame.pack(padx=20, pady=20)

    for square in range(9):
        button = tk.Button(
            board_frame,
            text="",
            width=8,
            height=4,
            font=("Arial", 20),
            command=lambda s=square: on_square(s),
        )

        row = square // 3
        column = square % 3
        button.grid(row=row, column=column, padx=3, pady=3)

        buttons.append(button)

    status_label = tk.Label(root, text="", font=("Arial", 12))
    status_label.pack(pady=(0, 10))

    reset_button = tk.Button(root, text="Reset", command=on_reset)
    reset_button.pack(pady=(0, 20))


def update_board(board):
    for square in range(9):
        buttons[square].config(text=SYMBOLS[board[square]])


def set_status(message):
    status_label.config(text=message)


def run():
    root.mainloop()