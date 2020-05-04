import os

import pytest

import models
import grid


@pytest.fixture
def state():
    return models.GameState('super fun game')


def test_simple_placement_no_brand(state):
    grid.place_tile(state, 1, 3)

    assert state.grid[1][3] is not None
    assert state.grid[1][3].brand is None


def test_simple_placement_brand(state):
    with pytest.raises(Exception):
        grid.place_tile(state, 1, 3, brand=models.Brand.LUXOR)


def test_already_taken_spot(state):
    grid.place_tile(state, 1, 3)

    with pytest.raises(Exception):
        grid.place_tile(state, 1, 3)


def test_grow_chain_no_brand(state):
    grid.place_tile(state, 4, 6)
    grid.place_tile(state, 4, 7)

    assert state.grid[4][6] is not None
    assert state.grid[4][6].brand is None

    assert state.grid[4][7] == state.grid[4][6]


def test_grow_chain_choose_brand(state):
    grid.place_tile(state, 4, 6)
    grid.place_tile(state, 4, 7, brand=models.Brand.FESTIVAL)

    assert state.grid[4][6] is not None
    assert state.grid[4][6].brand == models.Brand.FESTIVAL

    assert state.grid[4][7] == state.grid[4][6]


def test_grow_chain_brand(state):
    grid.place_tile(state, 4, 6)
    grid.place_tile(state, 4, 7, brand=models.Brand.IMPERIAL)
    grid.place_tile(state, 3, 6)

    assert state.grid[4][6] is not None
    assert state.grid[4][6].brand == models.Brand.IMPERIAL

    assert state.grid[4][7] == state.grid[4][6]
    assert state.grid[4][7] == state.grid[3][6]


def test_grow_chain_illegally_specify_same_brand(state):
    grid.place_tile(state, 4, 6)
    grid.place_tile(state, 4, 7, brand=models.Brand.IMPERIAL)

    with pytest.raises(Exception):
        grid.place_tile(state, 3, 6, brand=models.Brand.IMPERIAL)


def test_grow_chain_illegally_specify_new_brand(state):
    grid.place_tile(state, 4, 6)
    grid.place_tile(state, 4, 7, brand=models.Brand.IMPERIAL)

    with pytest.raises(Exception):
        grid.place_tile(state, 3, 6, brand=models.Brand.WORLDWIDE)


def test_merge_unbranded_no_choice(state):
    grid.place_tile(state, 11, 0)
    grid.place_tile(state, 11, 2)

    assert state.grid[11][0] is not None
    assert state.grid[11][2] is not None
    assert state.grid[11][0] != state.grid[11][2]

    grid.place_tile(state, 11, 1)

    assert state.grid[11][0] is not None
    assert state.grid[11][1] is not None
    assert state.grid[11][2] is not None
    assert state.grid[11][0] == state.grid[11][2]
    assert state.grid[11][0] == state.grid[11][1]


def test_merge_unbranded_choose_brand(state):
    grid.place_tile(state, 11, 0)
    grid.place_tile(state, 11, 2)

    assert state.grid[11][0] is not None
    assert state.grid[11][2] is not None
    assert state.grid[11][0] != state.grid[11][2]

    grid.place_tile(state, 11, 1, brand=models.Brand.AMERICAN)

    assert state.grid[11][0] is not None
    assert state.grid[11][1] is not None
    assert state.grid[11][2] is not None
    assert state.grid[11][2].brand == models.Brand.AMERICAN
    assert state.grid[11][0] == state.grid[11][2]
    assert state.grid[11][0] == state.grid[11][1]


def test_merge_branded_with_unbranded(state):
    grid.place_tile(state, 11, 0)
    grid.place_tile(state, 11, 2)
    grid.place_tile(state, 11, 3, brand=models.Brand.CONTINENTAL)
    grid.place_tile(state, 10, 1)

    assert state.grid[11][0] is not None
    assert state.grid[11][2] is not None
    assert state.grid[11][3] is not None
    assert state.grid[10][1] is not None
    assert state.grid[11][0] != state.grid[11][2]
    assert state.grid[10][1] != state.grid[11][2]
    assert state.grid[10][1] != state.grid[11][0]
    assert state.grid[11][3] == state.grid[11][2]

    grid.place_tile(state, 11, 1)

    assert state.grid[11][0] is not None
    assert state.grid[11][1] is not None
    assert state.grid[11][2] is not None
    assert state.grid[11][3] is not None
    assert state.grid[10][1] is not None
    assert state.grid[11][0].brand == models.Brand.CONTINENTAL
    assert state.grid[11][0] == state.grid[11][2]
    assert state.grid[11][0] == state.grid[11][1]
    assert state.grid[11][0] == state.grid[11][3]
    assert state.grid[11][0] == state.grid[10][1]


