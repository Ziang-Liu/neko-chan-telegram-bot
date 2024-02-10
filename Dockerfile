FROM python:3 AS builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libxml2-dev libxslt1-dev \
    && apt-get install -y python3-ebooklib \
    && pip install --upgrade pip \
    && pip install -r requirements.txt --upgrade \
    && apt-get remove --purge -y build-essential \
	&& apt-get autoclean -y && apt-get autoremove -y \
	&& rm -rf /default /etc/default /tmp/* /etc/cont-init.d/* /var/lib/apt/lists/* /var/tmp/*

FROM builder

COPY /telegraph-downloader /app/

RUN chmod 777 /app/tgbot_main.py

VOLUME /download

CMD ["python3", "/app/tgbot_main.py"]