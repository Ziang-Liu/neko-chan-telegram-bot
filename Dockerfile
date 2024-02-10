FROM python:3 AS builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libxml2-dev libxslt1-dev \
    && pip install --upgrade pip \
    && pip install --prefix="/install" lxml==4.1.0 -r requirements.txt

FROM python:3-alpine

WORKDIR /app

COPY --from=builder /install /usr/local

COPY /telegraph-downloader /app/

RUN chmod 777 /app/tgbot_main.py

VOLUME /download

CMD ["python3", "/app/tgbot_main.py"]