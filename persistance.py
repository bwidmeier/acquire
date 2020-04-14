from google.cloud import firestore

import models


def get_game(game_id):
    client = firestore.Client()
    return client.collection('games').document(game_id).get().to_dict()


def update_game(game_id, **kwargs):
    client = firestore.Client()
    client.collection('games').document(game_id).update(kwargs)


def create_game_state(game_id, state):
    client = firestore.Client()
    client.collection('game_states').add(state.to_json(), document_id=game_id)


def get_game_state(game_id):
    client = firestore.Client()
    response = client.collection('game_states').document(game_id).get().to_dict()
    return models.GameState(response)


def update_game_state(game_id, new_state):
    client = firestore.Client()
    client.collection('game_states').document(game_id).update(new_state)
