import tempfile
from contextlib import nullcontext
from pathlib import Path
from time import sleep
from typing import Callable, TypeVar, Any

import pytest
from jinja2 import Environment as JinjaEnv, DictLoader
from jinja2 import select_autoescape
from testcontainers.compose import DockerCompose
from testcontainers.core.utils import inside_container

from plato.db import db
from plato.file_storage import S3FileStorage, PlatoFileStorage, DiskFileStorage
from plato.flask_app import create_app
from tests.test_s3_application_set_up import BUCKET_NAME

TEST_DB_URL = f"postgresql://test:test@{'database:5432' if inside_container() else 'localhost:5456'}/test"

FuncType = Callable[..., Any]
F = TypeVar('F', bound=FuncType)


@pytest.fixture(scope='session')
def template_loader() -> DictLoader:
    yield DictLoader({})


@pytest.fixture(scope='class')
def client_local_storage():
    with tempfile.TemporaryDirectory() as file_dir:
        yield from flask_client(template_loader, file_storage=DiskFileStorage(file_dir))


@pytest.fixture(scope='class')
def client_s3_storage():
    with tempfile.TemporaryDirectory() as file_dir:
        yield from flask_client(template_loader, file_storage=S3FileStorage(file_dir, BUCKET_NAME))


def flask_client(template_loader, file_storage: PlatoFileStorage):

    current_folder = str(Path(__file__).resolve().parent)

    if inside_container():
        context_manager = nullcontext()
    else:
        docker_compose_path = f"{current_folder}/docker/"
        context_manager = DockerCompose(filepath=docker_compose_path, compose_file_name="docker-compose.local.test.yml")

    with context_manager:

        sleep(5)

        template_environment = JinjaEnv(
            loader=template_loader,
            autoescape=select_autoescape(["html", "xml"]),
            auto_reload=True
        )

        plato_app = create_app(db_url=TEST_DB_URL,
                               jinja_env=template_environment,
                               template_static_directory=f"{current_folder}/resources/static",
                               swagger_ui_config={},
                               storage=file_storage)
        plato_app.config['TESTING'] = True

        with plato_app.test_client() as client:
            with plato_app.app_context():
                db.create_all()
            yield client


@pytest.fixture(scope='session')
def jinjaenv(client_local_storage):
    yield client_local_storage.application.config["JINJAENV"]
