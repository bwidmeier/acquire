import os

import toolz

import models
import stock
import grid
import tiles
import persistance


def transition_from_place(game_state, place_tile_result, game_id):
    acquirer = place_tile_result.acquirer
    acquired_chains = place_tile_result.acquired_chains

    if acquired_chains and not acquirer:
        raise Exception('If there are acquired chains, the acquirer must be specified!')

    sorted_chains = sorted(acquired_chains, key=lambda c: len(c.tiles), reverse=True)
    resolution_queue = []

    for chain in sorted_chains:
        brand = chain.brand
        rotated_player_order = _rotate_list(game_state.player_order, game_state.current_action_player)
        for player_id in rotated_player_order:
            if game_state.stock_by_player[player_id][brand]:
                resolution_queue.append({
                    'player_id': player_id, 
                    'acquirer': acquirer, 
                    'acquiree': brand, 
                    'acquiree_cost_at_acquisition_time': stock.calculate_price_from_chain(chain)
                })
    
    game_state.acquisition_resolution_queue = resolution_queue[::-1]
    game_state.most_recently_placed_tile = place_tile_result.tile
    
    return transition_from_resolve(game_state, game_id)


def transition_from_resolve(game_state, game_id):
    if not game_state.acquisition_resolution_queue:
        if not game_state.active_brands:
            return transition_from_buy(game_state, game_id)
            
        game_state.current_action_player = game_state.current_turn_player
        game_state.current_action_type = models.ActionType.BUY_STOCK
        game_state.current_action_details = None
        return game_state

    resolution_details = game_state.acquisition_resolution_queue.pop()
    game_state.current_action_player = resolution_details['player_id']
    game_state.current_action_type = models.ActionType.RESOLVE_ACQUISITION

    game_state.current_action_details = {
        'acquirer': resolution_details['acquirer'].value,
        'acquiree': resolution_details['acquiree'].value,
        'acquiree_cost_at_acquisition_time': resolution_details['acquiree_cost_at_acquisition_time']
    }

    return game_state


def transition_from_buy(game_state, game_id):
    if _is_game_over(game_state):
        stock.handle_game_end(game_state)
        game_state.current_action_type = models.ActionType.GAME_OVER
        game_state.current_action_player = None
        game_state.current_turn_player = None
        game_state.current_action_details = list(toolz.map(toolz.first, sorted(game_state.money_by_player.items(), key=toolz.second, reverse=True)))
        return game_state

    global_tiles = persistance.get_global_tiles(game_id)
    new_tile = tiles.draw_tile(global_tiles)
    game_state.tiles_remaining = len(global_tiles)
    
    if new_tile:
        persistance.deal_tile_to_player(game_id, game_state.current_turn_player, new_tile)

    next_player = _get_next_player(game_state)
    game_state.current_turn_player = next_player
    game_state.current_action_player = next_player
    game_state.current_action_type = models.ActionType.PLACE_TILE
    return game_state


def _is_game_over(state):
    branded_chains = grid.get_branded_chains(state)
    win_size = int(os.environ['WIN_SIZE'])
    chain_of_sufficient_size_exists = any(len(chain.tiles) >= win_size for chain in branded_chains)
    all_chains_are_locked = branded_chains and all(chain.is_locked() for chain in branded_chains) 
    return chain_of_sufficient_size_exists or all_chains_are_locked


def _rotate_list(source, start_elem):
    # This will have undefined output in the case that start_elem appears twice in source
    doubled_source = source + source
    
    should_emit = False
    for elem in doubled_source:
        if elem == start_elem and should_emit:
            return
        
        if elem == start_elem and not should_emit:
            should_emit = True

        if should_emit:
            yield elem


def _get_next_player(game_state):
    player_order = game_state.player_order
    current_turn_player = game_state.current_turn_player

    player_count = len(player_order)
    current_turn_player_index = player_order.index(current_turn_player)
    next_player_index = (current_turn_player_index + 1) % player_count

    return player_order[next_player_index]
