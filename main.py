import os
from random import shuffle

import persistance
import models
import tile_placement


def place_tile(request):
    data = request.get_json(silent=True)
    game_id = data['game_id']
    x = data['x']
    y = data['y']
    raw_brand = data['brand']

    brand = None if raw_brand is None else models.Brand(raw_brand)

    old_state = persistance.get_game_state(game_id)
    new_state = tile_placement.place_tile(old_state, x, y, brand)
    persistance.update_game_state(game_id, new_state.to_json())

    return 'OK'


def start_game(request):
    data = request.get_json(silent=True)
    game_id = data['game_id']

    persistance.update_game(game_id, is_started=True)

    game = persistance.get_game(game_id)
    players = game['players']
    shuffle(players)

    empty_grid = _generate_initial_grid()

    # players start with $6k
    initial_state = models.GameState({
        'grid': empty_grid,
        'player_order': players
    })

    persistance.create_game_state(game_id, initial_state)


def _generate_initial_grid():
    height = int(os.environ['HEIGHT'])
    width = int(os.environ['WIDTH'])
    return {x: [None for _ in range(height)] for x in range(width)}
