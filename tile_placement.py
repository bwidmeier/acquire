import os

import models


def place_tile(state, x, y, brand=None):  # TODO: who made move and against what state version?
    if not 0 <= x < int(os.environ['WIDTH']):
        raise Exception()  # TODO: make custom exception type

    if not 0 <= y < int(os.environ['HEIGHT']):
        raise Exception()  # TODO: make custom exception type

    if state.grid[x][y] is not None:
        raise Exception()  # TODO: make custom exception type

    neighbors = _get_neighbors(state, x, y)
    locked_neighbors = [neighbor for neighbor in neighbors if neighbor.is_locked()]

    if len(locked_neighbors) > 1:
        raise Exception()  # TODO: make custom exception type

    if len(neighbors) == 0:
        if brand:
            raise Exception()
        return _create_chain(state, x, y)

    if len(neighbors) == 1:
        return _grow_chain(state, neighbors[0], brand, x, y)

    return _merge_chains(state, neighbors, brand, x, y)


def _create_chain(state, x, y):
    # do we need to deep copy the state here?
    tile = models.Tile(x, y)
    chain = models.Chain([tile])
    state.grid[x][y] = chain
    return state


def _grow_chain(state, chain, brand, x, y):
    # do we need to deep copy the state here?
    tile = models.Tile(x, y)
    chain.add_tile(tile, brand)
    state.grid[x][y] = chain
    return state


def _merge_chains(state, current_chains, brand, x, y):
    # do we need to deep copy the state here?
    tile = models.Tile(x, y)
    new_chain = models.Chain([tile])
    chains = current_chains + [new_chain]

    branded_chains, unbranded_chains = _partition(chains, lambda c: c.brand)

    if not any(branded_chains):
        return _combine_chains(state, chains, brand)

    max_branded_chain_length_example = max(branded_chains, key=lambda c: len(c.tiles))
    max_branded_chain_length = len(max_branded_chain_length_example.tiles)
    largest_brands = [chain.brand for chain in branded_chains if len(chain.tiles) == max_branded_chain_length]

    largest_brand_count = len(largest_brands)

    if largest_brand_count == 1:
        if brand:
            raise Exception()

        return _combine_chains(state, chains, largest_brands[0])

    if brand not in largest_brands:
        raise Exception() # TODO: custom type!

    return _combine_chains(state, chains, brand)


def _combine_chains(state, chains, brand):
    tiles = [tile for chain in chains for tile in chain.tiles]
    new_chain = models.Chain(tiles, brand)

    for tile in tiles:
        state.grid[tile.x][tile.y] = new_chain

    return state


def _partition(source, pred):
    positive, negative = [], []

    for elem in source:
        if pred(elem):
            positive.append(elem)
        else:
            negative.append(elem)

    return positive, negative


def _get_neighbors(state, x, y):
    return [tile for tile in _get_neighbors_with_nulls(state.grid, x, y) if tile]


def _get_neighbors_with_nulls(grid, x, y):
    if x > 0:
        yield grid[x - 1][y]
    if x < int(os.environ['WIDTH']) - 1:
        yield grid[x + 1][y]
    if y > 0:
        yield grid[x][y - 1]
    if y < int(os.environ['HEIGHT']) - 1:
        yield grid[x][y + 1]
