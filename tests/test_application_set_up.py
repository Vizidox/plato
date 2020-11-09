# -*- coding: utf-8 -*-
import boto3
import pytest
import pathlib
from moto import mock_s3
from smart_open import s3
from plato.setup_util import load_templates, NoIndexTemplateFound
from tempfile import TemporaryDirectory
from plato.db.models import Template, db

TEMPLATE_FILE_PATH_FORMAT = "templating/templates/{0}/{1}"
STATIC_FILE_PATH_FORMAT = "templating/static/{0}/{1}"

LOCAL_TEMPLATE_FILE_PATH_FORMAT = "templates/{0}/{1}"
LOCAL_STATIC_FILE_PATH_FORMAT = "static/{0}/{1}"


def get_template_file_path(template_id: str):
    return TEMPLATE_FILE_PATH_FORMAT.format(template_id, template_id)


def get_local_template_file_path(template_id: str):
    return LOCAL_TEMPLATE_FILE_PATH_FORMAT.format(template_id, template_id)


def get_static_file_path(template_id: str, file_name: str):
    return STATIC_FILE_PATH_FORMAT.format(template_id, file_name)


def get_local_static_file_path(template_id: str, file_name: str):
    return LOCAL_STATIC_FILE_PATH_FORMAT.format(template_id, file_name)


def create_child_temp_folder(main_directory: str) -> str:
    template_dir_name = main_directory + "/abc"
    pathlib.Path(template_dir_name).mkdir(parents=True, exist_ok=True)
    return template_dir_name


def write_to_s3(bucket_name: str, file_paths: list):
    encoding = "utf-8"
    for file_path in file_paths:
        with s3.open(bucket_name, key_id=file_path, mode="wb") as file:
            file.write(f"I am file !".encode(encoding))


@pytest.fixture(scope="class")
def populate_db(client):
    with client.application.test_request_context():
        template = Template(id_="0", schema={},
                            type_="text/html", tags=['test_tags'], metadata={},
                            example_composition={'place_holder': 'value'})
        db.session.add(template)
        db.session.commit()

    yield

    with client.application.test_request_context():
        Template.query.delete()
        db.session.commit()


@pytest.fixture(scope='function')
@mock_s3
def populate_s3() -> str:
    bucket_name = 'test_template_bucket_1'
    conn = boto3.resource('s3', region_name='eu-central-1')
    conn.create_bucket(Bucket=bucket_name)

    static_file_1 = get_static_file_path(file_name="abc_1", template_id="0")
    static_file_2 = get_static_file_path(file_name="abc_2", template_id="0")
    write_to_s3(bucket_name=bucket_name, file_paths=[static_file_1, static_file_2])

    template_file_1 = get_template_file_path(template_id="0")
    write_to_s3(bucket_name=bucket_name, file_paths=[template_file_1])

    return bucket_name


@pytest.fixture(scope='function')
@mock_s3
def populate_s3_with_missing_template_file() -> str:
    bucket_name = 'test_template_bucket_3'
    conn = boto3.resource('s3', region_name='eu-central-1')
    conn.create_bucket(Bucket=bucket_name)

    static_file = get_static_file_path(file_name="abc", template_id="0")
    write_to_s3(bucket_name=bucket_name, file_paths=[static_file])

    return bucket_name


@pytest.mark.usefixtures("populate_db")
@mock_s3
class TestApplicationSetup:
    def test_success_case(self, client, populate_s3):
        bucket_name = populate_s3
        with client.application.test_request_context():
            with TemporaryDirectory() as temp:
                # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
                base_dir = 'templating'
                template_dir_name = create_child_temp_folder(temp)
                load_templates(bucket_name, template_dir_name, base_dir)

                static_file_1 = template_dir_name + '/' + get_local_static_file_path(file_name="abc_1", template_id="0")
                static_file_2 = template_dir_name + '/' + get_local_static_file_path(file_name="abc_2", template_id="0")
                template_file_1 = template_dir_name + '/' + get_local_template_file_path(template_id="0")

                assert pathlib.Path(static_file_1).is_file() == True
                assert pathlib.Path(static_file_2).is_file() == True
                assert pathlib.Path(template_file_1).is_file() == True

    def test_missing_template_file(self, client, populate_s3_with_missing_template_file):
        bucket_name = populate_s3_with_missing_template_file
        with client.application.test_request_context():
            with pytest.raises(NoIndexTemplateFound):
                with TemporaryDirectory() as temp:
                    # as we cannot directly delete any folder created by TemporaryDirectory, we create another temporary one inside it
                    base_dir = 'templating'
                    template_dir_name = create_child_temp_folder(temp)
                    load_templates(bucket_name, template_dir_name, base_dir)
