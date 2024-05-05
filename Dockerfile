FROM fedora AS builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN dnf install -y python3 python3-pip gcc libxml2-devel libxslt-devel \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

COPY src/bot /app

RUN chmod -R 777 /app

VOLUME /download

CMD ["python3", "/app/bot.py"]
