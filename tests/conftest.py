from contextlib import nullcontext
from pathlib import Path
from time import sleep
from typing import Callable, TypeVar, Any

import pytest
from jinja2 import Environment as JinjaEnv, DictLoader
from jinja2 import select_autoescape
from testcontainers.compose import DockerCompose
from testcontainers.core.utils import inside_container

from micro_templating.db import db
from micro_templating.flask_app import create_app

TEST_DB_URL = f"postgresql://test:test@{'database:5432' if inside_container() else 'localhost:5456'}/test"

FuncType = Callable[..., Any]
F = TypeVar('F', bound=FuncType)


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

        micro_templating_app = create_app(db_url=TEST_DB_URL,
                                          jinja_env=template_environment,
                                          template_static_directory=f"{current_folder}/resources/static",
                                          swagger_ui_config={})
        micro_templating_app.config['TESTING'] = True

        with micro_templating_app.test_client() as client:
            with micro_templating_app.app_context():
                db.create_all()
            yield client


@pytest.fixture(scope='session')
def jinjaenv(client):
    yield client.application.config["JINJENV"]
