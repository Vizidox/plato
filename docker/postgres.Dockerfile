ARG pg_ver
FROM postgres:12.2

ARG uid
RUN groupadd -r -g $uid vizidox && \
    useradd -r -u $uid -g $uid vizidox
USER vizidox