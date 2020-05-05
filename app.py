import os
import traceback
from random import shuffle

from flask import Flask, request
from flask_cors import CORS
import firebase_admin
import firebase_admin.auth

import persistance
import models
import grid
import tiles
import turns
import stock


firebase_admin.initialize_app()
app = Flask(__name__, static_folder='ui')
CORS(app, max_age=3600, supports_credentials=True)  


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/scripts/<path:path>')
def send_script(path):
    return app.send_static_file(f'scripts/{path}')


@app.route('/img/<path:path>')
def send_img(path):
    return app.send_static_file(f'img/{path}')


@app.route('/place_tile', methods=['POST'])
def place_tile():
    game_id = request.json['game_id']
    id_token = request.json['id_token']
    should_skip = request.json['skip']
    
    player_id = firebase_admin.auth.verify_id_token(id_token)['uid']
    state = persistance.get_game_state(game_id)
    
    if state.current_action_player != player_id:
        raise Exception("Stop trying to take other player's turns! You cheat!")

    if state.current_action_type != models.ActionType.PLACE_TILE:
        raise Exception('It is your turn, but it is not time to place a tile!')

    if should_skip:
        turns.transition_from_place(state, None, [])
        persistance.update_game_state(game_id, state.to_dict())
        return 'OK'

    x = int(request.json['x'])
    y = int(request.json['y'])
    raw_brand = request.json['brand']
    brand = None if raw_brand == '' else models.Brand(raw_brand)

    global_tiles = persistance.get_global_tiles(game_id)
    player_tiles = persistance.get_player_tiles(game_id, player_id)

    if not any(tile.x == x and tile.y == y for tile in player_tiles):
        raise Exception('You do not have that tile! Stop trying to cheat!')

    if not state.is_started:
        raise Exception('Cannot take turn until game has begun!')

    place_tile_result = grid.place_tile(state, x, y, brand)
    stock.apply_majority_bonuses(state, place_tile_result.acquired_chains)
    stock.award_founder_share(state, player_id, brand)
    turns.transition_from_place(state, place_tile_result.acquirer, place_tile_result.acquired_chains)

    new_tile = tiles.draw_tile(global_tiles)
    state.tiles_remaining = len(global_tiles)

    if new_tile:
        persistance.deal_tile_to_player(game_id, player_id, new_tile)
    
    persistance.delete_player_tile(game_id, player_id, models.Tile(x, y))
    # this should all happen atomically, but as a stopgap make sure this happens last
    persistance.update_game_state(game_id, state.to_dict())

    return 'OK'


@app.route('/resolve_acquisition', methods=['POST'])
def resolve_acquisition():
    game_id = request.json['game_id']
    id_token = request.json['id_token']
    sell_count = int(request.json['sell_count'])
    trade_count = int(request.json['trade_count'])

    user_id = firebase_admin.auth.verify_id_token(id_token)['uid']
    state = persistance.get_game_state(game_id)

    if state.current_action_player != user_id:
        raise Exception("Stop trying to take other player's turns! You cheat!")

    if state.current_action_type != models.ActionType.RESOLVE_ACQUISITION:
        raise Exception('It is your turn, but it is not time to resolve an acquisition!')

    if not state.is_started:
        raise Exception('Cannot take turn until game has begun!')

    acquiree = models.Brand(state.current_action_details['acquiree'])
    player_acquiree_stock_count = state.stock_by_player[user_id][acquiree]

    if sell_count + trade_count > player_acquiree_stock_count:
        raise Exception('Cannot trade and sell more stock than you current have!')

    acquirer = models.Brand(state.current_action_details['acquirer'])
    cost_at_acquisition_time = state.current_action_details['acquiree_cost_at_acquisition_time']

    stock.sell_stock(state, user_id, acquiree, cost_at_acquisition_time, sell_count)
    stock.trade_stock(state, user_id, acquiree, acquirer, trade_count)
    turns.transition_from_resolve(state)

    persistance.update_game_state(game_id, state.to_dict())

    return 'OK'


