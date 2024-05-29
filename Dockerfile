FROM fedora AS builder

WORKDIR /neko/bot
WORKDIR /neko/src

ENV PATH=$PATH:/neko
ENV PYTHONPATH /neko

COPY requirements.txt requirements.txt
COPY bot /neko/bot
COPY src /neko/src

RUN dnf install -y python3 python3-pip gcc libxml2-devel \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && chmod -R 777 /neko

VOLUME ["/media", "/log"]

CMD ["python3", "/neko/bot/Main.py"]
