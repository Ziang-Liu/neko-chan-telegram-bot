FROM fedora AS builder

WORKDIR /src

COPY requirements.txt requirements.txt

RUN dnf install -y python3 python3-pip gcc libxml2-devel libxslt-devel \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

COPY /src /src/

RUN chmod 777 /src/launcher.py

VOLUME /download

CMD ["python3", "/src/launcher.py"]
