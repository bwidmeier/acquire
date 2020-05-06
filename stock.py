import math
import collections

import grid
import models


def buy_stock(state, player_id, brand, amount):
    if amount < 0:
        raise models.RuleViolation('Cannot buy negative stock!')

    if amount == 0:
        return state
    
    available_stock_count = state.stock_availability[brand]
    player_cash_amount = state.money_by_player[player_id]

    if amount > available_stock_count:
        raise models.RuleViolation('Insufficient stock available to fulfill this order!')

    price_per_stock = _calculate_price_from_state_and_brand(state, brand)
    total_price = price_per_stock * amount

    if total_price > player_cash_amount:
        raise models.RuleViolation('You cannot afford this order!')

    state.stock_availability[brand] -= amount
    _perform_money_change(state, player_id, -total_price)
    state.stock_by_player[player_id][brand] += amount

    return state


def sell_stock(state, player_id, brand, cost_per_stock, sell_count):
    if sell_count < 0:
        raise models.RuleViolation('Cannot sell negative stock!')

    player_stock_count = state.stock_by_player[player_id][brand]

    if player_stock_count < sell_count:
        raise models.RuleViolation('Cannot sell more stock than you have!')

    total_price = cost_per_stock * sell_count

    state.stock_by_player[player_id][brand] -= sell_count
    state.stock_availability[brand] += sell_count
    _perform_money_change(state, player_id, total_price)

    return state


def trade_stock(state, player_id, brand_to_send, brand_to_receive, send_count):
    if send_count < 0:
        raise models.RuleViolation('Cannot trade negative stock!')

    if send_count % 2 != 0:
        raise models.RuleViolation('Cannot trade an odd number of stock!')
    
    global_stock_to_receive_count = state.stock_availability[brand_to_receive]
    receive_count = send_count / 2

    if receive_count > global_stock_to_receive_count:
        raise models.RuleViolation('Insufficient stock available to complete trade!')

    state.stock_by_player[player_id][brand_to_send] -= send_count
    state.stock_by_player[player_id][brand_to_receive] += receive_count
    state.stock_availability[brand_to_send] += send_count
    state.stock_availability[brand_to_receive] -= receive_count

    return state


def award_founder_share(state, player_id, brand):
    if not brand:
        return state
    
    global_stock_count = state.stock_availability[brand]

    if global_stock_count < 1:
        return state

    state.stock_availability[brand] -= 1
    state.stock_by_player[player_id][brand] += 1
    return state


def apply_majority_bonuses(state, chains):
    for chain in chains:
        _apply_chain_majority_bonuses(state, chain)

    return state


def handle_game_end(state):
    branded_chains = grid.get_branded_chains(state.grid)
    players = state.player_order

    apply_majority_bonuses(state, branded_chains)

    for chain in branded_chains:
        brand = chain.brand
        cost_per_stock = calculate_price_from_chain(chain)
        for player in players:
            stock_count = state.stock_by_player[player][brand]
            sell_stock(state, player, brand, cost_per_stock, stock_count)


def calculate_price_from_chain(chain):
    brand = chain.brand

    if not brand:
        raise Exception('Chains without a brand have no price!')

    size = len(chain.tiles)
    value_tier = _calculate_effective_value_tier(brand, size)
    return _calculate_price_from_value_tier(value_tier)


def _perform_money_change(state, player_id, amount):
    player_name = state.user_data_by_id[player_id]['display_name']
    print(f'{player_name}: ${amount}')
    state.money_by_player[player_id] += amount


def _apply_chain_majority_bonuses(state, chain):
    value_tier = _calculate_effective_value_tier(chain.brand, len(chain.tiles))
    first_bonus = _calculate_first_majority_holder_bonus(value_tier)
    second_bonus = _calculate_second_majority_holder_bonus(value_tier)
    
    brand = chain.brand

    players_by_stock_count = collections.defaultdict(list)
    for player, stock_by_brand in state.stock_by_player.items():
        stock_count = stock_by_brand[brand]
        players_by_stock_count[stock_count].append(player)

    sorted_player_tiers = [
        players 
        for stock_count, players 
        in sorted(players_by_stock_count.items(), reverse=True) 
        if stock_count > 0
    ]

    tier_count = len(sorted_player_tiers)

    if tier_count == 0:
        # no one has any matching stock (I think this is impossible...)
        return state

    top_tier_players = sorted_player_tiers[0]
    top_tier_player_count = len(top_tier_players)

    if top_tier_player_count >= 2:
        # if tie for first, they all split first and second bonuses
        total_bonus = first_bonus + second_bonus
        raw_bonus_per_player = total_bonus / top_tier_player_count
        # round up to nearest 100
        bonus_per_player = math.ceil(raw_bonus_per_player / 100) * 100
        for player_id in top_tier_players:
            _perform_money_change(state, player_id, bonus_per_player)

        return state

    # there is a unique winner
    (top_tier_player,) = top_tier_players
    _perform_money_change(state, top_tier_player, first_bonus)

    if tier_count == 1:
        # winner gets both bonuses if no one else has matching stock
        _perform_money_change(state, top_tier_player, second_bonus)
        return state

    # there are some number of second place finishers (could be 1), split 2nd bonus among them
    second_tier_players = sorted_player_tiers[1]
    second_tier_player_count = len(second_tier_players)
    
    raw_bonus_per_player = second_bonus / second_tier_player_count
    bonus_per_player = math.ceil(raw_bonus_per_player / 100) * 100
    for player_id in second_tier_players:
        _perform_money_change(state, player_id, bonus_per_player)

    return state
    

def _calculate_price_from_state_and_brand(state, brand):
    chain = grid.find_chain(state.grid, brand)

    if not chain:
        raise models.RuleViolation('No chains of this brand found!')

    return calculate_price_from_chain(chain)


def _calculate_price_from_value_tier(effective_value_tier):
    if not 0 <= effective_value_tier <= 10:
        raise Exception('Invalid value tier specified!')

    return 200 + (effective_value_tier * 100)


def _calculate_first_majority_holder_bonus(effective_value_tier):
    if not 0 <= effective_value_tier <= 10:
        raise Exception('Invalid value tier specified!')

    return 2000 + (effective_value_tier * 1000)


def _calculate_second_majority_holder_bonus(effective_value_tier):
    if not 0 <= effective_value_tier <= 10:
        raise Exception('Invalid value tier specified!')

    return 1000 + (effective_value_tier * 500)


def _calculate_effective_value_tier(brand, size):
    raw_value_tier = _calculate_raw_chain_value_tier(size)
    value_tier_bonus = _calculate_brand_tier_bonus(brand)
    
    return raw_value_tier + value_tier_bonus


def _calculate_raw_chain_value_tier(chain_size):
    if chain_size < 2:
        raise Exception('Chain is too small to be branded. Something bad happened!')

    if chain_size == 2:
        return 0

    if chain_size == 3:
        return 1

    if chain_size == 4:
        return 2

    if chain_size == 5:
        return 3

    if chain_size in range(6, 11):
        return 4

    if chain_size in range(11, 21):
        return 5

    if chain_size in range(21, 31):
        return 6

    if chain_size in range(31, 41):
        return 7

    if chain_size >= 41:
        return 8


def _calculate_brand_tier_bonus(brand):
    if brand in [models.Brand.TOWER, models.Brand.LUXOR]:
        return 0

    if brand in [models.Brand.WORLDWIDE, models.Brand.AMERICAN, models.Brand.FESTIVAL]:
        return 1

    if brand in [models.Brand.IMPERIAL, models.Brand.CONTINENTAL]:
        return 2

    raise Exception('Unknown brand encountered!')
