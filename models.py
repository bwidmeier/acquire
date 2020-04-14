import os
import enum


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


class GameState:
    def __init__(self, state_data):
        self.grid = state_data['grid'].values()
        self.player_order = state_data['player_order']
        # self.current_player = state_data['current_player']
        # self.current_decision = state_data['current_decision']
        # self.money_by_player = state_data['money_by_player']
        # self.stock_by_player = state_data['stock_by_player']

    def to_json(self):
        return {
            'grid': {str(i): column for i, column in enumerate(self.grid)},
            'player_order': self.player_order,
            # 'current_player': self.current_player,
            # 'current_decision': self.current_decision,
            # 'money_by_player': self.money_by_player,
            # 'stock_by_player': self.stock_by_player
        }
