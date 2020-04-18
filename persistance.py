from google.cloud import firestore

import models


# games
def create_game(title):
    client = firestore.Client()
    
    (_, doc) = client.collection('games').add({
        'title': title,
        'is_started': False})

    return doc.id


# game_states
def create_game_state(game_id, state):
    client = firestore.Client()
    client.collection('game_states').add(state.to_dict(), document_id=game_id)


def get_game_state(game_id):
    client = firestore.Client()
    response = client.collection('game_states').document(game_id).get().to_dict()
    return models.GameState(response)


def update_game_state(game_id, new_state):
    client = firestore.Client()
    client.collection('game_states').document(game_id).update(new_state)
