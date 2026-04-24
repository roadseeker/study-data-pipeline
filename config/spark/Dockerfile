FROM apache/spark:3.5.8

USER root

RUN mkdir -p /home/spark/.ivy2 /home/spark/.cache/pip \
    && usermod -d /home/spark spark \
    && chown -R spark:spark /home/spark \
    && python3 -m pip install --no-cache-dir pyyaml

ENV HOME=/home/spark

USER spark
