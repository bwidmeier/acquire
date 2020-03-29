import os

import pytest

import models
import game


@pytest.fixture
def start_state():
    grid = []
    for i in range(int(os.environ['ROW_COUNT'])):
        grid.append([])
        for j in range(int(os.environ['COLUMN_COUNT'])):
            grid[i].append(None)
    return models.GameState(grid)


def test_simple_placement_no_brand(start_state):
    end_state = game.place_tile(start_state, 1, 3)

    assert end_state.grid[1][3] is not None
    assert end_state.grid[1][3].brand is None


def test_simple_placement_brand(start_state):
    with pytest.raises(Exception):
        game.place_tile(start_state, 1, 3, brand=models.Brand.LUXOR)


def test_already_taken_spot(start_state):
    state2 = game.place_tile(start_state, 1, 3)

    with pytest.raises(Exception):
        game.place_tile(state2, 1, 3)


def test_grow_chain_no_brand(start_state):
    state2 = game.place_tile(start_state, 4, 6)
    end_state = game.place_tile(state2, 4, 7)

    assert end_state.grid[4][6] is not None
    assert end_state.grid[4][6].brand is None

    assert end_state.grid[4][7] == end_state.grid[4][6]


def test_grow_chain_choose_brand(start_state):
    state_2 = game.place_tile(start_state, 4, 6)
    end_state = game.place_tile(state_2, 4, 7, brand=models.Brand.FESTIVAL)

    assert end_state.grid[4][6] is not None
    assert end_state.grid[4][6].brand == models.Brand.FESTIVAL

    assert end_state.grid[4][7] == end_state.grid[4][6]


def test_grow_chain_brand(start_state):
    state2 = game.place_tile(start_state, 4, 6)
    state3 = game.place_tile(state2, 4, 7, brand=models.Brand.IMPERIAL)
    end_state = game.place_tile(state3, 3, 6)

    assert end_state.grid[4][6] is not None
    assert end_state.grid[4][6].brand == models.Brand.IMPERIAL

    assert end_state.grid[4][7] == end_state.grid[4][6]
    assert end_state.grid[4][7] == end_state.grid[3][6]


def test_grow_chain_illegally_specify_same_brand(start_state):
    state2 = game.place_tile(start_state, 4, 6)
    state3 = game.place_tile(state2, 4, 7, brand=models.Brand.IMPERIAL)

    with pytest.raises(Exception):
        game.place_tile(state3, 3, 6, brand=models.Brand.IMPERIAL)


def test_grow_chain_illegally_specify_new_brand(start_state):
    state2 = game.place_tile(start_state, 4, 6)
    state3 = game.place_tile(state2, 4, 7, brand=models.Brand.IMPERIAL)

    with pytest.raises(Exception):
        game.place_tile(state3, 3, 6, brand=models.Brand.WORLDWIDE)


def test_merge_unbranded(start_state):
    state2 = game.place_tile(start_state, 0, 11)
    state3 = game.place_tile(state2, 2, 11)

    assert state3.grid[0][11] is not None
    assert state3.grid[2][11] is not None
    assert state3.grid[0][11] != state3.grid[2][11]

    end_state = game.place_tile(state3, 1, 11)

    assert end_state.grid[0][11] is not None
    assert end_state.grid[1][11] is not None
    assert end_state.grid[2][11] is not None
    assert end_state.grid[0][11] == state3.grid[2][11]
    assert end_state.grid[0][11] == state3.grid[1][11]
