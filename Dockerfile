FROM python:3.11-slim-buster

WORKDIR /code
ENV PYTHONPATH "${PYTHONPATH}:/code"

COPY ./requirements.txt /code/requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./.env /code/.env
COPY ./app /code/app

ENTRYPOINT python app/main.py