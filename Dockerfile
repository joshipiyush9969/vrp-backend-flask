FROM python:3.10.7-slim-bullseye AS app

WORKDIR /app

ARG UID=1000
ARG GID=1000

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential curl libpq-dev \
  && rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man \
  && apt-get clean \
  && groupadd -g "${GID}" python \
  && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" python \
  && chown python:python -R /app

USER python

COPY --chown=python:python requirements*.txt ./
COPY --chown=python:python bin/ ./bin

RUN chmod 0755 bin/* && bin/pip3-install

ARG FLASK_DEBUG=false
# use `=` if you want to set multiple env at a time
ENV FLASK_DEBUG=$FLASK_DEBUG \
    FLASK_APP=vrp-flask.app \
    FLASK_SKIP_DOTENV=true \
    PYTHONUNBUFFERED=true \
    PYTHONPATH=. \
    PATH="/home/python/.local/bin:$PATH" \
    USER=python

RUN echo $PATH

COPY --chown=python:python . .

# https://github.com/nickjj/flask-static-digest (not necessary here)
# RUN if [ "${FLASK_DEBUG}" != "true" ]; then \
#   python -m flask digest compile; \
#   fi

ENTRYPOINT ["/app/bin/docker-entrypoint"]

EXPOSE 8000

# https://stackoverflow.com/a/1621487/17825257
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers=4", "--log-level=debug", "app:app"]