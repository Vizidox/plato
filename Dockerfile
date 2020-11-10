FROM nexus.morphotech.co.uk/flask-deploy:1.2.1-python3.7

RUN apt-get update && apt-get install -y build-essential python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info


COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
COPY ./main.py /app/main.py
ENV FLASK_APP=/app/main.py
COPY plato /app/plato
COPY ./migrations /app/migrations
COPY ./prestart.sh /app/prestart.sh
COPY ./tests /app/tests

RUN poetry install -vvv



