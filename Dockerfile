FROM fedora AS builder

WORKDIR /app

COPY requirements.txt requirements.txt

RUN dnf install -y python3 python3-pip gcc libxml2-devel libxslt-devel \
    && pip install --upgrade pip \
    && pip install --prefix="/install" -r requirements.txt

COPY --from=builder /install /usr/local

COPY /src /app/

RUN chmod 777 /app/bot/launcher.py

VOLUME /download

CMD ["python", "/app/bot/launcher.py"]
