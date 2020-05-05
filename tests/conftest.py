from contextlib import nullcontext
from functools import wraps
from pathlib import Path
from time import sleep
from typing import Callable, TypeVar, Any, Dict

import pytest
from jinja2 import Environment as JinjaEnv, DictLoader
from jinja2 import FileSystemLoader, select_autoescape
from testcontainers.compose import DockerCompose
from testcontainers.core.utils import inside_container

from micro_templating.auth import Authenticator
from micro_templating.db import db
from micro_templating.flask_app import create_app

TEST_AUTH_HOST = f"http://{'auth:8080' if inside_container() else 'localhost:8788'}/auth/realms/micro-keycloak"
TEST_DB_URL = f"postgresql://test:test@{'database:5432' if inside_container() else 'localhost:5456'}/test"
TEST_OAUTH2_AUDIENCE = "content-provider"

FuncType = Callable[..., Any]
F = TypeVar('F', bound=FuncType)


class MockAuthenticator(Authenticator):

    authenticated_endpoints: Dict[str, F]

    def __init__(self):
        self.authenticated_endpoints = dict()

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

        self.authenticated_endpoints[f.__name__] = f
        return decorated


@pytest.fixture(scope='session')
def template_loader() -> DictLoader:
    yield DictLoader(dict())

@pytest.fixture(scope='session')
def client(template_loader):

    current_folder = str(Path(__file__).resolve().parent)

    if inside_container():
        context_manager = nullcontext()
    else:
        docker_compose_path = f"{current_folder}/docker/"
        context_manager = DockerCompose(filepath=docker_compose_path, compose_file_name="docker-compose.test.yml")

    with context_manager:

        sleep(3)

        template_environment = JinjaEnv(
            loader=template_loader,
            autoescape=select_autoescape(["html", "xml"]),
            auto_reload=True
        )

        authenticator = MockAuthenticator()
        micro_templating_app = create_app(db_url=TEST_DB_URL,
                                          jinja_env=template_environment,
                                          authenticator=authenticator,
                                          template_static_directory=f"{current_folder}/resources/static",
                                          swagger_ui_config={})
        micro_templating_app.config['TESTING'] = True

        with micro_templating_app.test_client() as client:
            with micro_templating_app.app_context():
                db.create_all()
            yield client


@pytest.fixture(scope='session')
def authenticator(client):
    yield client.application.config["AUTH"]


@pytest.fixture(scope='session')
def jinjaenv(client):
    yield client.application.config["JINJENV"]
