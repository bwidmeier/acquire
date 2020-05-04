from google.cloud import firestore

import models


# games
def create_game(title):
    client = firestore.Client()
    
    (_, doc) = client.collection('games').add({ 'title': title })

    return doc.id


# users
def get_user_data(user_id):
    client = firestore.Client()
    return client.document(f'users/{user_id}').get().to_dict()


# game_states
def create_game_state(game_id, state):
    client = firestore.Client()
    client.collection('game_states').add(state.to_dict(), document_id=game_id)


def get_game_state(game_id):
    client = firestore.Client()
    response = client.collection('game_states').document(game_id).get().to_dict()
    return models.GameState.from_dict(response)


def update_game_state(game_id, state):
    client = firestore.Client() 
    client.collection('game_states').document(game_id).update(state)


# game_state_secrets
def get_global_tiles(game_id):
    client = firestore.Client()
    raw_data = client.collection('game_state_secrets').document(game_id).get().to_dict()
    return [models.Tile(tile['x'], tile['y']) for tile in raw_data['tiles']]


def get_player_tiles(game_id, player_id):
    client = firestore.Client()
    raw_data = client.document(f'game_state_secrets/{game_id}/player_secrets/{player_id}').get().to_dict()
    return [models.Tile(tile['x'], tile['y']) for tile in raw_data['tiles']]


def initialize_global_tiles(game_id, tiles):
    client = firestore.Client()
    tile_dict_list = [tile.to_dict() for tile in tiles]
    client.collection('game_state_secrets').add({'tiles': tile_dict_list}, document_id=game_id)


def initialize_player_tiles(game_id, tiles_by_player_id):
    client = firestore.Client()
    batch = client.batch()

    player_secrets = client.collection(f'game_state_secrets/{game_id}/player_secrets')

    for player_id, tiles in tiles_by_player_id.items():
        tile_dict_list = [tile.to_dict() for tile in tiles]
        doc = player_secrets.document(player_id)
        batch.set(doc, {'tiles': tile_dict_list})

    batch.commit()


def deal_tile_to_player(game_id, player_id, tile):
    client = firestore.Client()
    batch = client.batch()
    tile_dict_list = [tile.to_dict()]
    
    game_secrets = client.document(f'game_state_secrets/{game_id}')
    player_secrets = client.document(f'game_state_secrets/{game_id}/player_secrets/{player_id}')

    batch.update(game_secrets, {'tiles': firestore.ArrayRemove(tile_dict_list)})
    batch.update(player_secrets, {'tiles': firestore.ArrayUnion(tile_dict_list)})

    batch.commit()


def delete_player_tile(game_id, player_id, tile):
    client = firestore.Client()
    tile_dict_list = [tile.to_dict()]

    player_secrets = client.document(f'game_state_secrets/{game_id}/player_secrets/{player_id}')
    player_secrets.update({'tiles': firestore.ArrayRemove(tile_dict_list)})
