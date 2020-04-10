import os
import enum


class Brand(enum.Enum):
    TOWER = enum.auto()
    LUXOR = enum.auto()
    WORLDWIDE = enum.auto()
    AMERICAN = enum.auto()
    FESTIVAL = enum.auto()
    IMPERIAL = enum.auto()
    CONTINENTAL = enum.auto()


class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f'({self.x}, {self.y})'


class Chain:
    def __init__(self, tiles, brand=None):
        self.tiles = tiles
        self.brand = brand

    def __repr__(self):
        return f'brand: {self.brand}, tiles: {self.tiles}'

    def is_locked(self):
        return (self.brand is not None) and (len(self.tiles) >= int(os.environ['LOCK_MINIMUM']))

    def add_tile(self, tile, brand=None):
        if self.brand is not None and brand is not None:
            raise Exception()

        if brand is not None:
            self.brand = brand

        self.tiles.append(tile)


class GameState:
    def __init__(self, grid):
        self.grid = grid

    def __repr__(self):
        return str(self.grid)
