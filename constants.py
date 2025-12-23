from custom_types import BlockMask, TetrisBlockShape
import curses
from pathlib import Path

# WIDTH and HEIGHT must be odd
WIDTH = 13
HEIGHT = 21

BLOCK_SYMBOL = "██"
BLOCK_WIDTH = 2

POINTS_PER_FULL_ROW = 10

ARROW_KEYS = [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_STATS = {
    "highscore": 0
}

COLOR_MAP: dict[str, int] = {
    "cyan": 1,
    "blue": 2,
    "magenta": 3,
    "yellow": 4,
    "green": 5,
    "red": 6,
    "white": 7
}

BLOCK_MASKS: dict[TetrisBlockShape, BlockMask] = {
    TetrisBlockShape.I: (
        False, False, False, False,
        True, True, True, True,
        False, False, False, False,
        False, False, False, False
    ),
    TetrisBlockShape.J: (
        False, False, False, False,
        False, True, False, False,
        False, True, True, True,
        False, False, False, False
    ),
    TetrisBlockShape.L: (
        False, False, False, False,
        False, False, True, False,
        True, True, True, False,
        False, False, False, False
    ),
    TetrisBlockShape.O: (
        False, False, False, False,
        False, True, True, False,
        False, True, True, False,
        False, False, False, False
    ),
    TetrisBlockShape.S: (
        False, False, False, False,
        False, True, True, False,
        True, True, False, False,
        False, False, False, False
    ),
    TetrisBlockShape.T: (
        False, False, False, False,
        False, True, False, False,
        True, True, True, False,
        False, False, False, False
    ),
    TetrisBlockShape.Z: (
        False, False, False, False,
        True, True, False, False,
        False, True, True, False,
        False, False, False, False
    ),
}

BLOCK_COLORS: dict[TetrisBlockShape, int] = {
    TetrisBlockShape.I: COLOR_MAP["cyan"],
    TetrisBlockShape.J: COLOR_MAP["blue"],
    TetrisBlockShape.L: COLOR_MAP["magenta"],
    TetrisBlockShape.O: COLOR_MAP["yellow"],
    TetrisBlockShape.S: COLOR_MAP["green"],
    TetrisBlockShape.T: COLOR_MAP["red"],
    TetrisBlockShape.Z: COLOR_MAP["white"]
}
