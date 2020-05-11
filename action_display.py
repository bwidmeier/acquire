import os


def record_place_action(state, place_tile_result):
    action_text = _generate_place_action_text(state, place_tile_result)
    _append_action_text(state, action_text)
    return state


def _generate_place_action_text(state, place_tile_result):
    player_name = _get_current_action_player_name(state)
    tile = place_tile_result.tile

    basic_info = f'{player_name} placed a tile at ({tile.x}, {tile.y}).'
    extra_info = ''
    
    if place_tile_result.new_brand:
        extra_info = f'They established a new chain under the {place_tile_result.new_brand.name} brand.'

    if place_tile_result.acquirer:
        brands_string = ', '.join(chain.brand.name for chain in place_tile_result.acquired_chains)
        extra_info = f'This resulted in {place_tile_result.acquirer.name} acquiring the following brand(s): {brands_string}'
    
    return f'{basic_info} {extra_info}'


def record_buy_action(state, brand, amount, price_per_stock):
    action_text = _generate_buy_action_text(state, brand, amount, price_per_stock)
    _append_action_text(state, action_text)
    return state


def _generate_buy_action_text(state, brand, amount, price_per_stock):
    player_name = _get_current_action_player_name(state)

    if amount == 3:
        return f'{player_name} jammed {brand.name} @ ${price_per_stock} each.'

    return f'{player_name} bought {amount} {brand.name} stock @ ${price_per_stock} each.'


def record_sell_action(state, brand, amount, price_per_stock):
    action_text = _generate_sell_action_text(state, brand, amount, price_per_stock)
    _append_action_text(state, action_text)
    return state


def _generate_sell_action_text(state, brand, amount, price_per_stock):
    player_name = _get_current_action_player_name(state)
    return f'{player_name} sold {amount} {brand.name} stock @ ${price_per_stock} each.'


def record_trade_action(state, source_brand, source_amount, target_brand, target_amount):
    action_text = _generate_trade_action_text(
        state, source_brand, source_amount, target_brand, target_amount)
    
    _append_action_text(state, action_text)
    return state


def _generate_trade_action_text(state, source_brand, source_amount, target_brand, target_amount):
    player_name = _get_current_action_player_name(state)
    return f'{player_name} traded {source_amount} {source_brand.name} for {target_amount} {target_brand.name}.'


def record_founders_share(state, brand):
    action_text = _generate_founders_share_text(state, brand)
    _append_action_text(state, action_text)
    return state


def _generate_founders_share_text(state, brand):
    player_name = _get_current_action_player_name(state)
    return f"{player_name} received a {brand.name} founder's share."


def record_majority_bonus(state, player_id, brand, amount, place):
    action_text = _generate_majority_bonus_text(state, player_id, brand, amount, place)
    _append_action_text(state, action_text)
    return state


def _generate_majority_bonus_text(state, player_id, brand, amount, place):
    player_name = state.user_data_by_id[player_id]['display_name']
    place_string = _generate_place_string(place)
    return f'{player_name} has received a {place_string} majority bonus in {brand.name} for ${amount}.'


def _generate_place_string(place_number):
    if place_number == 1:
        return '1st'

    if place_number == 2:
        return '2nd'

    raise Exception('Unknown place number encountered!')


def _append_action_text(state, text):
    max_count = int(os.environ['RECENT_ACTION_DISPLAY_COUNT'])
    state.most_recent_actions.append(text)
    state.most_recent_actions = state.most_recent_actions[-max_count:]
    return state


def _get_current_action_player_name(state):
    return state.user_data_by_id[state.current_action_player]['display_name']
