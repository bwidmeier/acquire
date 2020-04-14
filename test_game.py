import os

import pytest

import models
import tile_placement


@pytest.fixture
def start_state():
    grid = []
    for x in range(int(os.environ['WIDTH'])):
        grid.append([])
        for _ in range(int(os.environ['HEIGHT'])):
            grid[x].append(None)
    return models.GameState(grid)


def test_simple_placement_no_brand(start_state):
    end_state = tile_placement.place_tile(start_state, 1, 3)

    assert end_state.grid[1][3] is not None
    assert end_state.grid[1][3].brand is None


def test_simple_placement_brand(start_state):
    with pytest.raises(Exception):
        tile_placement.place_tile(start_state, 1, 3, brand=models.Brand.LUXOR)


def test_already_taken_spot(start_state):
    state2 = tile_placement.place_tile(start_state, 1, 3)

    with pytest.raises(Exception):
        tile_placement.place_tile(state2, 1, 3)


def test_grow_chain_no_brand(start_state):
    state2 = tile_placement.place_tile(start_state, 4, 6)
    end_state = tile_placement.place_tile(state2, 4, 7)

    assert end_state.grid[4][6] is not None
    assert end_state.grid[4][6].brand is None

    assert end_state.grid[4][7] == end_state.grid[4][6]


def test_grow_chain_choose_brand(start_state):
    state_2 = tile_placement.place_tile(start_state, 4, 6)
    end_state = tile_placement.place_tile(state_2, 4, 7, brand=models.Brand.FESTIVAL)

    assert end_state.grid[4][6] is not None
    assert end_state.grid[4][6].brand == models.Brand.FESTIVAL

    assert end_state.grid[4][7] == end_state.grid[4][6]


def test_grow_chain_brand(start_state):
    state2 = tile_placement.place_tile(start_state, 4, 6)
    state3 = tile_placement.place_tile(state2, 4, 7, brand=models.Brand.IMPERIAL)
    end_state = tile_placement.place_tile(state3, 3, 6)

    assert end_state.grid[4][6] is not None
    assert end_state.grid[4][6].brand == models.Brand.IMPERIAL

    assert end_state.grid[4][7] == end_state.grid[4][6]
    assert end_state.grid[4][7] == end_state.grid[3][6]


def test_grow_chain_illegally_specify_same_brand(start_state):
    state2 = tile_placement.place_tile(start_state, 4, 6)
    state3 = tile_placement.place_tile(state2, 4, 7, brand=models.Brand.IMPERIAL)

    with pytest.raises(Exception):
        tile_placement.place_tile(state3, 3, 6, brand=models.Brand.IMPERIAL)


def test_grow_chain_illegally_specify_new_brand(start_state):
    state2 = tile_placement.place_tile(start_state, 4, 6)
    state3 = tile_placement.place_tile(state2, 4, 7, brand=models.Brand.IMPERIAL)

    with pytest.raises(Exception):
        tile_placement.place_tile(state3, 3, 6, brand=models.Brand.WORLDWIDE)


def test_merge_unbranded_no_choice(start_state):
    state2 = tile_placement.place_tile(start_state, 11, 0)
    state3 = tile_placement.place_tile(state2, 11, 2)

    assert state3.grid[11][0] is not None
    assert state3.grid[11][2] is not None
    assert state3.grid[11][0] != state3.grid[11][2]

    end_state = tile_placement.place_tile(state3, 11, 1)

    assert end_state.grid[11][0] is not None
    assert end_state.grid[11][1] is not None
    assert end_state.grid[11][2] is not None
    assert end_state.grid[11][0] == end_state.grid[11][2]
    assert end_state.grid[11][0] == end_state.grid[11][1]


def test_merge_unbranded_choose_brand(start_state):
    state2 = tile_placement.place_tile(start_state, 11, 0)
    state3 = tile_placement.place_tile(state2, 11, 2)

    assert state3.grid[11][0] is not None
    assert state3.grid[11][2] is not None
    assert state3.grid[11][0] != state3.grid[11][2]

    end_state = tile_placement.place_tile(state3, 11, 1, brand=models.Brand.AMERICAN)

    assert end_state.grid[11][0] is not None
    assert end_state.grid[11][1] is not None
    assert end_state.grid[11][2] is not None
    assert end_state.grid[11][2].brand == models.Brand.AMERICAN
    assert end_state.grid[11][0] == end_state.grid[11][2]
    assert end_state.grid[11][0] == end_state.grid[11][1]