def test_merge_multiple_branded_same_size(state):
    grid.place_tile(state, 8, 5)
    grid.place_tile(state, 8, 6, brand=models.Brand.TOWER)
    
    grid.place_tile(state, 6, 4)
    grid.place_tile(state, 6, 5, brand=models.Brand.AMERICAN)

    with pytest.raises(Exception):
        grid.place_tile(state, 7, 5)

    with pytest.raises(Exception):
        grid.place_tile(state, 7, 5, brand=models.Brand.LUXOR)

    grid.place_tile(state, 7, 5, brand=models.Brand.AMERICAN)

    assert state.grid[8][5] is not None
    assert state.grid[8][6] is not None
    assert state.grid[6][4] is not None
    assert state.grid[6][5] is not None
    assert state.grid[7][5] is not None
    assert state.grid[8][5].brand == models.Brand.AMERICAN
    assert state.grid[8][5] == state.grid[8][6]
    assert state.grid[8][5] == state.grid[7][5]
    assert state.grid[8][5] == state.grid[6][4]
    assert state.grid[8][5] == state.grid[6][5]


def test_merge_multiple_branded_different_size(state):
    grid.place_tile(state, 8, 5)
    grid.place_tile(state, 8, 6)
    grid.place_tile(state, 8, 7, brand=models.Brand.TOWER)
    grid.place_tile(state, 6, 4)
    grid.place_tile(state, 6, 5, brand=models.Brand.AMERICAN)

    with pytest.raises(Exception):
        grid.place_tile(state, 7, 5, brand=models.Brand.AMERICAN)

    with pytest.raises(Exception):
        grid.place_tile(state, 7, 5, brand=models.Brand.LUXOR)

    grid.place_tile(state, 7, 5)

    assert state.grid[8][5] is not None
    assert state.grid[8][6] is not None
    assert state.grid[8][7] is not None
    assert state.grid[6][4] is not None
    assert state.grid[6][5] is not None
    assert state.grid[7][5] is not None
    assert state.grid[8][5].brand == models.Brand.TOWER
    assert state.grid[8][5] == state.grid[8][6]
    assert state.grid[8][5] == state.grid[8][7]
    assert state.grid[8][5] == state.grid[7][5]
    assert state.grid[8][5] == state.grid[6][4]
    assert state.grid[8][5] == state.grid[6][5]


def test_grow_unbranded_wouldbe_locked_chain_no_choice(state):
    grid.place_tile(state, 0, 0)
    grid.place_tile(state, 1, 0)
    grid.place_tile(state, 2, 0)
    grid.place_tile(state, 3, 0)
    grid.place_tile(state, 4, 0)
    grid.place_tile(state, 5, 0)
    grid.place_tile(state, 6, 0)
    grid.place_tile(state, 7, 0)
    grid.place_tile(state, 8, 0)
    grid.place_tile(state, 9, 0)
    grid.place_tile(state, 10, 0)

    assert state.grid[9][0] == state.grid[1][0]
    assert not state.grid[7][0].is_locked()

    grid.place_tile(state, 2, 1)

    assert len(state.grid[2][1].tiles) == 12
    assert not state.grid[2][1].is_locked()


def test_grow_unbranded_wouldbe_locked_chain_choose_brand(state):
    grid.place_tile(state, 0, 0)
    grid.place_tile(state, 1, 0)
    grid.place_tile(state, 2, 0)
    grid.place_tile(state, 3, 0)
    grid.place_tile(state, 4, 0)
    grid.place_tile(state, 5, 0)
    grid.place_tile(state, 6, 0)
    grid.place_tile(state, 7, 0)
    grid.place_tile(state, 8, 0)
    grid.place_tile(state, 9, 0)
    grid.place_tile(state, 10, 0)

    assert state.grid[9][0] == state.grid[1][0]
    assert not state.grid[7][0].is_locked()

    grid.place_tile(state, 2, 1, brand=models.Brand.WORLDWIDE)

    assert len(state.grid[2][1].tiles) == 12
    assert state.grid[2][1].is_locked()
    assert state.grid[2][1].brand == models.Brand.WORLDWIDE


