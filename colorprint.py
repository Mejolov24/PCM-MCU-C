from typing import Literal

COLORS = {
    "reset": "\033[0m",

    # Standard
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",

    # Bright
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",

    # Extended (256-color)
    "orange": "\033[38;5;208m",
    "dark_orange": "\033[38;5;166m",
    "brown": "\033[38;5;94m",
    "dark_brown": "\033[38;5;52m",

    "pink": "\033[38;5;213m",
    "hot_pink": "\033[38;5;198m",

    "lime": "\033[38;5;118m",
    "teal": "\033[38;5;30m",

    "purple": "\033[38;5;129m",
    "violet": "\033[38;5;177m",

    "gold": "\033[38;5;220m",
    "beige": "\033[38;5;180m",

    "gray": "\033[38;5;245m",
    "dark_gray": "\033[38;5;238m",
}

ColorName = Literal[
    "reset",
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
    "bright_black", "bright_red", "bright_green", "bright_yellow",
    "bright_blue", "bright_magenta", "bright_cyan", "bright_white",

    "orange", "dark_orange", "brown", "dark_brown",
    "pink", "hot_pink",
    "lime", "teal",
    "purple", "violet",
    "gold", "beige",
    "gray", "dark_gray"
]

def cprint(text, color : ColorName):
    print(f"{COLORS[color]}{text}{COLORS['reset']}")
