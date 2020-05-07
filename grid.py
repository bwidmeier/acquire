import os

import models


def place_tile(state, tile, brand=None): 
    if not 0 <= tile.x < int(os.environ['WIDTH']):
        raise models.RuleViolation('x coordinate is off the board!')
    
    if not 0 <= tile.y < int(os.environ['HEIGHT']):
        raise models.RuleViolation('y coordinate is off the board!')

    if state.grid[tile.x][tile.y] is not None:
        raise models.RuleViolation('Space already has tile on it!')

    neighbors = get_unique_neighbors(state.grid, tile)
    locked_neighbors = [neighbor for neighbor in neighbors if neighbor.is_locked()]

    if len(locked_neighbors) > 1:
        raise models.RuleViolation('Cannot place tile adjacent to multiple locked chains!')

    if len(neighbors) == 0:
        if brand:
            raise models.RuleViolation('Cannot specify brand for single tile!')

        _create_chain(state, tile)
        return models.PlaceTileResult(state, [], None, None, tile)

    if len(neighbors) == 1:
        _grow_chain(state, neighbors[0], brand, tile)
        return models.PlaceTileResult(state, [], None, brand, tile)

    acquired_chains, acquiree, new_brand = _merge_chains(state, neighbors, brand, tile)

    return models.PlaceTileResult(state, acquired_chains, acquiree, new_brand, tile)


def get_unique_neighbors(grid, tile):
    return list({chain for chain in _get_nonunique_neighbors_with_nulls(grid, tile) if chain})


def get_branded_chains(state):
    branded_chains = set()

    for column in state.grid:
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


def set_brand_lists(state):
    branded_chains = get_branded_chains(state)
    active_brands = [chain.brand for chain in branded_chains]
    inactive_brands = [brand for brand in models.Brand if brand not in active_brands]

    state.active_brands = sorted(active_brands, key=models.Brand.order_helper)
    state.inactive_brands = sorted(inactive_brands, key=models.Brand.order_helper)
    return state


def _create_chain(state, tile):
    chain = models.Chain([tile])
    state.grid[tile.x][tile.y] = chain
    return state


def _grow_chain(state, chain, brand, tile):
    if brand in state.cost_by_brand:
        raise models.RuleViolation('Cannot use brand already in use!')
    
    if brand is not None and chain.brand is not None:
        raise models.RuleViolation('Cannot rebrand chain!')

    if brand:
        chain.brand = brand

    chain.tiles.append(tile)
    
    state.grid[tile.x][tile.y] = chain
    return state


def _merge_chains(state, current_chains, brand, tile):
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


def _partition(source, pred):
    positive, negative = [], []

    for elem in source:
        if pred(elem):
            positive.append(elem)
        else:
            negative.append(elem)

    return positive, negative


def _get_nonunique_neighbors_with_nulls(grid, tile):
    x = tile.x
    y = tile.y
    
    if x > 0:
        yield grid[x - 1][y]
    if x < int(os.environ['WIDTH']) - 1:
        yield grid[x + 1][y]
    if y > 0:
        yield grid[x][y - 1]
    if y < int(os.environ['HEIGHT']) - 1:
        yield grid[x][y + 1]
