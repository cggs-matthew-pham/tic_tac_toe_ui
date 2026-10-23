"""Turn what a player types (or later, says) into a square number 0-8.

Squares are numbered 1-9 for players, like a phone keypad:

    1 | 2 | 3
    4 | 5 | 6
    7 | 8 | 9

Accepted: "5", "five", "square 5", "centre", "top left", "bottom middle",
"middle right", "left top". Returns None if it can't tell which square.

Voice input only needs to turn speech into text and call parse_move().
"""

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9,
    # common speech-to-text slips
    "won": 1, "to": 2, "too": 2, "for": 4, "ate": 8,
}

ROWS = {"top": 0, "upper": 0, "bottom": 2, "lower": 2}
COLUMNS = {"left": 0, "right": 2}
MIDDLE = {"middle", "centre", "center", "mid", "central"}

FILLER = {"square", "the", "box", "cell", "please", "go", "in", "at", "on", "number", "put", "it"}


def parse_move(text):
    words = (
        text.lower()
        .replace("-", " ")
        .replace(",", " ")
        .replace(".", " ")
        .split()
    )
    words = [w for w in words if w not in FILLER]

    # A single number: digit or word.
    if len(words) == 1:
        word = words[0]
        number = int(word) if word.isdigit() else NUMBER_WORDS.get(word)
        if number is not None and 1 <= number <= 9:
            return number - 1
        if word in MIDDLE:
            return 4
        return None

    # A position: one row word and one column word, either order.
    # "middle" can mean either, so it fills whichever is missing.
    if len(words) == 2:
        row = column = None
        middles = 0
        for word in words:
            if word in ROWS:
                row = ROWS[word]
            elif word in COLUMNS:
                column = COLUMNS[word]
            elif word in MIDDLE:
                middles += 1
            else:
                return None
        if middles == 2:
            return 4
        if middles == 1:
            if row is None:
                row = 1
            elif column is None:
                column = 1
        if row is not None and column is not None:
            return row * 3 + column

    return None
