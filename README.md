# 🎮️ Tetris

A Tetris clone that runs directly in your terminal.

## Technologies

- `Python`
- `curses`

## Controls

- `←`, `→`, `↓`: Move the blocks
- `↑`: Rotate a block
- `p`: Pause / unpause the game
- `q`: Quit
- `Ctrl+C`: Quit

## Requirements

- Python 3.10+
- A terminal that supports `curses` and colors (most modern terminals)

## Installation

I have not packaged this game. To use it, you can clone it.

```bash
git clone https://github.com/jonahkraft/tetris.git
```

Then use the following commands to start the game.

```bash
cd tetris
python3 main.py
```

The game itself does not have any dependencies outside Python's standard library.  
You can create an alias to play it from anywhere. Just add

```bash
alias tetris="python3 ~/path/to/tetris/main.py"
```

to your `.bashrc` or `.zshrc` file. Use `tetris` to start the game.

## Preview

<img src="preview.png" alt="A preview of the gameplay">

## License

Distributed under the MIT License. See LICENSE file for more information. Do whatever you want with these scripts.
