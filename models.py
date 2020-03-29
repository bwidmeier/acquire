import os


class Brand:
    TOWER = 1
    LUXOR = 2
    WORLDWIDE = 3
    AMERICAN = 4
    FESTIVAL = 5
    IMPERIAL = 6
    CONTINENTAL = 7


class Tile:
    def __init__(self, i, j):
        self.i = i
        self.j = j


class Chain:
    def __init__(self, tiles, brand=None):
        self.tiles = tiles
        self.brand = brand

    def __repr__(self):
        return self.brand

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
        return self.grid