def test_grow_locked_chain(state):
    grid.place_tile(state, 0, 0)
    grid.place_tile(state, 1, 0)
    grid.place_tile(state, 2, 0)
    grid.place_tile(state, 3, 0)
    grid.place_tile(state, 4, 0, brand=models.Brand.FESTIVAL)
    grid.place_tile(state, 5, 0)
    grid.place_tile(state, 6, 0)
    grid.place_tile(state, 7, 0)
    grid.place_tile(state, 8, 0)
    grid.place_tile(state, 9, 0)
    grid.place_tile(state, 10, 0)

    assert state.grid[9][0] == state.grid[1][0]
    assert state.grid[7][0].is_locked()
    assert state.grid[0][0].brand == models.Brand.FESTIVAL
    assert state.grid[4][0].brand == models.Brand.FESTIVAL
    assert state.grid[5][0].brand == models.Brand.FESTIVAL

    grid.place_tile(state, 2, 1)

    assert len(state.grid[2][1].tiles) == 12
    assert state.grid[2][1].is_locked()
    assert state.grid[2][1].brand == models.Brand.FESTIVAL


def test_merge_locked_chains(state):
    grid.place_tile(state, 0, 0)
    grid.place_tile(state, 1, 0)
    grid.place_tile(state, 2, 0)
    grid.place_tile(state, 3, 0)
    grid.place_tile(state, 4, 0, brand=models.Brand.FESTIVAL)
    grid.place_tile(state, 5, 0)
    grid.place_tile(state, 6, 0)
    grid.place_tile(state, 7, 0)
    grid.place_tile(state, 8, 0)
    grid.place_tile(state, 9, 0)
    grid.place_tile(state, 10, 0)

    grid.place_tile(state, 0, 2)
    grid.place_tile(state, 1, 2)
    grid.place_tile(state, 2, 2)
    grid.place_tile(state, 3, 2)
    grid.place_tile(state, 4, 2, brand=models.Brand.LUXOR)
    grid.place_tile(state, 5, 2)
    grid.place_tile(state, 6, 2)
    grid.place_tile(state, 7, 2)
    grid.place_tile(state, 8, 2)
    grid.place_tile(state, 9, 2)
    grid.place_tile(state, 10, 2)

    assert state.grid[7][0].is_locked()
    assert state.grid[1][2].is_locked()

    with pytest.raises(Exception):
        grid.place_tile(state, 2, 1)


def test_merge_locked_and_unlocked_chain(state):
    grid.place_tile(state, 0, 0)
    grid.place_tile(state, 1, 0)
    grid.place_tile(state, 2, 0)
    grid.place_tile(state, 3, 0)
    grid.place_tile(state, 4, 0, brand=models.Brand.FESTIVAL)
    grid.place_tile(state, 5, 0)
    grid.place_tile(state, 6, 0)
    grid.place_tile(state, 7, 0)
    grid.place_tile(state, 8, 0)
    grid.place_tile(state, 9, 0)
    grid.place_tile(state, 10, 0)

    grid.place_tile(state, 0, 2)
    grid.place_tile(state, 1, 2)
    grid.place_tile(state, 2, 2)
    grid.place_tile(state, 3, 2)
    grid.place_tile(state, 4, 2, brand=models.Brand.LUXOR)
    grid.place_tile(state, 5, 2)
    grid.place_tile(state, 6, 2)
    grid.place_tile(state, 7, 2)
    grid.place_tile(state, 8, 2)
    grid.place_tile(state, 9, 2)

    assert state.grid[7][0].is_locked()
    assert not state.grid[1][2].is_locked()

    grid.place_tile(state, 2, 1)

    assert state.grid[0][0] == state.grid[7][2]
    assert state.grid[2][1].brand == models.Brand.FESTIVAL


def test_merge_locked_chains_and_unlocked_chain(state):
    grid.place_tile(state, 0, 1)
    grid.place_tile(state, 1, 1)
    grid.place_tile(state, 2, 1)
    grid.place_tile(state, 3, 1)
    grid.place_tile(state, 4, 1, brand=models.Brand.FESTIVAL)
    grid.place_tile(state, 5, 1)
    grid.place_tile(state, 6, 1)
    grid.place_tile(state, 7, 1)
    grid.place_tile(state, 8, 1)
    grid.place_tile(state, 9, 1)
    grid.place_tile(state, 5, 0)

    grid.place_tile(state, 0, 3)
    grid.place_tile(state, 1, 3)
    grid.place_tile(state, 2, 3)
    grid.place_tile(state, 3, 3)
    grid.place_tile(state, 4, 3, brand=models.Brand.LUXOR)
    grid.place_tile(state, 5, 3)
    grid.place_tile(state, 6, 3)
    grid.place_tile(state, 7, 3)
    grid.place_tile(state, 8, 3)
    grid.place_tile(state, 9, 3)
    grid.place_tile(state, 5, 4)

    grid.place_tile(state, 10, 2)

    assert state.grid[7][1].is_locked()
    assert state.grid[5][4].is_locked()
    assert not state.grid[10][2].is_locked()

    with pytest.raises(Exception):
        grid.place_tile(state, 9, 2)