def test_merge_branded_with_unbranded(start_state):
    state2 = tile_placement.place_tile(start_state, 11, 0)
    state3 = tile_placement.place_tile(state2, 11, 2)
    state4 = tile_placement.place_tile(state3, 11, 3, brand=models.Brand.CONTINENTAL)
    state5 = tile_placement.place_tile(state4, 10, 1)

    assert state5.grid[11][0] is not None
    assert state5.grid[11][2] is not None
    assert state5.grid[11][3] is not None
    assert state5.grid[10][1] is not None
    assert state5.grid[11][0] != state5.grid[11][2]
    assert state5.grid[10][1] != state5.grid[11][2]
    assert state5.grid[10][1] != state5.grid[11][0]
    assert state5.grid[11][3] == state5.grid[11][2]

    end_state = tile_placement.place_tile(state5, 11, 1)

    assert end_state.grid[11][0] is not None
    assert end_state.grid[11][1] is not None
    assert end_state.grid[11][2] is not None
    assert end_state.grid[11][3] is not None
    assert end_state.grid[10][1] is not None
    assert end_state.grid[11][0].brand == models.Brand.CONTINENTAL
    assert end_state.grid[11][0] == end_state.grid[11][2]
    assert end_state.grid[11][0] == end_state.grid[11][1]
    assert end_state.grid[11][0] == end_state.grid[11][3]
    assert end_state.grid[11][0] == end_state.grid[10][1]


def test_merge_multiple_branded_same_size(start_state):
    state2 = tile_placement.place_tile(start_state, 8, 5)
    state3 = tile_placement.place_tile(state2, 8, 6, brand=models.Brand.TOWER)

    state4 = tile_placement.place_tile(state3, 6, 4)
    state5 = tile_placement.place_tile(state4, 6, 5, brand=models.Brand.AMERICAN)

    with pytest.raises(Exception):
        tile_placement.place_tile(state5, 7, 5)

    with pytest.raises(Exception):
        tile_placement.place_tile(state5, 7, 5, brand=models.Brand.LUXOR)

    end_state = tile_placement.place_tile(state5, 7, 5, brand=models.Brand.AMERICAN)

    assert end_state.grid[8][5] is not None
    assert end_state.grid[8][6] is not None
    assert end_state.grid[6][4] is not None
    assert end_state.grid[6][5] is not None
    assert end_state.grid[7][5] is not None
    assert end_state.grid[8][5].brand == models.Brand.AMERICAN
    assert end_state.grid[8][5] == end_state.grid[8][6]
    assert end_state.grid[8][5] == end_state.grid[7][5]
    assert end_state.grid[8][5] == end_state.grid[6][4]
    assert end_state.grid[8][5] == end_state.grid[6][5]


def test_merge_multiple_branded_different_size(start_state):
    state2 = tile_placement.place_tile(start_state, 8, 5)
    state3 = tile_placement.place_tile(state2, 8, 6)
    state4 = tile_placement.place_tile(state3, 8, 7, brand=models.Brand.TOWER)

    state5 = tile_placement.place_tile(state4, 6, 4)
    state6 = tile_placement.place_tile(state5, 6, 5, brand=models.Brand.AMERICAN)

    with pytest.raises(Exception):
        tile_placement.place_tile(state6, 7, 5, brand=models.Brand.AMERICAN)

    with pytest.raises(Exception):
        tile_placement.place_tile(state6, 7, 5, brand=models.Brand.LUXOR)

    end_state = tile_placement.place_tile(state6, 7, 5)

    assert end_state.grid[8][5] is not None
    assert end_state.grid[8][6] is not None
    assert end_state.grid[8][7] is not None
    assert end_state.grid[6][4] is not None
    assert end_state.grid[6][5] is not None
    assert end_state.grid[7][5] is not None
    assert end_state.grid[8][5].brand == models.Brand.TOWER
    assert end_state.grid[8][5] == end_state.grid[8][6]
    assert end_state.grid[8][5] == end_state.grid[8][7]
    assert end_state.grid[8][5] == end_state.grid[7][5]
    assert end_state.grid[8][5] == end_state.grid[6][4]
    assert end_state.grid[8][5] == end_state.grid[6][5]


