FROM python:3.12-alpine AS builder

WORKDIR /neko/bot
WORKDIR /neko/src

ENV PATH=$PATH:/neko
ENV PYTHONPATH /neko

COPY requirements.txt requirements.txt
COPY bot /neko/bot
COPY src /neko/src

RUN pip install --no-cache-dir -r requirements.txt

VOLUME ["/media", "/log"]

CMD ["python3", "/neko/bot/Main.py"]
