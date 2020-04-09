from contextlib import nullcontext
from functools import wraps
from pathlib import Path
from typing import Callable, TypeVar, Any

import pytest
from testcontainers.compose import DockerCompose
from testcontainers.core.utils import inside_container
from time import sleep

from micro_templating.auth import Authenticator
from micro_templating.db import db
from micro_templating.flask_app import create_app
from micro_templating.settings import PROJECT_NAME, PROJECT_VERSION

TEST_AUTH_HOST = f"http://{'auth:8080' if inside_container() else 'localhost:8788'}/auth/realms/micro-keycloak"
TEST_DB_URL = f"postgresql://test:test@{'database:5432' if inside_container() else 'localhost:5456'}/test"
TEST_OAUTH2_AUDIENCE = "content-provider"

FuncType = Callable[..., Any]
F = TypeVar('F', bound=FuncType)


class MockAuthenticator(Authenticator):
    def token_required(self, f: Callable) -> F:
        """
        Does nothing. Replaces token requirement

        Args:
            f: decorated function

        """

        @wraps(f)
        def decorated(*args, **kwargs):
            """
            Returns f, does nothing.
            Args:
                *args: decorated function's arguments
                **kwargs: decorated function's keyword arguments

            Returns:

            """
            return f(*args, **kwargs)

        return decorated


@pytest.fixture(scope='session')
def client():

    if inside_container():
        context_manager = nullcontext()
    else:
        docker_compose_path = f"{str(Path(__file__).resolve().parent)}/docker/"
        context_manager = DockerCompose(filepath=docker_compose_path, compose_file_name="docker-compose.test.yml")

    with context_manager:

        sleep(3)

        fake_authenticator = MockAuthenticator("", "")
        micro_templating_app = create_app(project_name=PROJECT_NAME, project_version=PROJECT_VERSION,
                                          db_url=TEST_DB_URL, jinja_env=None, authenticator=fake_authenticator,)
        micro_templating_app.config['TESTING'] = True

        with micro_templating_app.test_client() as client:
            with micro_templating_app.app_context():
                db.create_all()
            yield client


@pytest.fixture(scope='session')
def authenticator(client):
    yield client.application.config["AUTH"]
