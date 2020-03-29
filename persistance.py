import os
import models


_GRID = []
for i in range(int(os.environ['ROW_COUNT'])):
    _GRID.append([])
    for j in range(int(os.environ['COLUMN_COUNT'])):
        _GRID[i].append(None)


def get_state():
    return models.GameState(_GRID)


def set_state(state):
    _GRID = state.grid
