init:
	pipenv install -d

test: 
	pipenv run pytest

create-env-vars-file:
	cat .env | sed -E 's/=(.*)/: "\1"/' > .env.yaml

deploy-place-tile: create-env-vars-file
	gcloud functions deploy place_tile --runtime python37 --trigger-http --allow-unauthenticated --project acquire-538ab --env-vars-file .env.yaml

deploy-create-game: create-env-vars-file
	gcloud functions deploy create_game --runtime python37 --trigger-http --allow-unauthenticated --project acquire-538ab --env-vars-file .env.yaml

deploy-join-game: create-env-vars-file
	gcloud functions deploy join_game --runtime python37 --trigger-http --allow-unauthenticated --project acquire-538ab --env-vars-file .env.yaml

deploy-start-game: create-env-vars-file
	gcloud functions deploy start_game --runtime python37 --trigger-http --allow-unauthenticated --project acquire-538ab --env-vars-file .env.yaml

deploy: deploy-place-tile deploy-start-game deploy-create-game deploy-join-game
	echo 'Deployed!'
