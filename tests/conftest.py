from contextlib import nullcontext

import pytest
import requests
from testcontainers.compose import DockerCompose
from testcontainers.core.utils import inside_container
from testcontainers.core.waiting_utils import wait_for

from micro_templating.flask_app import create_app
from settings import PROJECT_NAME, PROJECT_VERSION

TEST_AUTH_HOST = f"http://{'auth:8080' if inside_container() else 'localhost:8788'}/auth/realms/micro-keycloak"
TEST_DB_URL = f"postgresql://test:test@{'database:5432' if inside_container() else 'localhost:5456'}/test"
TEST_OAUTH2_AUDIENCE = "content-provider"


@pytest.fixture(scope='session')
def client():

    if inside_container():
        context_manager = nullcontext()
    else:
        context_manager = DockerCompose(filepath="./", compose_file_name="docker-compose.test.yml")

    with context_manager:

        wait_for(lambda: requests.get(f"{TEST_AUTH_HOST}/.well-known/openid-configuration").json())

        micro_templating_app = create_app(project_name=PROJECT_NAME, project_version=PROJECT_VERSION,
                                          auth_host_url=TEST_AUTH_HOST, db_url=TEST_DB_URL,
                                          oauth2_audience=TEST_OAUTH2_AUDIENCE, load_s3_templates=False)
        micro_templating_app.config['TESTING'] = True

        with micro_templating_app.test_client() as client:
            with micro_templating_app.app_context():
                pass
            yield client


@pytest.fixture(scope='session')
def authenticator(client):
    yield client.application.config["AUTH"]
