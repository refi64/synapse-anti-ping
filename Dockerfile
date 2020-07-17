FROM matrixdotorg/synapse:v1.17.0-py3

RUN apk add git && \
  pip3 install --no-cache-dir -e 'git+https://github.com/matrix-org/mjolnir.git#egg=mjolnir&subdirectory=synapse_antispam' && \
  apk del git

COPY . /synapse_anti_ping/
RUN apk add build-base && pip3 install /synapse_anti_ping && apk del build-base
