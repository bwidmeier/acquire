import os

import models


def place_tile(state, i, j, brand=None): # TODO: who made move and against what state version?
    if not 0 <= i < int(os.environ['ROW_COUNT']):
        raise Exception() # TODO: make custom exception type

    if not 0 <= j < int(os.environ['COLUMN_COUNT']):
        raise Exception() # TODO: make custom exception type

    if state.grid[i][j] is not None:
        raise Exception() # TODO: make custom exception type

    neighbors = _get_neighbors(state, i, j)
    locked_neighbors = [neighbor for neighbor in neighbors if neighbor.is_locked()]

    if len(locked_neighbors) > 1:
        raise Exception() # TODO: make custom exception type

    if len(neighbors) == 0:
        if brand:
            raise Exception()
        return _create_chain(state, i, j)

    if len(neighbors) == 1:
        return _grow_chain(state, neighbors[0], brand, i, j)

    return _merge_chains(state, neighbors, brand, i, j)


def _create_chain(state, i, j):
    # do we need to deep copy the state here?
    tile = models.Tile(i, j)
    chain = models.Chain([tile])
    state.grid[i][j] = chain
    return state


def _grow_chain(state, chain, brand, i, j):
    # do we need to deep copy the state here?
    tile = models.Tile(i, j)
    chain.add_tile(tile, brand)
    state.grid[i][j] = chain
    return state


def _merge_chains(state, current_chains, brand, i, j):
    # do we need to deep copy the state here?
    tile = models.Tile(i, j)
    new_chain = models.Chain([tile], brand)
    chains = current_chains + [new_chain]

    branded_chains, unbranded_chains = _partition(chains, lambda c: c.brand)

    if not any(branded_chains):
        if brand:
            raise Exception()

        return _combine_chains(state, chains, None)

    max_branded_chain_length = max(branded_chains, key=lambda c: len(c.tiles))
    largest_brands = [chain.brand for chain in branded_chains if len(chain) == max_branded_chain_length]

    if brand not in largest_brands:
        raise Exception() # TODO: custom type!

    return _combine_chains(state, chains, brand)


def _combine_chains(state, chains, brand):
    # import ipdb; ipdb.set_trace()
    tiles = [tile for chain in chains for tile in chain.tiles]
    new_chain = models.Chain(tiles, brand)

    for i, row in enumerate(state.grid):
        for j, chain in enumerate(row):
            if chain in chains:
                state.grid[i][j] = new_chain

    return state


def _partition(source, pred):
    positive, negative = [], []

    for elem in source:
        if pred(elem):
            positive.append(elem)
        else:
            negative.append(elem)

    return positive, negative


def _get_neighbors(state, i, j):
    return [tile for tile in _get_neighbors_with_nulls(state.grid, i, j) if tile]


def _get_neighbors_with_nulls(grid, i, j):
    if i > 0:
        yield grid[i - 1][j]
    if i < int(os.environ['ROW_COUNT']) - 1:
        yield grid[i + 1][j]
    if j > 0:
        yield grid[i][j - 1]
    if j < int(os.environ['COLUMN_COUNT']) - 1:
        yield grid[i][j + 1]
