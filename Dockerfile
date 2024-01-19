FROM python:3.5 AS builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && pip install --upgrade pip \
    && pip install --prefix="/install" -r requirements.txt

FROM python:3-alpine

WORKDIR /app

COPY --from=builder /install /usr/local

RUN apk add --no-cache libstdc++ \
    && apk add --no-cache --virtual .build-deps build-base \
    && pip install --no-cache-dir requests

COPY /telegraph-downloader /app/

RUN chmod 777 /app/tgbot_main.py

VOLUME /download

CMD ["python3", "/app/tgbot_main.py"]
