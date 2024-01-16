FROM python:3 AS basetelebot

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get upgrade -y  && \ 
	apt-get install -y \
	python3-pip && \
	python3 -m pip install --upgrade pip  && \
	pip3 install -r requirements.txt --upgrade && \
	apt-get remove --purge -y build-essential  && \
	apt-get autoclean -y && apt-get autoremove -y  && \
	rm -rf /default /etc/default /tmp/* /etc/cont-init.d/* /var/lib/apt/lists/* /var/tmp/*
FROM basetelebot

COPY /telegraph-downloader /app/

RUN chmod 777 /app/tgbot_main.py

VOLUME /download

CMD ["python3", "/app/tgbot_main.py"]