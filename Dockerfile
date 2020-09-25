FROM matrixdotorg/synapse:v1.20.1

COPY . /synapse_anti_ping/
RUN apt-get update && apt-get install -y build-essential git && \
  pip3 install --no-cache-dir -e 'git+https://github.com/matrix-org/mjolnir.git#egg=mjolnir&subdirectory=synapse_antispam' && \
  pip3 install /synapse_anti_ping && \
  apt-get remove -y --autoremove build-essential git && rm -rf /var/lib/apt/lists
