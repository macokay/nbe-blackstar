FROM python:3.13-alpine

# paho-mqtt 1.x: nbe.py uses the v1 callback API (on_connect with rc)
RUN pip install --no-cache-dir paho-mqtt==1.6.1 pycryptodome==3.23.0 \
    && adduser -D -u 10001 nbe

RUN mkdir -p /var/lib/nbe && chown nbe:nbe /var/lib/nbe

COPY --chown=nbe:nbe ./src /app
COPY ./docker/docker_init /docker_init
RUN chmod 755 /docker_init

WORKDIR /app
USER nbe

# unbuffered output so `docker logs` shows lines as they are written
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=60s --timeout=5s --start-period=120s --retries=3 \
    CMD test -n "$(find /tmp/nbe-alive -mmin -5 2>/dev/null)"

ENTRYPOINT ["/docker_init"]
