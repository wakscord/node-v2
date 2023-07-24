FROM python:3.11-slim-buster

WORKDIR /code
ENV PYTHONPATH "${PYTHONPATH}:/code"

COPY ./.env /code/.env
COPY ./requirements.txt /code/requirements.txt
COPY ./app /code/app

RUN pip3 install --no-cache-dir --upgrade -r /code/requirements.txt
ENTRYPOINT python app/main.py