import os

import models


def place_tile(state, x, y, brand=None):
    result = _place_tile_without_brand_registration(state, x, y, brand)
    
    for chain in result.acquired_chains:
        _unregister_brand(state, chain.brand)

    if result.new_brand:
        _register_brand(state, result.new_brand)

    return result


def get_unique_neighbors(grid, x, y):
    return list({chain for chain in _get_nonunique_neighbors_with_nulls(grid, x, y) if chain})


def get_branded_chains(grid):
    branded_chains = set()

    for column in grid:
        for chain in column:
            if chain and chain.brand:
                branded_chains.add(chain)

    return list(branded_chains)


def find_chain(grid, brand):
    for column in grid:
        for chain in column:
            if chain and chain.brand == brand:
                return chain

    return None


def _place_tile_without_brand_registration(state, x, y, brand=None):
    if not 0 <= x < int(os.environ['WIDTH']):
        raise models.RuleViolation('x coordinate is off the board!')
    
    if not 0 <= y < int(os.environ['HEIGHT']):
        raise models.RuleViolation('y coordinate is off the board!')

    if state.grid[x][y] is not None:
        raise models.RuleViolation('Space already has tile on it!')

    neighbors = get_unique_neighbors(state.grid, x, y)
    locked_neighbors = [neighbor for neighbor in neighbors if neighbor.is_locked()]

    if len(locked_neighbors) > 1:
        raise models.RuleViolation('Cannot place tile adjacent to multiple locked chains!')

    if len(neighbors) == 0:
        if brand:
            raise models.RuleViolation('Cannot specify brand for single tile!')

        _create_chain(state, x, y)
        return models.PlaceTileResult(state, [], None, None)

    if len(neighbors) == 1:
        _grow_chain(state, neighbors[0], brand, x, y)
        return models.PlaceTileResult(state, [], None, brand)

    acquired_chains, acquiree, new_brand = _merge_chains(state, neighbors, brand, x, y)

    return models.PlaceTileResult(state, acquired_chains, acquiree, new_brand)


def _create_chain(state, x, y):
    tile = models.Tile(x, y)
    chain = models.Chain([tile])
    state.grid[x][y] = chain
    return state


def _grow_chain(state, chain, brand, x, y):
    if brand in state.active_brands:
        raise models.RuleViolation('Cannot use brand already in use!')
    
    if brand is not None and chain.brand is not None:
        raise models.RuleViolation('Cannot rebrand chain!')

    if brand:
        chain.brand = brand

    tile = models.Tile(x, y)
    chain.tiles.append(tile)
    
    state.grid[x][y] = chain
    return state


def _merge_chains(state, current_chains, brand, x, y):
    tile = models.Tile(x, y)
    new_chain = models.Chain([tile])
    chains = current_chains + [new_chain]

    branded_chains = [chain for chain in chains if chain.brand]

    if not any(branded_chains):
        return _combine_chains(state, chains, brand)

    max_branded_chain_length_example = max(branded_chains, key=lambda c: len(c.tiles))
    max_branded_chain_length = len(max_branded_chain_length_example.tiles)
    largest_brands = [chain.brand for chain in branded_chains if len(chain.tiles) == max_branded_chain_length]

    largest_brand_count = len(largest_brands)

    if largest_brand_count == 1:
        if brand:
            raise models.RuleViolation('Cannot choose a brand when there is uniquely one largest!')

        return _combine_chains(state, chains, largest_brands[0])

    if not brand:
        raise models.RuleViolation('Must choose a brand!')

    if brand not in largest_brands:
        raise models.RuleViolation('Must choose one of the largest brands!')

    return _combine_chains(state, chains, brand)


def _combine_chains(state, chains, brand):
    tiles = [tile for chain in chains for tile in chain.tiles]
    new_chain = models.Chain(tiles, brand)

    for tile in tiles:
        state.grid[tile.x][tile.y] = new_chain

    acquired_chains = [chain for chain in chains if chain.brand not in [None, brand]]

    any_branded_chains = any(chain.brand for chain in chains)
    new_brand = brand if not any_branded_chains else None

    return (acquired_chains, brand, new_brand)


def _unregister_brand(state, brand):
    if not brand:
        raise Exception('Cannot unregister null brand!')

    state.active_brands.remove(brand)
    state.inactive_brands.append(brand)


def _register_brand(state, brand):
    if not brand:
        raise Exception('Cannot register null brand!')

    state.active_brands.append(brand)
    state.inactive_brands.remove(brand)


def _partition(source, pred):
    positive, negative = [], []

    for elem in source:
        if pred(elem):
            positive.append(elem)
        else:
            negative.append(elem)

    return positive, negative


def _get_nonunique_neighbors_with_nulls(grid, x, y):
    if x > 0:
        yield grid[x - 1][y]
    if x < int(os.environ['WIDTH']) - 1:
        yield grid[x + 1][y]
    if y > 0:
        yield grid[x][y - 1]
    if y < int(os.environ['HEIGHT']) - 1:
        yield grid[x][y + 1]