@app.route('/buy_stock', methods=['POST'])
def buy_stock():
    max_purchase_amount = int(os.environ['MAX_STOCK_PURCHASE_AMOUNT'])
    
    game_id = request.json['game_id']
    id_token = request.json['id_token']
    purchase_order = request.json['purchase_order']

    user_id = firebase_admin.auth.verify_id_token(id_token)['uid']
    state = persistance.get_game_state(game_id)

    if state.current_action_player != user_id:
        raise Exception("Stop trying to take other player's turns! You cheat!")

    if state.current_action_type != models.ActionType.BUY_STOCK:
        raise Exception('It is your turn, but it is not time to buy stock!')

    if not state.is_started:
        raise Exception('Cannot take turn until game has begun!')

    total_stock_purchased = 0

    for raw_brand, raw_amount in purchase_order.items():
        parsed_amount = int(raw_amount)
        total_stock_purchased += parsed_amount
        stock.buy_stock(state, user_id, models.Brand(raw_brand), parsed_amount)

    if total_stock_purchased > max_purchase_amount:
        raise Exception('Too many stock in purchase order!')

    turn_transitioned_state = turns.transition_from_buy(state)

    persistance.update_game_state(game_id, turn_transitioned_state.to_dict())

    return 'OK'


@app.route('/create_game', methods=['POST'])
def create_game():
    title = request.json['title']

    initial_state = models.GameState(title)

    game_id = persistance.create_game(title)
    persistance.create_game_state(game_id, initial_state)

    return 'OK'


@app.route('/join_game', methods=['POST'])
def join_game():
    game_id = request.json['game_id']
    user_id = request.json['user_id']

    game_state = persistance.get_game_state(game_id)

    if user_id in game_state.player_order:
        raise Exception('Player is already in this game!')

    if game_state.is_started:
        raise Exception('Cannot join a game in progress!')

    user_data = persistance.get_user_data(user_id)

    game_state.player_order.append(user_id)
    game_state.money_by_player[user_id] = 6000
    game_state.stock_by_player[user_id] = {brand: 0 for brand in models.Brand}
    game_state.user_data_by_id[user_id] = user_data

    persistance.update_game_state(game_id, game_state.to_dict())

    return 'OK'


@app.route('/start_game', methods=['POST'])
def start_game():
    game_id = request.json['game_id']

    game_state = persistance.get_game_state(game_id)
    
    if game_state.is_started:
        raise Exception('Cannot start already started game!')

    player_count_min = int(os.environ['PLAYER_COUNT_MIN'])
    player_count_max = int(os.environ['PLAYER_COUNT_MAX'])
    tile_hand_size = int(os.environ['TILE_HAND_SIZE'])

    player_count = len(game_state.player_order)

    if not player_count_min <= player_count <= player_count_max:
        raise Exception(f'Cannot start game with {player_count} players!')

    shuffle(game_state.player_order)
    starting_player = game_state.player_order[0]

    game_state.is_started = True
    game_state.current_turn_player = starting_player
    game_state.current_action_player = starting_player

    initial_tiles = tiles.generate_initial_tiles()

    board_starting_tiles = tiles.draw_tiles(initial_tiles, player_count)
    for tile in board_starting_tiles:
        grid.place_tile(game_state, tile.x, tile.y)

    tiles_by_player_id = { 
        player_id: tiles.draw_tiles(initial_tiles, tile_hand_size) 
        for player_id
        in game_state.player_order
    }

    game_state.tiles_remaining = len(initial_tiles)

    persistance.initialize_global_tiles(game_id, initial_tiles)
    persistance.initialize_player_tiles(game_id, tiles_by_player_id)
    persistance.update_game_state(game_id, game_state.to_dict())

    return 'OK'


if __name__ == '__main__':
    app.run()