def test_grow_unbranded_wouldbe_locked_chain_no_choice(start_state):
    state2 = tile_placement.place_tile(start_state, 0, 0)
    state3 = tile_placement.place_tile(state2, 1, 0)
    state4 = tile_placement.place_tile(state3, 2, 0)
    state5 = tile_placement.place_tile(state4, 3, 0)
    state6 = tile_placement.place_tile(state5, 4, 0)
    state7 = tile_placement.place_tile(state6, 5, 0)
    state8 = tile_placement.place_tile(state7, 6, 0)
    state9 = tile_placement.place_tile(state8, 7, 0)
    state10 = tile_placement.place_tile(state9, 8, 0)
    state11 = tile_placement.place_tile(state10, 9, 0)
    state12 = tile_placement.place_tile(state11, 10, 0)

    assert state12.grid[9][0] == state12.grid[1][0]
    assert not state12.grid[7][0].is_locked()

    end_state = tile_placement.place_tile(state12, 2, 1)

    assert len(end_state.grid[2][1].tiles) == 12
    assert not end_state.grid[2][1].is_locked()


def test_grow_unbranded_wouldbe_locked_chain_choose_brand(start_state):
    state2 = tile_placement.place_tile(start_state, 0, 0)
    state3 = tile_placement.place_tile(state2, 1, 0)
    state4 = tile_placement.place_tile(state3, 2, 0)
    state5 = tile_placement.place_tile(state4, 3, 0)
    state6 = tile_placement.place_tile(state5, 4, 0)
    state7 = tile_placement.place_tile(state6, 5, 0)
    state8 = tile_placement.place_tile(state7, 6, 0)
    state9 = tile_placement.place_tile(state8, 7, 0)
    state10 = tile_placement.place_tile(state9, 8, 0)
    state11 = tile_placement.place_tile(state10, 9, 0)
    state12 = tile_placement.place_tile(state11, 10, 0)

    assert state12.grid[9][0] == state12.grid[1][0]
    assert not state12.grid[7][0].is_locked()

    end_state = tile_placement.place_tile(state12, 2, 1, brand=models.Brand.WORLDWIDE)

    assert len(end_state.grid[2][1].tiles) == 12
    assert end_state.grid[2][1].is_locked()
    assert end_state.grid[2][1].brand == models.Brand.WORLDWIDE


def test_grow_locked_chain(start_state):
    state2 = tile_placement.place_tile(start_state, 0, 0)
    state3 = tile_placement.place_tile(state2, 1, 0)
    state4 = tile_placement.place_tile(state3, 2, 0)
    state5 = tile_placement.place_tile(state4, 3, 0)
    state6 = tile_placement.place_tile(state5, 4, 0, brand=models.Brand.FESTIVAL)
    state7 = tile_placement.place_tile(state6, 5, 0)
    state8 = tile_placement.place_tile(state7, 6, 0)
    state9 = tile_placement.place_tile(state8, 7, 0)
    state10 = tile_placement.place_tile(state9, 8, 0)
    state11 = tile_placement.place_tile(state10, 9, 0)
    state12 = tile_placement.place_tile(state11, 10, 0)

    assert state12.grid[9][0] == state12.grid[1][0]
    assert state12.grid[7][0].is_locked()
    assert state12.grid[0][0].brand == models.Brand.FESTIVAL
    assert state12.grid[4][0].brand == models.Brand.FESTIVAL
    assert state12.grid[5][0].brand == models.Brand.FESTIVAL

    end_state = tile_placement.place_tile(state12, 2, 1)

    assert len(end_state.grid[2][1].tiles) == 12
    assert end_state.grid[2][1].is_locked()
    assert end_state.grid[2][1].brand == models.Brand.FESTIVAL


def test_merge_locked_chains(start_state):
    state2 = tile_placement.place_tile(start_state, 0, 0)
    state3 = tile_placement.place_tile(state2, 1, 0)
    state4 = tile_placement.place_tile(state3, 2, 0)
    state5 = tile_placement.place_tile(state4, 3, 0)
    state6 = tile_placement.place_tile(state5, 4, 0, brand=models.Brand.FESTIVAL)
    state7 = tile_placement.place_tile(state6, 5, 0)
    state8 = tile_placement.place_tile(state7, 6, 0)
    state9 = tile_placement.place_tile(state8, 7, 0)
    state10 = tile_placement.place_tile(state9, 8, 0)
    state11 = tile_placement.place_tile(state10, 9, 0)
    state12 = tile_placement.place_tile(state11, 10, 0)

    state13 = tile_placement.place_tile(state12, 0, 2)
    state14 = tile_placement.place_tile(state13, 1, 2)
    state15 = tile_placement.place_tile(state14, 2, 2)
    state16 = tile_placement.place_tile(state15, 3, 2)
    state17 = tile_placement.place_tile(state16, 4, 2, brand=models.Brand.LUXOR)
    state18 = tile_placement.place_tile(state17, 5, 2)
    state19 = tile_placement.place_tile(state18, 6, 2)
    state20 = tile_placement.place_tile(state19, 7, 2)
    state21 = tile_placement.place_tile(state20, 8, 2)
    state22 = tile_placement.place_tile(state21, 9, 2)
    state23 = tile_placement.place_tile(state22, 10, 2)

    assert state23.grid[7][0].is_locked()
    assert state23.grid[1][2].is_locked()

    with pytest.raises(Exception):
        tile_placement.place_tile(state23, 2, 1)


