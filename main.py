from constants import WIDTH, HEIGHT, BLOCK_MASKS, BLOCK_COLORS, BLOCK_SYMBOL, BLOCK_WIDTH, COLOR_MAP, \
    POINTS_PER_FULL_ROW, ARROW_KEYS, DEFAULT_STATS, BASE_DIR
from custom_types import TetrisBlock, Vector2, BoundingBox, BlockMask, TetrisBlockShape, GameContext
import random
from typing import cast
import curses
import time
import sys
import traceback
import copy
import json
import os.path


def index_bm(x: int, y: int) -> int:
    """Index function for the block mask"""
    return 4 * y + (3 - x)


def load_stats() -> dict[str, int]:
    """Loads the stats dictionary from the corresponding json file"""
    try:
        with open(os.path.join(BASE_DIR, "stats.json")) as file:
            return json.load(file)
    except FileNotFoundError:
        return copy.deepcopy(DEFAULT_STATS)
    except json.JSONDecodeError:
        return copy.deepcopy(DEFAULT_STATS)


def save_stats(stats: dict[str, int]) -> None:
    """Saves the stats dictionary to the corresponding json file"""
    with open(os.path.join(BASE_DIR, "stats.json"), "w") as file:
        json.dump(stats, file)


# ----- Collision check -----


def get_shape_bounds(position: Vector2) -> BoundingBox:
    """Coverts the reference point of a shape (bottom left) into the corresponding bounding box"""
    return BoundingBox(position.x, position.x + 4, position.y, position.y + 4)


def get_intersection_area(box_a: BoundingBox, box_b: BoundingBox) -> BoundingBox:
    """Calculates the bounding box of the area where the given boxes could overlap"""
    return BoundingBox(
        max(box_a.min_x, box_b.min_x),
        min(box_a.max_x, box_b.max_x),
        max(box_a.min_y, box_b.min_y),
        min(box_a.max_y, box_b.max_y)
    )


def check_collision(intersection: BoundingBox, shape_a: TetrisBlock, shape_b: TetrisBlock) -> bool:
    """Checks if two shapes collide inside "intersection". This is the case if they collide at least in one coordinate."""

    for x in range(intersection.min_x, intersection.max_x):
        for y in range(intersection.min_y, intersection.max_y):

            val_a = shape_a.block[index_bm(x - shape_a.position.x, y - shape_a.position.y)]
            if not val_a: continue

            val_b = shape_b.block[index_bm(x - shape_b.position.x, y - shape_b.position.y)]
            if not val_b: continue

            return True

    return False


def intersects_any(shapes: list[TetrisBlock]) -> bool:
    """Check if the shape that is currently moving overlaps with any other shape"""

    # the last shape in the list is the one that is moving
    current_shape = shapes[-1]
    current_bb = get_shape_bounds(current_shape.position)

    for i in range(len(shapes) - 1):
        other_shape = shapes[i]
        other_bb = get_shape_bounds(other_shape.position)

        # if the bounding boxes don't overlap there cannot be a collision
        if current_bb.min_x > other_bb.max_x or current_bb.max_x < other_bb.min_x: continue
        if current_bb.min_y > other_bb.max_y or current_bb.max_y < other_bb.min_y: continue

        # get the area with possible overlapping
        intersection = get_intersection_area(current_bb, other_bb)

        # check for a collision
        if check_collision(intersection, current_shape, other_shape):
            return True

    return False


# ----- Handle full rows -----


def categorize_and_mark_shape(shape: TetrisBlock, cut_shapes: list[TetrisBlock], above_shapes: list[TetrisBlock], row_fill_mask: list[bool], row: int) -> None:
    """
    Categorizes shape relative to row (above/cut/below) and marks filled columns.
    """

    # check if the shape is above
    if shape.position.y > row:
        above_shapes.append(shape)
        return

    # check if the shape is below
    if shape.position.y + 4 <= row:
        return

    # otherwise, the shape cuts this row
    cut_shapes.append(shape)

    # write all columns that overlap with the shape into row_entries
    for x in range(4):
        col_idx = shape.position.x + x
        if not (0 <= col_idx < WIDTH): continue

        # update the row entry if the shape overlaps with the corresponding col_idx
        if shape.block[index_bm(x, row - shape.position.y)]:
            row_fill_mask[col_idx] = True


