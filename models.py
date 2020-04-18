import os
import enum

import tile_placement


class Brand(enum.Enum):
    TOWER = 'T'
    LUXOR = 'L'
    WORLDWIDE = 'W'
    AMERICAN = 'A'
    FESTIVAL = 'F'
    IMPERIAL = 'I'
    CONTINENTAL = 'C'


class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Chain:
    def __init__(self, tiles, brand=None):
        self.tiles = tiles
        self.brand = brand

    def is_locked(self):
        return (self.brand is not None) and (len(self.tiles) >= int(os.environ['LOCK_MINIMUM']))

    def add_tile(self, tile, brand=None):
        if self.brand is not None and brand is not None:
            raise Exception()

        if brand is not None:
            self.brand = brand

        self.tiles.append(tile)

    def to_dict(self):
        return {
            'brand': self.brand.value if self.brand else None,
            'is_locked': self.is_locked()
        }


class GameState:
    def __init__(self, state_data):
        self.is_started = state_data['is_started']
        self.title = state_data['title']
        self.grid = self._build_grid_from_firestore_map(state_data['grid'])
        self.player_order = state_data['player_order']
        self.current_player = state_data['current_player']
        # self.current_decision = state_data['current_decision']
        self.money_by_player = state_data['money_by_player']
        self.stock_by_player = state_data['stock_by_player']

    def to_dict(self):
        return {
            'is_started': self.is_started,
            'title': self.title,
            'grid': {str(i): [chain.to_dict() if chain else None for chain in column] for i, column in enumerate(self.grid)},
            'player_order': self.player_order,
            'current_player': self.current_player,
            # 'current_decision': self.current_decision,
            'money_by_player': self.money_by_player,
            'stock_by_player': self.stock_by_player
        }

    def _build_grid_from_firestore_map(self, firestore_grid):
        grid = tile_placement.generate_initial_grid()
        branded_chains_by_brand = {brand: Chain([], brand) for brand in Brand}

        for x, firestore_column in enumerate(firestore_grid.values()):
            for y, firestore_space in enumerate(firestore_column):
                if not firestore_space:
                    continue
                
                brand_letter = firestore_space['brand']
                brand = Brand(brand_letter) if brand_letter else None 
                
                if brand:
                    chain = branded_chains_by_brand[brand]
                    chain.tiles.append(Tile(x, y))
                    grid[x][y] = chain
                    continue

                neighbors = set(tile_placement.get_neighbors(grid, x, y))

                tile = Tile(x, y)

                if not neighbors:
                    grid[x][y] = Chain([tile])
                    continue

                if len(neighbors) == 1:
                    (chain,) = neighbors
                    chain.tiles.append(tile)
                    grid[x][y] = chain
                    continue
                
                merged_chain = Chain([tile for chain in neighbors for tile in chain.tiles] + [tile])
                grid[x][y] = merged_chain

                for chain in neighbors:
                    for tile in chain.tiles:
                        grid[tile.x][tile.y] = merged_chain

        return grid