def test_merge_locked_and_unlocked_chain(start_state):
    state2 = tile_placement.place_tile(start_state, 0, 0)
    state3 = tile_placement.place_tile(state2, 1, 0)
    state4 = tile_placement.place_tile(state3, 2, 0)
    state5 = tile_placement.place_tile(state4, 3, 0)
    state6 = tile_placement.place_tile(state5, 4, 0, brand=models.Brand.FESTIVAL)
    state7 = tile_placement.place_tile(state6, 5, 0)
    state8 = tile_placement.place_tile(state7, 6, 0)
    state9 = tile_placement.place_tile(state8, 7, 0)
    state10 = tile_placement.place_tile(state9, 8, 0)
    state11 = tile_placement.place_tile(state10, 9, 0)
    state12 = tile_placement.place_tile(state11, 10, 0)

    state13 = tile_placement.place_tile(state12, 0, 2)
    state14 = tile_placement.place_tile(state13, 1, 2)
    state15 = tile_placement.place_tile(state14, 2, 2)
    state16 = tile_placement.place_tile(state15, 3, 2)
    state17 = tile_placement.place_tile(state16, 4, 2, brand=models.Brand.LUXOR)
    state18 = tile_placement.place_tile(state17, 5, 2)
    state19 = tile_placement.place_tile(state18, 6, 2)
    state20 = tile_placement.place_tile(state19, 7, 2)
    state21 = tile_placement.place_tile(state20, 8, 2)
    state22 = tile_placement.place_tile(state21, 9, 2)

    assert state22.grid[7][0].is_locked()
    assert not state22.grid[1][2].is_locked()

    end_state = tile_placement.place_tile(state22, 2, 1)

    assert end_state.grid[0][0] == end_state.grid[7][2]
    assert end_state.grid[2][1].brand == models.Brand.FESTIVAL


def test_merge_locked_chains_and_unlocked_chain(start_state):
    state2 = tile_placement.place_tile(start_state, 0, 1)
    state3 = tile_placement.place_tile(state2, 1, 1)
    state4 = tile_placement.place_tile(state3, 2, 1)
    state5 = tile_placement.place_tile(state4, 3, 1)
    state6 = tile_placement.place_tile(state5, 4, 1, brand=models.Brand.FESTIVAL)
    state7 = tile_placement.place_tile(state6, 5, 1)
    state8 = tile_placement.place_tile(state7, 6, 1)
    state9 = tile_placement.place_tile(state8, 7, 1)
    state10 = tile_placement.place_tile(state9, 8, 1)
    state11 = tile_placement.place_tile(state10, 9, 1)
    state12 = tile_placement.place_tile(state11, 5, 0)

    state13 = tile_placement.place_tile(state12, 0, 3)
    state14 = tile_placement.place_tile(state13, 1, 3)
    state15 = tile_placement.place_tile(state14, 2, 3)
    state16 = tile_placement.place_tile(state15, 3, 3)
    state17 = tile_placement.place_tile(state16, 4, 3, brand=models.Brand.LUXOR)
    state18 = tile_placement.place_tile(state17, 5, 3)
    state19 = tile_placement.place_tile(state18, 6, 3)
    state20 = tile_placement.place_tile(state19, 7, 3)
    state21 = tile_placement.place_tile(state20, 8, 3)
    state22 = tile_placement.place_tile(state21, 9, 3)
    state23 = tile_placement.place_tile(state22, 5, 4)

    state24 = tile_placement.place_tile(state23, 10, 2)

    assert state24.grid[7][1].is_locked()
    assert state24.grid[5][4].is_locked()
    assert not state24.grid[10][2].is_locked()

    with pytest.raises(Exception):
        tile_placement.place_tile(state24, 9, 2)
