ARG pg_ver
FROM postgres:$pg_ver

ARG uid
RUN groupadd -r -g $uid vizidox && \
    useradd -r -u $uid -g $uid vizidox
USER vizidox