def move_shapes_down(shapes: list[TetrisBlock]) -> None:
    """
    Moves all shapes down by one row
    """
    for shape in shapes:
        shape.position.y -= 1


def remove_row_from_shapes(shapes: list[TetrisBlock], row: int) -> None:
    """
    Removes the given row from all shapes
    """
    for shape in shapes:
        row_idx = row - shape.position.y
        new_block = [False] * 16

        for x in range(4):
            for y in range(4):

                if y < row_idx:
                    # ignore rows that are below the current row
                    new_block[index_bm(x, y)] = shape.block[index_bm(x, y)]
                elif y + 1 < 4:
                    # move blocks downwards that are above row_idx
                    new_block[index_bm(x, y)] = shape.block[index_bm(x, y + 1)]
                else:
                    # the highest row becomes empty
                    new_block[index_bm(x, y)] = False

        shape.block = cast(BlockMask, tuple(new_block))


def clear_full_rows(shapes: list[TetrisBlock]) -> int:
    """
    Clears all full rows and returns the number of rows that have been cleared
    """

    number_cleared_rows = 0
    row = 0

    while row < HEIGHT:
        cut_shapes: list[TetrisBlock] = []  # shapes that are partially in this row
        above_shapes: list[TetrisBlock] = []  # shapes that are above this row
        is_column_filled = [False] * WIDTH  # tracks which columns have blocks in this row

        for shape in shapes:
            categorize_and_mark_shape(shape, cut_shapes, above_shapes, is_column_filled, row)

        if not all(is_column_filled):
            row += 1
            continue

        move_shapes_down(above_shapes)
        remove_row_from_shapes(cut_shapes, row)
        number_cleared_rows += 1

    return number_cleared_rows


# ----- Manage shapes -----


