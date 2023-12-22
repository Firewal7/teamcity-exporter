FROM alpine:3.7

ENV TE_LISTEN_ADDRESS=0.0.0.0
ENV TE_LISTEN_PORT=9191
ENV TE_LOG_LEVEL=INFO

RUN apk --no-cache add \
    curl \
    python3 \
    python3-dev \
    py3-pip \
    bash

RUN pip3 install python-dotenv prometheus_client

ADD requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

COPY teamcity_exporter.py /teamcity_exporter.py

ENTRYPOINT ["python3", "/teamcity_exporter.py"]
