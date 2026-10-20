FROM python:3.14-alpine

# pinned runtime dependencies (paho-mqtt 2.x uses the VERSION2 callback API)
COPY requirements.txt /tmp/requirements.txt
# pip is removed after installing: the runtime does not need it, and it vendors libraries
# (urllib3, msgpack) that scanners flag
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && pip uninstall -y pip \
    && rm /tmp/requirements.txt \
    && adduser -D -u 10001 nbe \
    && mkdir -p /var/lib/nbe \
    && chown nbe:nbe /var/lib/nbe

COPY --chown=nbe:nbe ./src/nbe_blackstar /app/nbe_blackstar

WORKDIR /app
USER nbe

# unbuffered output so `docker logs` shows lines as they are written
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=60s --timeout=5s --start-period=120s --retries=3 \
    CMD test -n "$(find /tmp/nbe-alive -mmin -5 2>/dev/null)"

ENTRYPOINT ["python3", "-m", "nbe_blackstar"]
