FROM python:3.12-alpine AS builder

WORKDIR /neko/bot
WORKDIR /neko/src

ENV PATH=$PATH:/neko
ENV PYTHONPATH /neko

COPY requirements.txt requirements.txt
COPY bot /neko/bot
COPY src /neko/src

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del --purge .build-deps

VOLUME ["/media", "/log"]

CMD ["python3", "/neko/bot/Main.py"]
