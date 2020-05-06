import os
import enum

import toolz

import grid


class Brand(enum.Enum):
    TOWER = 'T'
    LUXOR = 'L'
    WORLDWIDE = 'W'
    AMERICAN = 'A'
    FESTIVAL = 'F'
    IMPERIAL = 'I'
    CONTINENTAL = 'C'


class ActionType(enum.Enum):
    PLACE_TILE = 'PLACE'
    BUY_STOCK = 'BUY'
    RESOLVE_ACQUISITION = 'RESOLVE'
    GAME_OVER = 'GAME_OVER'


class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y
        }


class Chain:
    def __init__(self, tiles, brand=None):
        self.tiles = tiles
        self.brand = brand

    def is_locked(self):
        return (self.brand is not None) and (len(self.tiles) >= int(os.environ['LOCK_MINIMUM']))

    def to_dict(self):
        return {
            'brand': self.brand.value if self.brand else None,
            'is_locked': self.is_locked()
        }


class GameState:
    def __init__(self, title):
        self.is_started = False
        self.title = title
        self.grid = GameState._generate_initial_grid()
        self.player_order = []
        self.current_turn_player = None
        self.current_action_player = None
        self.current_action_type = ActionType.PLACE_TILE
        self.current_action_details = None
        self.stock_availability = { brand: 25 for brand in Brand }
        self.stock_by_player = {}
        self.money_by_player = {}
        self.user_data_by_id = {}
        self.tiles_remaining = 0
        self.active_brands = []
        self.inactive_brands = [brand for brand in Brand]
        self.acquisition_resolution_queue = []


    def to_dict(self):
        return {
            'is_started': self.is_started,
            'title': self.title,
            'grid': { str(i): [chain.to_dict() if chain else None for chain in column] for i, column in enumerate(self.grid) },
            'player_order': self.player_order,
            'current_turn_player': self.current_turn_player,
            'current_action_player': self.current_action_player,
            'current_action_type': self.current_action_type.value,
            'current_action_details': self.current_action_details,
            'stock_availability': toolz.keymap(lambda b: b.value, self.stock_availability),
            'money_by_player': self.money_by_player,
            'stock_by_player': toolz.valmap(lambda stock_map: toolz.keymap(lambda brand: brand.value, stock_map), self.stock_by_player),
            'user_data_by_id': self.user_data_by_id,
            'tiles_remaining': self.tiles_remaining,
            'active_brands': [brand.value for brand in self.active_brands],
            'inactive_brands': [brand.value for brand in self.inactive_brands],
            'acquisition_resolution_queue': [
                {
                    'player_id': details['player_id'], 
                    'acquirer': details['acquirer'].value,
                    'acquiree': details['acquiree'].value,
                    'acquiree_cost_at_acquisition_time': details['acquiree_cost_at_acquisition_time']
                }
                for details
                in self.acquisition_resolution_queue
            ]
        }


    @staticmethod
    def from_dict(state_data):
        new_state = GameState(state_data['title'])

        new_state.is_started = state_data['is_started']
        new_state.grid = GameState._build_grid_from_firestore_map(state_data['grid'])
        new_state.player_order = state_data['player_order']
        new_state.current_turn_player = state_data['current_turn_player']
        new_state.current_action_player = state_data['current_action_player']
        new_state.current_action_type = ActionType(state_data['current_action_type'])
        new_state.current_action_details = state_data['current_action_details']
        new_state.stock_availability = { Brand(brand): stock_count for brand, stock_count in state_data['stock_availability'].items() }
        new_state.money_by_player = state_data['money_by_player']
        new_state.stock_by_player = { player: { Brand(brand_value): amount for brand_value, amount in stock_map.items() } for player, stock_map in state_data['stock_by_player'].items() }
        new_state.user_data_by_id = state_data['user_data_by_id']
        new_state.tiles_remaining = state_data['tiles_remaining']
        new_state.active_brands = [Brand(brand_value) for brand_value in state_data['active_brands']]
        new_state.inactive_brands = [Brand(brand_value) for brand_value in state_data['inactive_brands']]
        new_state.acquisition_resolution_queue = [
            {
                'player_id': details['player_id'], 
                'acquirer': Brand(details['acquirer']),
                'acquiree': Brand(details['acquiree']),
                'acquiree_cost_at_acquisition_time': details['acquiree_cost_at_acquisition_time']
            }
            for details
            in state_data['acquisition_resolution_queue']
        ]

        return new_state


    @staticmethod
    def _build_grid_from_firestore_map(firestore_grid):
        board = GameState._generate_initial_grid()
        branded_chains_by_brand = {brand: Chain([], brand) for brand in Brand}

        for x_string, firestore_column in firestore_grid.items():
            x = int(x_string)
            for y, firestore_space in enumerate(firestore_column):
                if not firestore_space:
                    continue
                
                brand_letter = firestore_space['brand']
                brand = Brand(brand_letter) if brand_letter else None 
                
                if brand:
                    chain = branded_chains_by_brand[brand]
                    chain.tiles.append(Tile(x, y))
                    board[x][y] = chain
                    continue

                neighbors = grid.get_unique_neighbors(board, x, y)

                tile = Tile(x, y)

                if not neighbors:
                    board[x][y] = Chain([tile])
                    continue

                if len(neighbors) == 1:
                    (chain,) = neighbors
                    chain.tiles.append(tile)
                    board[x][y] = chain
                    continue
                
                merged_chain = Chain([tile for chain in neighbors for tile in chain.tiles] + [tile])
                board[x][y] = merged_chain

                for chain in neighbors:
                    for tile in chain.tiles:
                        board[tile.x][tile.y] = merged_chain

        return board


    @staticmethod
    def _generate_initial_grid():
        height = int(os.environ['HEIGHT'])
        width = int(os.environ['WIDTH'])
        return [[None for _ in range(height)] for x in range(width)]


class PlaceTileResult():
    def __init__(self, state, acquired_chains, acquirer, new_brand):
        self.state = state
        self.acquired_chains = acquired_chains
        self.acquirer = acquirer
        self.new_brand = new_brand


class RuleViolation(Exception):
    pass
