FROM python:3.7-slim

ENV PORT 8080

RUN pip install pipenv
RUN pip install gunicorn

WORKDIR /app

COPY Pipfile* /app/
RUN pipenv install --system --deploy

COPY *.py /app/

CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 8 --timeout 0 app:app