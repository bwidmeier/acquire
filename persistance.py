import os
import models


_GRID = []
for x in range(int(os.environ['WIDTH'])):
    _GRID.append([])
    for j in range(int(os.environ['HEIGHT'])):
        _GRID[x].append(None)


def get_state():
    return models.GameState(_GRID)


def set_state(state):
    _GRID = state.grid
