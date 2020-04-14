init:
	pipenv install -d

test: 
	pipenv run pytest

generate-requirements-txt:
	pipenv run pip freeze > requirements.txt

create-env-vars-file:
	cat .env | sed -E 's/=(.*)/: "\1"/' > .env.yaml

deploy-place-tile: create-env-vars-file generate-requirements-txt
	gcloud functions deploy place_tile --runtime python37 --trigger-http --allow-unauthenticated --project acquire-538ab --env-vars-file .env.yaml

deploy-start-game: create-env-vars-file generate-requirements-txt
	gcloud functions deploy start_game --runtime python37 --trigger-http --allow-unauthenticated --project acquire-538ab --env-vars-file .env.yaml

deploy: deploy-place-tile deploy-start-game
	echo 'Deployed!'
