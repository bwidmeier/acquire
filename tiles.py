import os
import random

import models


def draw_tile(tiles):
    if not tiles:
        return None
    return tiles.pop()


def draw_tiles(tiles, requested_tile_count):
    remaining_tile_count = len(tiles)
    tile_count = min(remaining_tile_count, requested_tile_count)
    return [tiles.pop() for _ in range(tile_count)]
    

def generate_initial_tiles():
    height = int(os.environ['HEIGHT'])
    width = int(os.environ['WIDTH'])

    tiles = []

    for x in range(width):
        for y in range(height):
            tiles.append(models.Tile(x, y))

    random.shuffle(tiles)

    return tiles