def get_new_shape() -> TetrisBlock:
    """Returns a new random shape."""

    shape_type = random.choice([
        TetrisBlockShape.I,
        TetrisBlockShape.J,
        TetrisBlockShape.L,
        TetrisBlockShape.O,
        TetrisBlockShape.S,
        TetrisBlockShape.T,
        TetrisBlockShape.Z
    ])

    return TetrisBlock(
        Vector2(WIDTH // 2 - 2, HEIGHT - 4),
        BLOCK_MASKS[shape_type],
        BLOCK_COLORS[shape_type]
    )


def spawn_shape(context: GameContext) -> None:
    """Adds the next shape to the shapes list and updates next_shape"""
    context.shapes.append(context.next_shape)
    context.next_shape = get_new_shape()


def rotate_shape(mask: BlockMask) -> BlockMask:
    """Rotates a shape by updating the block mask"""

    result = [False] * 16

    for x in range(4):
        for y in range(4):
            result[index_bm(y, 3 - x)] = mask[index_bm(x, y)]

    return cast(BlockMask, tuple(result))


def move_shape(shape: TetrisBlock, key: int) -> None:
    """Moves a shape depending on the key that was pressed"""

    match key:
        case curses.KEY_LEFT:
            shape.position.x -= 1

        case curses.KEY_RIGHT:
            shape.position.x += 1

        case curses.KEY_UP:
            shape.block = rotate_shape(shape.block)

        case curses.KEY_DOWN:
            shape.position.y -= 1


def is_in_bounds(shape: TetrisBlock) -> bool:
    """Checks if a shape is inside the bounds"""

    for x in range(4):
        for y in range(4):
            if not shape.block[index_bm(x, y)]: continue

            if any([
                shape.position.x + x < 0,
                shape.position.x + x >= WIDTH,
                shape.position.y + y < 0
            ]):
                return False
    return True


# ----- Manage level & points -----


def update_points(context: GameContext, num_cleared_rows: int) -> None:
    """
    Updates the points depending on the number of cleared rows.
    The player is rewarded for clearing multiple rows at a time.
    """

    factor = 0

    match num_cleared_rows:
        case 1:
            factor = 1
        case 2:
            factor = 3
        case 3:
            factor = 5
        case 4:
            factor = 8

    context.points += factor * POINTS_PER_FULL_ROW * (context.level + 1)


def update_level(context: GameContext, num_cleared_rows: int) -> None:
    """Updates the level based on the number of cleared rows"""

    context.cleared_rows += num_cleared_rows
    context.level = context.cleared_rows // 10


# ----- CLI -----


def reset_game(context: GameContext) -> None:
    """Resets the game if the player loses."""
    context.points = 0
    context.shapes.clear()
    spawn_shape(context)
    context.game_started = False
    context.level = 0
    context.cleared_rows = 0


def frame(key: int, context: GameContext) -> None:
    """
    Handles one frame of the game.
    Moves the current shape depending on the key that was pressed.
    Valides the movement to ensure the shape does not get out of bounds or overlaps with other shapes.
    Handles full rows and updates the points.
    Resets the game if the player loses.
    """

    if not key in ARROW_KEYS:
        return

    shape = context.shapes[-1]

    # Store the old position and block
    # If the shape gets out of bounds they are used to reset the position
    old_pos = Vector2(shape.position.x, shape.position.y)
    old_block = shape.block

    left_right_up = key in [curses.KEY_LEFT, curses.KEY_RIGHT, curses.KEY_UP]

    # move the shape
    move_shape(shape, key)

    # check if the shape is out of bounds
    out_of_bounds = not is_in_bounds(shape)

    # now check for collisions with other shapes
    collides = intersects_any(context.shapes)

    # The move was illegal if the shape gets out of bounds or collides with any other shape.
    # In this case, reset the position
    if out_of_bounds or collides:
        shape.position = old_pos
        shape.block = old_block
    else:
        # the move was valid and we are done
        return

    if not left_right_up:
        # check for full rows and delete them
        num_deleted_rows = clear_full_rows(context.shapes)

        # add points and level
        update_points(context, num_deleted_rows)
        update_level(context, num_deleted_rows)

        # add a new shape
        spawn_shape(context)

        # update highscore
        context.highscore = max(context.points, context.highscore)

        # if the new shape collides with any existing shape, the game is over
        if intersects_any(context.shapes):
            reset_game(context)


def init_colors() -> None:
    """Initializes all needed colors"""
    curses.start_color()

    if curses.can_change_color():
        curses.use_default_colors()
        bg = -1
    else:
        bg = curses.COLOR_BLACK

    curses.init_pair(COLOR_MAP["cyan"], curses.COLOR_CYAN, bg)
    curses.init_pair(COLOR_MAP["blue"], curses.COLOR_BLUE, bg)
    curses.init_pair(COLOR_MAP["magenta"], curses.COLOR_MAGENTA, bg)
    curses.init_pair(COLOR_MAP["yellow"], curses.COLOR_YELLOW, bg)
    curses.init_pair(COLOR_MAP["green"], curses.COLOR_GREEN, bg)
    curses.init_pair(COLOR_MAP["red"], curses.COLOR_RED, bg)
    curses.init_pair(COLOR_MAP["white"], curses.COLOR_WHITE, bg)


def run_game(stdscr, context: GameContext) -> None:
    """Main function handling user input"""

    curses.curs_set(0)  # disable cursor
    init_colors()
    stdscr.timeout(50)  # ensure that stdscr.getch() is not blocking

    last_time = time.time()

    # game loop
    while True:
        key = stdscr.getch()

        if key == ord("q"):
            quit_game(context)
        if key == ord("p"):
            context.paused = not context.paused
        if key in ARROW_KEYS:
            context.game_started = True

        if not context.paused and context.game_started:
            frame(key, context)

            # update frequency is based on the current number of points
            update_frequency = max(0.1, 1.0 - (context.cleared_rows // 10) * 0.1)

            if time.time() - last_time >= update_frequency:
                frame(curses.KEY_DOWN, context)
                last_time = time.time()

        draw(stdscr, context)
        time.sleep(0.01)


def quit_game(context: GameContext) -> None:
    """Exits the game and saves the highscore"""
    save_stats({
        "highscore": context.highscore
    })
    sys.exit(0)

# ----- Draw functions -----


def draw_borders(stdscr) -> None:
    """Draws the borders of the playing field"""

    # top and bottom border
    for x in range(WIDTH + 2):
        stdscr.addstr(
            0,
            x * BLOCK_WIDTH,
            BLOCK_SYMBOL,
            curses.color_pair(7)
        )
        stdscr.addstr(
            HEIGHT + 1,
            x * BLOCK_WIDTH,
            BLOCK_SYMBOL,
            curses.color_pair(7)
        )

    # left and right border
    for y in range(1, HEIGHT + 1):
        stdscr.addstr(
            y,
            0,
            BLOCK_SYMBOL,
            curses.color_pair(7)
        )
        stdscr.addstr(
            y,
            BLOCK_WIDTH * (WIDTH + 1),
            BLOCK_SYMBOL,
            curses.color_pair(7)
        )


def draw_shape(stdscr, position: Vector2, block: BlockMask, color: int) -> None:
    """Draws a single shape"""

    for x in range(4):
        for y in range(4):
            if not block[index_bm(x, y)]: continue

            stdscr.addstr(
                HEIGHT - (position.y + y),
                BLOCK_WIDTH * (position.x + x + 1),
                BLOCK_SYMBOL,
                curses.color_pair(color)
            )


def draw(stdscr, context: GameContext) -> None:
    """Draws a border box, all shapes and the score."""
    stdscr.erase()

    y_offset = 0

    try:
        draw_borders(stdscr)

        # shapes
        for shape in context.shapes:
            draw_shape(stdscr, shape.position, shape.block, shape.color)

        # score
        stdscr.addstr(y_offset, BLOCK_WIDTH * (WIDTH + 3), f"Score: {context.points}")

        # level
        y_offset += 2
        stdscr.addstr(y_offset, BLOCK_WIDTH * (WIDTH + 3), f"Level: {context.level}")

        # paused
        if context.paused:
            y_offset += 2
            stdscr.addstr(y_offset, BLOCK_WIDTH * (WIDTH + 3), "Paused...")

        # game_started
        if not context.game_started:
            y_offset += 2
            stdscr.addstr(y_offset, BLOCK_WIDTH * (WIDTH + 3), "Press an arrow key to start!")

        # highscore
        y_offset += 2
        stdscr.addstr(y_offset, BLOCK_WIDTH * (WIDTH + 3), f"Highscore: {context.highscore}")

        # next shape: title
        y_offset += 2
        stdscr.addstr(y_offset, BLOCK_WIDTH * (WIDTH + 3), "Next Block:")

        # next shape: shape
        y_offset += 4
        next_pos = Vector2(WIDTH + 2, HEIGHT - y_offset)
        draw_shape(stdscr, next_pos, context.next_shape.block, context.next_shape.color)

    except curses.error:
        # something is outside the visible area
        pass

    stdscr.noutrefresh()
    curses.doupdate()


# ----- Run application -----


def main() -> None:
    context = GameContext(
        points = 0,
        paused = False,
        game_started = False,
        shapes = [get_new_shape()],
        next_shape = get_new_shape(),
        highscore = load_stats().get("highscore", 0),
        level = 0,
        cleared_rows = 0
    )

    try:
        curses.wrapper(run_game, context)

    except KeyboardInterrupt:
        quit_game(context)

    except Exception as e:
        print(e)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
