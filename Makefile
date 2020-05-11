init:
	pipenv install -d

test: 
	pipenv run pytest

build:
	gcloud builds submit --tag gcr.io/acquire-538ab/acquire

deploy: build
	gcloud run deploy acquire --image gcr.io/acquire-538ab/acquire --platform managed --region us-east4 --allow-unauthenticated

run-server:
	pipenv run flask run
