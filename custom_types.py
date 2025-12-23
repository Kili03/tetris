from dataclasses import dataclass
from enum import Enum


class TetrisBlockShape(Enum):
    I = 0
    J = 1
    L = 2
    O = 3
    S = 4
    T = 5
    Z = 6


BlockMask = tuple[
    bool, bool, bool, bool,
    bool, bool, bool, bool,
    bool, bool, bool, bool,
    bool, bool, bool, bool
]


@dataclass
class Vector2:
    x: int
    y: int


@dataclass
class TetrisBlock:
    position: Vector2
    block: BlockMask
    color: int


@dataclass
class BoundingBox:
    min_x: int
    max_x: int
    min_y: int
    max_y: int


@dataclass
class GameContext:
    points: int
    paused: bool
    game_started: bool
    shapes: list[TetrisBlock]
    next_shape: TetrisBlock
    highscore: int
    level: int
    cleared_rows: int
