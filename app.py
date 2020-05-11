import os
import traceback
from random import shuffle

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
import firebase_admin.auth

import persistance
import models
import grid
import tiles
import turns
import stock
import action_display


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
    x = int(request.json['x'])
    y = int(request.json['y'])
    raw_brand = request.json['brand']
    brand = None if raw_brand == '' else models.Brand(raw_brand)

    player_id = firebase_admin.auth.verify_id_token(id_token)['uid']
    state = persistance.get_game_state(game_id)
    
    if state.current_action_player != player_id:
        raise models.RuleViolation("Stop trying to take other player's turns! You cheat!")

    if state.current_action_type != models.ActionType.PLACE_TILE:
        raise models.RuleViolation('It is your turn, but it is not time to place a tile!')

    player_tiles = persistance.get_player_tiles(game_id, player_id)

    if not any(tile.x == x and tile.y == y for tile in player_tiles):
        raise models.RuleViolation('You do not have that tile! Stop trying to cheat!')

    if not state.is_started:
        raise models.RuleViolation('Cannot take turn until game has begun!')

    tile = models.Tile(x, y)
    place_tile_result = grid.place_tile(state, tile, brand)
    stock.apply_majority_bonuses(state, place_tile_result.acquired_chains)
    stock.award_founder_share(state, player_id, brand)
    grid.set_brand_lists(state)
    stock.set_price_table(state)
    turns.transition_from_place(state, place_tile_result, game_id)
    
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
        raise models.RuleViolation("Stop trying to take other player's turns! You cheat!")

    if state.current_action_type != models.ActionType.RESOLVE_ACQUISITION:
        raise models.RuleViolation('It is your turn, but it is not time to resolve an acquisition!')

    if not state.is_started:
        raise models.RuleViolation('Cannot take turn until game has begun!')

    acquiree = models.Brand(state.current_action_details['acquiree'])
    player_acquiree_stock_count = state.stock_by_player[user_id][acquiree]

    if sell_count + trade_count > player_acquiree_stock_count:
        raise models.RuleViolation('Cannot trade and sell more stock than you current have!')

    acquirer = models.Brand(state.current_action_details['acquirer'])
    cost_at_acquisition_time = state.current_action_details['acquiree_cost_at_acquisition_time']
    
    stock.sell_stock(state, user_id, acquiree, cost_at_acquisition_time, sell_count)
    stock.trade_stock(state, user_id, acquiree, acquirer, trade_count)

    turns.transition_from_resolve(state, game_id)

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
        raise models.RuleViolation("Stop trying to take other player's turns! You cheat!")

    if state.current_action_type != models.ActionType.BUY_STOCK:
        raise models.RuleViolation('It is your turn, but it is not time to buy stock!')

    if not state.is_started:
        raise models.RuleViolation('Cannot take turn until game has begun!')

    total_stock_purchased = 0

    for raw_brand, raw_amount in purchase_order.items():
        parsed_amount = int(raw_amount)
        total_stock_purchased += parsed_amount
        brand = models.Brand(raw_brand)
        stock.buy_stock(state, user_id, brand, parsed_amount)

    if total_stock_purchased > max_purchase_amount:
        raise models.RuleViolation('Too many stock in purchase order!')

    turn_transitioned_state = turns.transition_from_buy(state, game_id)

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
        raise models.RuleViolation('Player is already in this game!')

    if game_state.is_started:
        raise models.RuleViolation('Cannot join a game in progress!')

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
        raise models.RuleViolation('Cannot start already started game!')

    player_count_min = int(os.environ['PLAYER_COUNT_MIN'])
    player_count_max = int(os.environ['PLAYER_COUNT_MAX'])
    tile_hand_size = int(os.environ['TILE_HAND_SIZE'])

    player_count = len(game_state.player_order)

    if not player_count_min <= player_count <= player_count_max:
        raise models.RuleViolation(f'Cannot start game with {player_count} players!')

    shuffle(game_state.player_order)
    starting_player = game_state.player_order[0]

    initial_tiles = tiles.generate_initial_tiles()

    board_starting_tiles = tiles.draw_tiles(initial_tiles, player_count)
    for tile in board_starting_tiles:
        grid.place_tile(game_state, tile)

    game_state.is_started = True
    game_state.current_turn_player = starting_player
    game_state.current_action_player = starting_player

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


@app.errorhandler(models.RuleViolation)
def handle_rule_violation(e):
    return (jsonify(error=str(e)), 400)



@app.after_request
def add_header(r):
    if bool(int(os.environ.get('FORCE_REFRESH', '0'))):
        r.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        r.headers['Pragma'] = 'no-cache'
        r.headers['Expires'] = '0'
    return r


if __name__ == '__main__':
    app.run()
