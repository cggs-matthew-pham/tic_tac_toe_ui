"""Tkinter window for the board. Plain functions, no classes.

Call build() once with the functions to run on each action, then run().
Players can click a square or type a move (see moves.py) and press Enter.
"""

import tkinter as tk

SYMBOLS = {1: "X", 2: "O"}

MODES = ["Two player", "vs Computer (easy)", "vs Computer (hard)"]

root = None
buttons = []
status_label = None
move_entry = None
move_button = None
mode_var = None
computer_first_var = None
robot_var = None
pump_var = None
pump_check = None


def build(on_square, on_text, on_reset, on_pump, robot_available, pump_on):
    global root, status_label, move_entry, move_button
    global mode_var, computer_first_var, robot_var, pump_var, pump_check

    root = tk.Tk()
    root.title("Tic-Tac-Toe")

    # ---- Board ----
    board_frame = tk.Frame(root)
    board_frame.pack(padx=20, pady=(20, 10))

    for square in range(9):
        button = tk.Button(
            board_frame,
            text="",
            width=6,
            height=3,
            font=("Arial", 24),
            command=lambda s=square: on_square(s),
        )
        button.grid(row=square // 3, column=square % 3, padx=3, pady=3)
        buttons.append(button)

    status_label = tk.Label(root, text="", font=("Arial", 14))
    status_label.pack(pady=(0, 10))

    # ---- Typed move ----
    move_frame = tk.Frame(root)
    move_frame.pack(pady=(0, 10))
    tk.Label(move_frame, text="Your move:", font=("Arial", 12)).pack(side=tk.LEFT)

    move_entry = tk.Entry(move_frame, width=14, font=("Arial", 14))
    move_entry.pack(side=tk.LEFT, padx=5)

    def submit(_event=None):
        text = move_entry.get()
        move_entry.delete(0, tk.END)
        if text.strip():
            on_text(text)

    move_entry.bind("<Return>", submit)
    move_button = tk.Button(move_frame, text="Move", command=submit)
    move_button.pack(side=tk.LEFT)

    tk.Label(root, text='Type 1-9, or e.g. "centre", "top left"', fg="grey").pack()

    # ---- Game settings: take effect on New game ----
    settings = tk.LabelFrame(root, text="New game settings", padx=10, pady=5)
    settings.pack(padx=20, pady=10, fill=tk.X)

    mode_var = tk.StringVar(value=MODES[0])
    tk.OptionMenu(settings, mode_var, *MODES).pack(anchor=tk.W)

    computer_first_var = tk.BooleanVar(value=False)
    tk.Checkbutton(settings, text="Computer goes first (plays X)",
                   variable=computer_first_var).pack(anchor=tk.W)

    robot_var = tk.BooleanVar(value=robot_available)
    robot_text = "Robot arm" if robot_available else "Robot arm (not connected)"
    robot_check = tk.Checkbutton(settings, text=robot_text, variable=robot_var)
    robot_check.pack(anchor=tk.W)
    if not robot_available:
        robot_check.config(state=tk.DISABLED)

    tk.Button(settings, text="New game", command=on_reset).pack(pady=(5, 0))

    # ---- Pump: takes effect immediately ----
    pump_var = tk.BooleanVar(value=pump_on)
    pump_check = tk.Checkbutton(root, text="Suction pump on",
                                variable=pump_var, command=lambda: on_pump(pump_var.get()))
    pump_check.pack(pady=(0, 15))
    if not robot_available:
        pump_check.config(state=tk.DISABLED)

    move_entry.focus_set()


def update_board(board):
    for square in range(9):
        if board[square] in SYMBOLS:
            buttons[square].config(text=SYMBOLS[board[square]], fg="black")
        else:
            # Empty squares show their number, for typing or saying it.
            buttons[square].config(text=str(square + 1), fg="#bbbbbb")


def set_status(message):
    status_label.config(text=message)


def set_busy(busy):
    """Block input while the computer or the robot is moving."""
    state = tk.DISABLED if busy else tk.NORMAL
    for button in buttons:
        button.config(state=state)
    move_entry.config(state=state)
    move_button.config(state=state)
    if not busy:
        move_entry.focus_set()


def refresh():
    """Redraw now, before a slow robot move blocks the window."""
    root.update_idletasks()


def later(ms, function):
    root.after(ms, function)


def get_mode():
    return MODES.index(mode_var.get())  # 0 two player, 1 easy, 2 hard


def computer_first():
    return computer_first_var.get()


def robot_on():
    return robot_var.get()


def run():
    root.mainloop()
