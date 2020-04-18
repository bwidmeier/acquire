import os
from random import shuffle

import persistance
import models
import tile_placement


def _cors_allow_all(fnc):
    def new_func(request):
        if request.method == 'OPTIONS':
            headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Max-Age': '3600',
                'Access-Control-Allow-Credentials': 'true'
            }

            return ('', 204, headers)

        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': 'true'
        }

        return (fnc(request), 200, headers)

    return new_func


@_cors_allow_all
def place_tile(request):
    data = request.get_json(silent=True)
    game_id = data['game_id']
    x = int(data['x'])
    y = int(data['y'])
    raw_brand = data['brand']

    brand = None if raw_brand == '' else models.Brand(raw_brand)

    old_state = persistance.get_game_state(game_id)
    new_state = tile_placement.place_tile(old_state, x, y, brand)
    persistance.update_game_state(game_id, new_state.to_dict())

    return 'OK'


@_cors_allow_all
def create_game(request):
    title = request.json['title']

    game_id = persistance.create_game(title)

    empty_grid = tile_placement.generate_initial_grid()

    # players start with $6k
    initial_state = models.GameState({
        'is_started': False,
        'title': title,
        'grid': empty_grid,
        'player_order': [],
        'current_player': None,
        'stock_by_player': {},
        'money_by_player': {}
    })

    persistance.create_game_state(game_id, initial_state)


@_cors_allow_all
def join_game(request):
    game_id = request.json['game_id']
    user_id = request.json['user_id']

    game_state = persistance.get_game_state(game_id)

    if user_id in game_state.player_order:
        raise Exception('Player is already in this game!')

    if game_state.is_started:
        raise Exception('Cannot join a game in progress!')

    game_state.player_order.append(user_id)
    game_state.money_by_player['user_id'] = 6000
    game_state.stock_by_player['user_id'] = {brand.value: 0 for brand in models.Brand}

    persistance.update_game_state(game_id, game_state.to_dict())


@_cors_allow_all
def start_game(request):
    game_id = request.json['game_id']

    game_state = persistance.get_game_state(game_id)
    
    if game_state.is_started:
        raise Exception('Cannot start already started game!')

    shuffle(game_state.player_order)
    game_state.is_started = True

    persistance.update_game_state(game_id, game_state.to_dict())
